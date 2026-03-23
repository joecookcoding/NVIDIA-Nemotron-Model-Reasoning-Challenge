from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": dedent(text).strip("\n").splitlines(keepends=True),
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(text).strip("\n").splitlines(keepends=True),
    }


NOTEBOOK_PATH = Path("notebooks/nvidia-nemotron-first-submit.ipynb")


cells = [
    md(
        """
        # Nemotron First Submit

        Single Kaggle notebook for the NVIDIA Nemotron Model Reasoning Challenge.

        This notebook assumes:

        - the competition `train.csv` is attached,
        - the Nemotron model is attached,
        - the offline package dataset is either attached under `/kaggle/input` or downloaded with `kagglehub.dataset_download("dennisfong/nvidia-nemotron-offline-packages")`,
        - if the offline package dataset does not include `mamba_ssm`, attach a local `mamba_ssm` source tarball or source directory as an extra dataset input,
        - and the goal is to produce `submission.zip` for the first scored Kaggle submission.
        """
    ),
    code(
        r"""
        import gc
        import hashlib
        import importlib.util
        import json
        import math
        import os
        import platform
        import random
        import re
        import shutil
        import socket
        import stat
        import subprocess
        import sys
        import tarfile
        import time
        import traceback
        import zipfile
        from datetime import datetime, timezone
        from pathlib import Path

        import pandas as pd
        import torch

        INPUT_ROOT = Path("/kaggle/input")
        WORK_ROOT = Path("/kaggle/working")
        NOTEBOOK_NAME = "nvidia-nemotron-first-submit"
        RUN_ID = os.environ.get("NEMOTRON_LORA_RUN_ID") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        RUN_ROOT = WORK_ROOT / "artifacts" / "lora_runs" / RUN_ID
        RUN_ROOT.mkdir(parents=True, exist_ok=True)

        def write_json(path: Path, payload) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")

        def dedupe_paths(paths: list[Path]) -> list[Path]:
            unique: list[Path] = []
            seen: set[str] = set()
            for path in paths:
                try:
                    key = str(path.resolve())
                except Exception:
                    key = str(path)
                if key in seen:
                    continue
                seen.add(key)
                unique.append(path)
            return unique

        def discover_wheelhouse_dirs(root: Path) -> list[Path]:
            wheel_counts: dict[Path, int] = {}
            for wheel_path in root.rglob("*.whl"):
                wheel_counts[wheel_path.parent] = wheel_counts.get(wheel_path.parent, 0) + 1
            return sorted(wheel_counts, key=lambda path: (-wheel_counts[path], str(path)))

        def wheelhouse_has_package(wheelhouse: Path | None, package_prefixes: tuple[str, ...]) -> bool:
            if wheelhouse is None:
                return False
            normalized_prefixes = tuple(prefix.lower().replace("-", "_") for prefix in package_prefixes)
            seen_prefixes: set[str] = set()
            for wheel_path in wheelhouse.glob("*.whl"):
                stem = wheel_path.name.lower().replace("-", "_")
                for prefix in normalized_prefixes:
                    if stem.startswith(prefix):
                        seen_prefixes.add(prefix)
            return all(prefix in seen_prefixes for prefix in normalized_prefixes)

        def select_package_wheels(wheelhouse: Path, package_names: tuple[str, ...]) -> tuple[dict[str, list[Path]], list[str]]:
            py_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
            selected: dict[str, list[Path]] = {}
            missing: list[str] = []

            for package_name in package_names:
                normalized = package_name.lower().replace("-", "_")
                matches = sorted(
                    path for path in wheelhouse.glob("*.whl")
                    if path.name.lower().replace("-", "_").startswith(normalized)
                )
                preferred = [
                    path for path in matches
                    if py_tag in path.name or "py3-none-any" in path.name or "none-any" in path.name
                ]
                chosen = preferred or matches
                if chosen:
                    selected[package_name] = chosen
                else:
                    missing.append(package_name)

            return selected, missing

        def find_model_candidates(root: Path) -> list[Path]:
            candidates: list[Path] = []
            for config_path in root.rglob("config.json"):
                parent = config_path.parent
                if (parent / "tokenizer_config.json").exists():
                    candidates.append(parent)
            return sorted(
                set(candidates),
                key=lambda path: ("nemotron" not in str(path).lower(), len(path.parts), str(path)),
            )

        def find_competition_file(filename: str) -> Path | None:
            candidates = sorted(
                path for path in INPUT_ROOT.rglob(filename)
                if "competition" in str(path).lower()
            )
            return candidates[0] if candidates else None

        def stable_int(text: str) -> int:
            return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)

        def normalize_name(text: str) -> str:
            return re.sub(r"[^a-z0-9]+", "_", text.lower())

        WHEELHOUSE_SCAN_ROOTS = dedupe_paths(
            [
                path
                for path in [
                    INPUT_ROOT,
                    Path("/root/.cache/kagglehub/datasets"),
                    Path.home() / ".cache" / "kagglehub" / "datasets",
                    WORK_ROOT / "offline_packages",
                    WORK_ROOT / "wheelhouse",
                ]
                if path.exists()
            ]
        )
        SOURCE_SCAN_ROOTS = dedupe_paths(
            [
                path
                for path in [
                    INPUT_ROOT,
                    Path("/kaggle/usr/lib/notebooks"),
                    Path("/root/.cache/kagglehub/datasets"),
                    Path.home() / ".cache" / "kagglehub" / "datasets",
                    WORK_ROOT,
                ]
                if path.exists()
            ]
        )
        WHEELHOUSE_DIRS: list[Path] = []
        for wheelhouse_root in WHEELHOUSE_SCAN_ROOTS:
            WHEELHOUSE_DIRS.extend(discover_wheelhouse_dirs(wheelhouse_root))
        WHEELHOUSE_DIRS = dedupe_paths(WHEELHOUSE_DIRS)

        def find_offline_package_root() -> Path | None:
            direct_candidates = [
                INPUT_ROOT / "datasets" / "dennisfong" / "nvidia-nemotron-offline-packages" / "offline_packages",
                INPUT_ROOT / "nvidia-nemotron-offline-packages" / "offline_packages",
                Path("/root/.cache/kagglehub/datasets/dennisfong/nvidia-nemotron-offline-packages/offline_packages"),
                Path.home() / ".cache" / "kagglehub" / "datasets" / "dennisfong" / "nvidia-nemotron-offline-packages" / "offline_packages",
            ]
            for candidate in direct_candidates:
                if candidate.exists() and any(candidate.glob("*.whl")):
                    return candidate

            for root in WHEELHOUSE_SCAN_ROOTS:
                for candidate in sorted(path for path in root.rglob("offline_packages") if path.is_dir()):
                    if any(candidate.glob("*.whl")):
                        return candidate

            return next(
                (
                    path for path in WHEELHOUSE_DIRS
                    if wheelhouse_has_package(path, ("datasets", "trl", "peft", "accelerate"))
                ),
                None,
            )

        OFFLINE_PACKAGE_ROOT = find_offline_package_root()

        MODEL_CANDIDATES = find_model_candidates(INPUT_ROOT)
        MODEL_DIR = MODEL_CANDIDATES[0] if MODEL_CANDIDATES else None
        TRAIN_DATA_PATH = find_competition_file("train.csv")
        TEST_DATA_PATH = find_competition_file("test.csv")

        REQUIRED_MODULES = [
            "datasets",
            "trl",
            "peft",
            "accelerate",
        ]

        def collect_required_status() -> dict[str, bool]:
            return {
                name: importlib.util.find_spec(name) is not None
                for name in REQUIRED_MODULES
            }

        REQUIRED_STATUS = collect_required_status()
        MISSING_MODULES = [name for name, present in REQUIRED_STATUS.items() if not present]
        MODEL_RUNTIME_INSTALL_LOG: list[dict[str, object]] = []

        def collect_model_runtime_status() -> dict[str, bool]:
            return {
                "mamba_ssm": importlib.util.find_spec("mamba_ssm") is not None,
                "causal_conv1d": importlib.util.find_spec("causal_conv1d") is not None,
            }

        def extract_archives_for_fragments(package_fragments: tuple[str, ...]) -> list[Path]:
            extracted_dirs: list[Path] = []
            archive_patterns = ("*.tar.gz", "*.tgz")
            extraction_root = WORK_ROOT / "_source_cache"
            extraction_root.mkdir(parents=True, exist_ok=True)

            for root in SOURCE_SCAN_ROOTS:
                for pattern in archive_patterns:
                    for archive_path in root.rglob(pattern):
                        if not any(fragment in normalize_name(archive_path.name) for fragment in package_fragments):
                            continue
                        destination = extraction_root / normalize_name(archive_path.name)
                        marker = destination / ".extracted"
                        if not marker.exists():
                            destination.mkdir(parents=True, exist_ok=True)
                            with tarfile.open(archive_path, "r:*") as archive:
                                archive.extractall(destination)
                            marker.write_text(str(archive_path), encoding="utf-8")
                        extracted_dirs.append(destination)

            return extracted_dirs

        def find_local_source_candidates(package_fragments: tuple[str, ...]) -> list[Path]:
            candidates: list[Path] = []

            for root in SOURCE_SCAN_ROOTS:
                for setup_path in root.rglob("setup.py"):
                    if any(fragment in normalize_name(str(setup_path.parent)) for fragment in package_fragments):
                        candidates.append(setup_path.parent)

            for extracted_root in extract_archives_for_fragments(package_fragments):
                for setup_path in extracted_root.rglob("setup.py"):
                    if any(fragment in normalize_name(str(setup_path.parent)) for fragment in package_fragments):
                        candidates.append(setup_path.parent)

            return dedupe_paths(candidates)

        def install_packages_from_wheelhouse(package_names: tuple[str, ...], required_names: tuple[str, ...] | None = None) -> dict[str, object]:
            required_names = required_names or package_names
            if OFFLINE_PACKAGE_ROOT is None or not OFFLINE_PACKAGE_ROOT.exists():
                return {
                    "mode": "wheelhouse",
                    "installed": False,
                    "reason": "offline_package_root_missing",
                    "requested_packages": list(package_names),
                }

            supplemental = []
            for extra_name in ("ninja", "packaging", "setuptools"):
                if extra_name not in package_names:
                    supplemental.append(extra_name)

            resolved_packages = tuple(package_names) + tuple(supplemental)
            wheel_map, missing_wheels = select_package_wheels(OFFLINE_PACKAGE_ROOT, resolved_packages)
            required_missing = [name for name in required_names if name in missing_wheels]
            if required_missing:
                return {
                    "mode": "wheelhouse",
                    "installed": False,
                    "reason": "missing_wheels",
                    "requested_packages": list(package_names),
                    "required_missing": required_missing,
                    "available_wheels_preview": sorted(path.name for path in OFFLINE_PACKAGE_ROOT.glob("*.whl"))[:100],
                }

            install_command = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--no-index",
                "--ignore-installed",
            ]
            for package_name in resolved_packages:
                install_command.extend(str(path) for path in wheel_map.get(package_name, []))

            subprocess.check_call(install_command)
            importlib.invalidate_caches()
            return {
                "mode": "wheelhouse",
                "installed": True,
                "requested_packages": list(package_names),
                "resolved_wheels": {
                    name: [path.name for path in paths]
                    for name, paths in wheel_map.items()
                },
            }

        def install_package_from_source(package_name: str, package_fragments: tuple[str, ...]) -> dict[str, object]:
            candidates = find_local_source_candidates(package_fragments)
            if not candidates:
                return {
                    "mode": "source",
                    "installed": False,
                    "package_name": package_name,
                    "reason": "no_local_source_candidates",
                    "scan_roots": [str(path) for path in SOURCE_SCAN_ROOTS[:20]],
                }

            failures: list[dict[str, str]] = []
            for candidate in candidates:
                try:
                    subprocess.check_call(
                        [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "--quiet",
                            "--ignore-installed",
                            "--no-build-isolation",
                            str(candidate),
                        ]
                    )
                    importlib.invalidate_caches()
                    if importlib.util.find_spec(package_name) is not None:
                        return {
                            "mode": "source",
                            "installed": True,
                            "package_name": package_name,
                            "source_path": str(candidate),
                        }
                except Exception as exc:
                    failures.append(
                        {
                            "source_path": str(candidate),
                            "error_type": type(exc).__name__,
                            "error_message": str(exc),
                        }
                    )

            return {
                "mode": "source",
                "installed": False,
                "package_name": package_name,
                "reason": "all_source_candidates_failed",
                "failures": failures,
            }

        OFFLINE_INSTALL_ATTEMPTED = False
        if MISSING_MODULES:
            assert OFFLINE_PACKAGE_ROOT is not None and OFFLINE_PACKAGE_ROOT.exists(), (
                "Could not find the offline package wheelhouse. Attach the dataset under /kaggle/input "
                "or run kagglehub.dataset_download('dennisfong/nvidia-nemotron-offline-packages') first."
            )
            available_wheels = sorted(path.name for path in OFFLINE_PACKAGE_ROOT.glob("*.whl"))
            install_command = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--no-index",
                "--find-links",
                str(OFFLINE_PACKAGE_ROOT),
                "--ignore-installed",
                "datasets",
                "trl",
                "peft",
                "accelerate",
                "ninja",
                "packaging",
                "setuptools",
            ]
            print("Installing offline packages from:", OFFLINE_PACKAGE_ROOT)
            print("Missing modules before install:", MISSING_MODULES)
            print("Wheel preview:", available_wheels[:40])
            OFFLINE_INSTALL_ATTEMPTED = True
            subprocess.check_call(install_command)
            importlib.invalidate_caches()
            REQUIRED_STATUS = collect_required_status()
            MISSING_MODULES = [name for name, present in REQUIRED_STATUS.items() if not present]

        MODEL_RUNTIME_STATUS = collect_model_runtime_status()

        if not MODEL_RUNTIME_STATUS["causal_conv1d"]:
            causal_wheel_attempt = install_packages_from_wheelhouse(("causal_conv1d",), required_names=())
            MODEL_RUNTIME_INSTALL_LOG.append(causal_wheel_attempt)
            MODEL_RUNTIME_STATUS = collect_model_runtime_status()
            if not MODEL_RUNTIME_STATUS["causal_conv1d"]:
                causal_source_attempt = install_package_from_source("causal_conv1d", ("causal_conv1d", "causal_conv1d_cuda", "causal_conv1d_"))
                MODEL_RUNTIME_INSTALL_LOG.append(causal_source_attempt)
                MODEL_RUNTIME_STATUS = collect_model_runtime_status()

        if not MODEL_RUNTIME_STATUS["mamba_ssm"]:
            mamba_wheel_attempt = install_packages_from_wheelhouse(("mamba_ssm",), required_names=("mamba_ssm",))
            MODEL_RUNTIME_INSTALL_LOG.append(mamba_wheel_attempt)
            MODEL_RUNTIME_STATUS = collect_model_runtime_status()
            if not MODEL_RUNTIME_STATUS["mamba_ssm"]:
                mamba_source_attempt = install_package_from_source("mamba_ssm", ("mamba_ssm", "mamba_ssm_"))
                MODEL_RUNTIME_INSTALL_LOG.append(mamba_source_attempt)
                MODEL_RUNTIME_STATUS = collect_model_runtime_status()

        print("Run ID:", RUN_ID)
        print("Artifact root:", RUN_ROOT)
        print("Torch version:", torch.__version__)
        print("Torch CUDA build:", torch.version.cuda)
        print("CUDA available:", torch.cuda.is_available())
        if torch.cuda.is_available():
            print("GPU:", torch.cuda.get_device_name(0))
            print("GPU capability:", torch.cuda.get_device_capability(0))
            print("GPU VRAM GB:", round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2))

        print("Wheelhouse scan roots:")
        for path in WHEELHOUSE_SCAN_ROOTS[:10]:
            print("-", path)
        print("Wheelhouse directories detected:")
        for path in WHEELHOUSE_DIRS[:10]:
            print("-", path)

        print("Model candidates:")
        for index, path in enumerate(MODEL_CANDIDATES[:10]):
            print(index, path)

        print("TRAIN_DATA_PATH:", TRAIN_DATA_PATH)
        print("TEST_DATA_PATH:", TEST_DATA_PATH)
        print("Required package status:", REQUIRED_STATUS)
        print("Model runtime status:", MODEL_RUNTIME_STATUS)
        print("Model runtime install log:")
        for attempt in MODEL_RUNTIME_INSTALL_LOG:
            print(json.dumps(attempt, indent=2, default=str))

        setup_summary = {
            "run_id": RUN_ID,
            "artifact_root": str(RUN_ROOT),
            "torch_version": torch.__version__,
            "torch_cuda_build": torch.version.cuda,
            "cuda_available": bool(torch.cuda.is_available()),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "gpu_capability": torch.cuda.get_device_capability(0) if torch.cuda.is_available() else None,
            "offline_package_root": str(OFFLINE_PACKAGE_ROOT),
            "wheelhouse_scan_roots": [str(path) for path in WHEELHOUSE_SCAN_ROOTS[:10]],
            "wheelhouse_dirs": [str(path) for path in WHEELHOUSE_DIRS[:10]],
            "model_candidates": [str(path) for path in MODEL_CANDIDATES[:10]],
            "train_data_path": str(TRAIN_DATA_PATH) if TRAIN_DATA_PATH is not None else None,
            "test_data_path": str(TEST_DATA_PATH) if TEST_DATA_PATH is not None else None,
            "required_packages": REQUIRED_STATUS,
            "model_runtime_status": MODEL_RUNTIME_STATUS,
            "model_runtime_install_log": MODEL_RUNTIME_INSTALL_LOG,
            "offline_install_attempted": OFFLINE_INSTALL_ATTEMPTED,
            "offline_package_root": str(OFFLINE_PACKAGE_ROOT),
            "source_scan_roots": [str(path) for path in SOURCE_SCAN_ROOTS[:20]],
            "python_version": platform.python_version(),
            "hostname": socket.gethostname(),
        }
        write_json(RUN_ROOT / "setup_summary.json", setup_summary)

        assert torch.cuda.is_available(), "Turn on a GPU before running the training notebook."
        assert MODEL_DIR is not None, "Attach the Nemotron model to the notebook input."
        assert TRAIN_DATA_PATH is not None, "Attach the competition train.csv input to the notebook."

        if MISSING_MODULES:
            raise RuntimeError(
                "Missing required Python packages after offline install: "
                + ", ".join(MISSING_MODULES)
                + ". The offline package dataset was attached, but the required modules still were not importable after local installation."
            )
        if not MODEL_RUNTIME_STATUS["mamba_ssm"]:
            raise RuntimeError(
                "mamba_ssm is still missing before model load. Attach an offline wheelhouse that contains "
                "a compatible mamba_ssm wheel, or attach a local mamba_ssm source tarball/source directory "
                "under /kaggle/input so this notebook can build it offline."
            )
        """
    ),
    md(
        """
        ## Runtime Fixes And Training Config

        This cell applies the Blackwell/Triton workarounds from the competition notebook,
        then defines the lightweight LoRA configuration for the first scored submission.
        """
    ),
    code(
        r"""
        import triton.backends.nvidia as nv_backend
        import triton.backends.nvidia.compiler as nv_compiler
        from datasets import Dataset
        from peft import LoraConfig, TaskType, get_peft_model
        from trl import SFTConfig, SFTTrainer
        from transformers import AutoModelForCausalLM, AutoTokenizer

        def patch_loaded_nemotron_modules(force_slow_path: bool = False) -> dict:
            patched = {
                "rmsnorm_modules": [],
                "slow_path_modules": [],
            }

            def pure_rmsnorm_fn(x, weight, bias=None, z=None, eps=1e-5, group_size=None, norm_before_gate=True, upcast=True):
                dtype = x.dtype
                if upcast:
                    x = x.float()
                variance = x.pow(2).mean(-1, keepdim=True)
                x_normed = x * torch.rsqrt(variance + eps)
                out = x_normed * weight.float()
                if bias is not None:
                    out = out + bias.float()
                if z is not None:
                    out = out * torch.nn.functional.silu(z.float())
                return out.to(dtype)

            for name, module in list(sys.modules.items()):
                if hasattr(module, "rmsnorm_fn"):
                    module.rmsnorm_fn = pure_rmsnorm_fn
                    patched["rmsnorm_modules"].append(name)
                if force_slow_path and "modeling_nemotron_h" in name and hasattr(module, "is_fast_path_available"):
                    module.is_fast_path_available = False
                    patched["slow_path_modules"].append(name)

            return patched

        def configure_blackwell_triton() -> dict:
            src_candidates = [
                Path("/kaggle/usr/lib/notebooks/ryanholbrook/nvidia-utility-script/triton/backends/nvidia/bin/ptxas-blackwell"),
                Path("/opt/conda/lib/python3.12/site-packages/triton/backends/nvidia/bin/ptxas-blackwell"),
            ]
            dst = Path("/tmp/ptxas-blackwell")
            dst_bin = Path("/tmp/triton_nvidia_bin")
            copied_from = None

            for src in src_candidates:
                if src.exists():
                    shutil.copy2(src, dst)
                    os.chmod(dst, os.stat(dst).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                    src_bin = Path(nv_backend.__file__).resolve().parent / "bin"
                    shutil.copytree(src_bin, dst_bin, dirs_exist_ok=True)
                    for path in dst_bin.iterdir():
                        if path.is_file():
                            os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                    os.environ["TRITON_PTXAS_PATH"] = str(dst)
                    os.environ["TRITON_PTXAS_BLACKWELL_PATH"] = str(dst)
                    copied_from = str(src)
                    break

            nv_compiler.get_ptxas_version = lambda arch: "12.0"
            return {
                "copied_from": copied_from,
                "ptxas_path": str(dst) if copied_from else None,
                "triton_bin_path": str(dst_bin) if copied_from else None,
            }

        runtime_patch_summary = {
            "preload_patch": patch_loaded_nemotron_modules(force_slow_path=False),
            "blackwell_triton": configure_blackwell_triton(),
        }
        write_json(RUN_ROOT / "runtime_patch_summary.json", runtime_patch_summary)
        print(json.dumps(runtime_patch_summary, indent=2))

        TRAIN_SAMPLE_LIMIT = 600
        VAL_FRACTION = 0.10
        VAL_SAMPLE_LIMIT = 60
        RANDOM_SEED = 42

        LORA_RANK = 32
        LORA_ALPHA = 16
        LORA_DROPOUT = 0.05
        TARGET_MODULES = "all-linear"

        MAX_SEQ_LEN = 1024
        NUM_EPOCHS = 1
        PER_DEVICE_BATCH_SIZE = 1
        GRAD_ACCUM = 4
        LEARNING_RATE = 2e-4
        WEIGHT_DECAY = 0.01
        MAX_GRAD_NORM = 1.0

        EVAL_MAX_NEW_TOKENS = 96
        OUTPUT_DIR = RUN_ROOT / "adapter"
        VALIDATION_PREDICTIONS_PATH = RUN_ROOT / "validation_predictions.csv"
        TRAINING_CONFIG = {
            "train_sample_limit": TRAIN_SAMPLE_LIMIT,
            "val_fraction": VAL_FRACTION,
            "val_sample_limit": VAL_SAMPLE_LIMIT,
            "random_seed": RANDOM_SEED,
            "lora_rank": LORA_RANK,
            "lora_alpha": LORA_ALPHA,
            "lora_dropout": LORA_DROPOUT,
            "target_modules": TARGET_MODULES,
            "max_seq_len": MAX_SEQ_LEN,
            "num_epochs": NUM_EPOCHS,
            "per_device_batch_size": PER_DEVICE_BATCH_SIZE,
            "grad_accum": GRAD_ACCUM,
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "max_grad_norm": MAX_GRAD_NORM,
            "eval_max_new_tokens": EVAL_MAX_NEW_TOKENS,
            "output_dir": str(OUTPUT_DIR),
        }
        write_json(RUN_ROOT / "training_config.json", TRAINING_CONFIG)
        print(json.dumps(TRAINING_CONFIG, indent=2))
        """
    ),
    md(
        """
        ## Load And Split Competition Data

        We keep a deterministic validation slice so every run has a local score before packaging adapters.
        """
    ),
    code(
        r"""
        FAMILY_PATTERNS = [
            ("a secret bit manipulation rule transforms 8-bit binary numbers", "bit_manipulation"),
            ("the gravitational constant has been secretly changed", "gravity_constant"),
            ("a secret unit conversion is applied to measurements", "unit_conversion"),
            ("secret encryption rules are used on text", "text_decryption"),
            ("numbers are secretly converted into a different numeral system", "numeral_system"),
            ("a secret set of transformation rules is applied to equations", "equation_transform"),
        ]

        def classify_prompt_family(prompt: str) -> str:
            lowered = prompt.lower()
            for pattern, family in FAMILY_PATTERNS:
                if pattern in lowered:
                    return family
            return "unknown"

        def deterministic_take(frame: pd.DataFrame, limit: int | None, salt: str) -> pd.DataFrame:
            if limit is None or len(frame) <= limit:
                return frame.reset_index(drop=True)
            ranked = frame.copy()
            ranked["_sort_key"] = ranked["id"].astype(str).map(lambda value: stable_int(f"{salt}:{RANDOM_SEED}:{value}"))
            ranked = ranked.sort_values("_sort_key").head(limit).drop(columns=["_sort_key"])
            return ranked.reset_index(drop=True)

        def split_train_validation(frame: pd.DataFrame, val_fraction: float) -> tuple[pd.DataFrame, pd.DataFrame]:
            train_parts: list[pd.DataFrame] = []
            val_parts: list[pd.DataFrame] = []
            for family, group in frame.groupby("family", sort=False):
                group = group.copy()
                group["_sort_key"] = group["id"].astype(str).map(lambda value: stable_int(f"val:{RANDOM_SEED}:{value}"))
                group = group.sort_values("_sort_key")
                if len(group) <= 1:
                    val_count = 0
                else:
                    val_count = min(max(1, int(round(len(group) * val_fraction))), len(group) - 1)
                val_parts.append(group.head(val_count))
                train_parts.append(group.iloc[val_count:])
            train_split = pd.concat(train_parts, ignore_index=True).drop(columns=["_sort_key"], errors="ignore")
            val_split = pd.concat(val_parts, ignore_index=True).drop(columns=["_sort_key"], errors="ignore")
            return train_split, val_split

        full_train_df = pd.read_csv(TRAIN_DATA_PATH)
        full_train_df["family"] = full_train_df["prompt"].map(classify_prompt_family)
        train_df, val_df = split_train_validation(full_train_df, VAL_FRACTION)
        train_df = deterministic_take(train_df, TRAIN_SAMPLE_LIMIT, "train")
        val_df = deterministic_take(val_df, VAL_SAMPLE_LIMIT, "val")

        train_family_counts = train_df["family"].value_counts().to_dict()
        val_family_counts = val_df["family"].value_counts().to_dict()
        split_summary = {
            "full_train_rows": int(len(full_train_df)),
            "train_rows": int(len(train_df)),
            "validation_rows": int(len(val_df)),
            "train_family_counts": train_family_counts,
            "validation_family_counts": val_family_counts,
        }
        write_json(RUN_ROOT / "split_summary.json", split_summary)
        train_df.to_csv(RUN_ROOT / "train_split.csv", index=False)
        val_df.to_csv(RUN_ROOT / "validation_split.csv", index=False)

        print("Split summary:")
        print(json.dumps(split_summary, indent=2))
        display(train_df.head())
        display(val_df.head())
        """
    ),
    md(
        """
        ## Tokenizer And Training Text

        We train the adapter to return the final answer inside `\\boxed{}`.
        """
    ),
    code(
        r"""
        tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR), trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        def build_training_text(example: dict) -> dict:
            user_msg = example["prompt"] + "\nPut your final answer inside \\boxed{}."
            assistant_msg = f"\\boxed{{{example['answer']}}}"
            try:
                messages = [
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg},
                ]
                text = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=False,
                )
            except Exception:
                text = (
                    f"<|im_start|>user\n{user_msg}<|im_end|>\n"
                    f"<|im_start|>assistant\n{assistant_msg}<|im_end|>"
                )
            return {"text": text}

        train_hf = Dataset.from_pandas(train_df[["id", "prompt", "answer"]].copy(), preserve_index=False)
        train_hf = train_hf.map(build_training_text, remove_columns=train_hf.column_names)

        tokenizer_summary = {
            "model_dir": str(MODEL_DIR),
            "tokenizer_class": tokenizer.__class__.__name__,
            "vocab_size": getattr(tokenizer, "vocab_size", None),
            "train_dataset_rows": int(len(train_hf)),
            "validation_rows": int(len(val_df)),
        }
        write_json(RUN_ROOT / "tokenizer_summary.json", tokenizer_summary)
        print(json.dumps(tokenizer_summary, indent=2))
        print(train_hf[0]["text"][:700])
        """
    ),
    md(
        """
        ## Load Model And Attach LoRA
        """
    ),
    code(
        r"""
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        model = AutoModelForCausalLM.from_pretrained(
            str(MODEL_DIR),
            device_map="auto",
            trust_remote_code=True,
            dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
        )
        model.config.use_cache = False

        postload_patch_summary = patch_loaded_nemotron_modules(force_slow_path=True)
        write_json(RUN_ROOT / "postload_patch_summary.json", postload_patch_summary)
        print(json.dumps(postload_patch_summary, indent=2))

        lora_config = LoraConfig(
            r=LORA_RANK,
            lora_alpha=LORA_ALPHA,
            target_modules=TARGET_MODULES,
            lora_dropout=LORA_DROPOUT,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

        def model_input_device(active_model):
            if hasattr(active_model, "device"):
                return active_model.device
            return next(iter(active_model.parameters())).device

        model_summary = {
            "model_dir": str(MODEL_DIR),
            "input_device": str(model_input_device(model)),
            "device_map": getattr(model, "hf_device_map", "single-device"),
            "torch_dtype": "bfloat16",
            "lora_rank": LORA_RANK,
            "target_modules": TARGET_MODULES,
        }
        write_json(RUN_ROOT / "model_summary.json", model_summary)
        print(json.dumps(model_summary, indent=2))
        """
    ),
    md(
        """
        ## Train Adapter
        """
    ),
    code(
        r"""
        effective_batch = PER_DEVICE_BATCH_SIZE * GRAD_ACCUM
        steps_per_epoch = max(1, math.ceil(len(train_hf) / effective_batch))
        total_steps = max(1, steps_per_epoch * NUM_EPOCHS)
        warmup_steps = max(1, total_steps // 10)

        training_args = SFTConfig(
            output_dir=str(OUTPUT_DIR),
            per_device_train_batch_size=PER_DEVICE_BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM,
            num_train_epochs=NUM_EPOCHS,
            learning_rate=LEARNING_RATE,
            weight_decay=WEIGHT_DECAY,
            logging_steps=max(1, total_steps // 20),
            bf16=True,
            max_grad_norm=MAX_GRAD_NORM,
            optim="adamw_torch",
            lr_scheduler_type="cosine",
            warmup_steps=warmup_steps,
            save_strategy="no",
            report_to="none",
            dataset_text_field="text",
            max_length=MAX_SEQ_LEN,
            packing=False,
            gradient_checkpointing=True,
            gradient_checkpointing_kwargs={"use_reentrant": True},
        )

        trainer = SFTTrainer(
            model=model,
            train_dataset=train_hf,
            processing_class=tokenizer,
            args=training_args,
        )

        print("Starting training...")
        train_result = trainer.train()
        train_metrics = {key: float(value) if isinstance(value, (int, float)) else value for key, value in train_result.metrics.items()}
        train_metrics["steps_per_epoch"] = steps_per_epoch
        train_metrics["total_steps_estimate"] = total_steps
        train_metrics["warmup_steps"] = warmup_steps
        write_json(RUN_ROOT / "train_metrics.json", train_metrics)
        print(json.dumps(train_metrics, indent=2))
        """
    ),
    md(
        """
        ## Validation Score

        This is the local sanity check before packaging adapters.
        """
    ),
    code(
        r"""
        def tokenize_messages(messages, enable_thinking=False):
            kwargs = {
                "tokenize": True,
                "add_generation_prompt": True,
                "return_tensors": "pt",
            }
            try:
                return tokenizer.apply_chat_template(messages, enable_thinking=enable_thinking, **kwargs)
            except TypeError:
                return tokenizer.apply_chat_template(messages, **kwargs)

        def extract_boxed_answer(text: str) -> str | None:
            matches = re.findall(r"\\boxed\{([^{}]*)\}", text)
            if matches:
                return matches[-1].strip()
            return None

        def normalize_answer(text: str | None) -> str:
            if text is None:
                return ""
            return re.sub(r"\s+", " ", str(text).strip())

        model.eval()
        model.config.use_cache = True

        validation_records = []
        family_correct: dict[str, int] = {}
        family_total: dict[str, int] = {}
        validation_started = time.perf_counter()

        for record in val_df.to_dict(orient="records"):
            prompt_text = record["prompt"] + "\nPut your final answer inside \\boxed{}."
            messages = [{"role": "user", "content": prompt_text}]
            inputs = tokenize_messages(messages, enable_thinking=False).to(model_input_device(model))

            with torch.no_grad():
                outputs = model.generate(
                    inputs,
                    max_new_tokens=EVAL_MAX_NEW_TOKENS,
                    do_sample=False,
                    num_beams=1,
                    eos_token_id=tokenizer.eos_token_id,
                )

            generated_tokens = outputs[0][inputs.shape[-1]:]
            generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=False)
            predicted_answer = extract_boxed_answer(generated_text)
            normalized_prediction = normalize_answer(predicted_answer)
            normalized_target = normalize_answer(record["answer"])
            matched = normalized_prediction == normalized_target

            family = record["family"]
            family_total[family] = family_total.get(family, 0) + 1
            if matched:
                family_correct[family] = family_correct.get(family, 0) + 1

            validation_records.append(
                {
                    "id": record["id"],
                    "family": family,
                    "answer": record["answer"],
                    "predicted_answer": predicted_answer,
                    "generated_text": generated_text,
                    "exact_match": matched,
                }
            )

        validation_df = pd.DataFrame(validation_records)
        validation_df.to_csv(VALIDATION_PREDICTIONS_PATH, index=False)

        family_accuracy = {}
        for family, total in family_total.items():
            correct = family_correct.get(family, 0)
            family_accuracy[family] = {
                "correct": correct,
                "total": total,
                "accuracy": (correct / total) if total else 0.0,
            }

        overall_accuracy = float(validation_df["exact_match"].mean()) if len(validation_df) else 0.0
        validation_summary = {
            "rows": int(len(validation_df)),
            "overall_exact_match": overall_accuracy,
            "family_accuracy": family_accuracy,
            "latency_ms": int((time.perf_counter() - validation_started) * 1000),
            "predictions_path": str(VALIDATION_PREDICTIONS_PATH),
        }
        write_json(RUN_ROOT / "validation_summary.json", validation_summary)
        print(json.dumps(validation_summary, indent=2))
        display(validation_df.head())
        """
    ),
    md(
        """
        ## Package Adapter Submission
        """
    ),
    code(
        r"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        trainer.model.save_pretrained(OUTPUT_DIR)
        tokenizer.save_pretrained(RUN_ROOT / "tokenizer")

        adapter_files = sorted(path.name for path in OUTPUT_DIR.iterdir() if path.is_file())
        print("Adapter files:")
        for name in adapter_files:
            size_kb = (OUTPUT_DIR / name).stat().st_size / 1024
            print(f"- {name} ({size_kb:.1f} KB)")

        versioned_zip_path = WORK_ROOT / f"submission_{RUN_ID}.zip"
        canonical_zip_path = WORK_ROOT / "submission.zip"

        with zipfile.ZipFile(versioned_zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(OUTPUT_DIR.iterdir()):
                if path.is_file():
                    archive.write(path, path.name)

        shutil.copy2(versioned_zip_path, canonical_zip_path)

        with zipfile.ZipFile(versioned_zip_path, "r") as archive:
            names = sorted(archive.namelist())

        assert "adapter_config.json" in names, "Missing adapter_config.json in submission zip."

        packaging_summary = {
            "adapter_dir": str(OUTPUT_DIR),
            "adapter_files": adapter_files,
            "versioned_zip_path": str(versioned_zip_path),
            "canonical_zip_path": str(canonical_zip_path),
            "zip_contents": names,
        }
        write_json(RUN_ROOT / "packaging_summary.json", packaging_summary)
        print(json.dumps(packaging_summary, indent=2))
        print("Submission zip is ready:", canonical_zip_path)
        """
    ),
]


notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.12",
            "mimetype": "text/x-python",
            "codemirror_mode": {"name": "ipython", "version": 3},
            "pygments_lexer": "ipython3",
            "nbconvert_exporter": "python",
            "file_extension": ".py",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}


NOTEBOOK_PATH.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
print(f"Wrote {NOTEBOOK_PATH}")
