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


NOTEBOOK_PATH = Path("notebooks/nvidia-nemotron-submission-demo.ipynb")


cells = [
    md(
        """
        # Nemotron Submission Demo

        Minimal offline LoRA submission notebook for the NVIDIA Nemotron Model Reasoning Challenge.

        Goals:

        - keep the flow simple,
        - train a small adapter quickly,
        - save the adapter files,
        - package `submission.zip`.
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
        import shutil
        import site
        import stat
        import subprocess
        import sys
        import zipfile
        from datetime import datetime, timezone
        from pathlib import Path

        import pandas as pd
        import torch

        INPUT_ROOT = Path("/kaggle/input")
        WORK_ROOT = Path("/kaggle/working")
        RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        RUN_ROOT = WORK_ROOT / "artifacts" / "submission_demo_runs" / RUN_ID
        RUN_ROOT.mkdir(parents=True, exist_ok=True)

        EXTRA_SITE_DIRS = [
            WORK_ROOT,
            WORK_ROOT / "site-packages",
            WORK_ROOT / "python",
            WORK_ROOT / "deps",
        ]
        ACTIVE_EXTRA_SITE_DIRS: list[str] = []
        for path in EXTRA_SITE_DIRS:
            if path.exists():
                site.addsitedir(str(path))
                if str(path) not in sys.path:
                    sys.path.insert(0, str(path))
                ACTIVE_EXTRA_SITE_DIRS.append(str(path))

        def write_json(path: Path, payload) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")

        def discover_wheelhouse_dirs(root: Path) -> list[Path]:
            wheel_counts: dict[Path, int] = {}
            for wheel_path in root.rglob("*.whl"):
                wheel_counts[wheel_path.parent] = wheel_counts.get(wheel_path.parent, 0) + 1
            return sorted(wheel_counts, key=lambda path: (-wheel_counts[path], str(path)))

        def wheelhouse_has_package(wheelhouse: Path | None, package_prefixes: tuple[str, ...]) -> bool:
            if wheelhouse is None:
                return False
            normalized_prefixes = tuple(prefix.lower().replace("-", "_") for prefix in package_prefixes)
            for wheel_path in wheelhouse.glob("*.whl"):
                stem = wheel_path.name.lower().replace("-", "_")
                if any(stem.startswith(prefix) for prefix in normalized_prefixes):
                    return True
            return False

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

        def find_competition_train() -> Path | None:
            candidates = sorted(
                path for path in INPUT_ROOT.rglob("train.csv")
                if "competition" in str(path).lower()
            )
            return candidates[0] if candidates else None

        WHEELHOUSE_SCAN_ROOTS = [
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
        WHEELHOUSE_DIRS: list[Path] = []
        for root in WHEELHOUSE_SCAN_ROOTS:
            WHEELHOUSE_DIRS.extend(discover_wheelhouse_dirs(root))

        OFFLINE_PACKAGE_ROOT = next(
            (
                path for path in WHEELHOUSE_DIRS
                if wheelhouse_has_package(path, ("datasets", "trl", "peft", "mamba_ssm"))
            ),
            None,
        )
        MODEL_DIR = (find_model_candidates(INPUT_ROOT) or [None])[0]
        TRAIN_DATA_PATH = find_competition_train()

        REQUIRED_MODULES = ["datasets", "trl", "peft", "mamba_ssm"]
        REQUIRED_STATUS = {name: importlib.util.find_spec(name) is not None for name in REQUIRED_MODULES}
        MISSING_MODULES = [name for name, present in REQUIRED_STATUS.items() if not present]

        assert torch.cuda.is_available(), "Turn on a GPU before running the demo notebook."
        assert MODEL_DIR is not None, "Attach the Nemotron model to the notebook."
        assert TRAIN_DATA_PATH is not None, "Attach the competition train.csv input."

        if MISSING_MODULES:
            assert OFFLINE_PACKAGE_ROOT is not None, "Could not find the offline package wheelhouse."
            wheel_map, missing_wheels = select_package_wheels(
                OFFLINE_PACKAGE_ROOT,
                ("datasets", "trl", "peft", "mamba_ssm", "ninja", "packaging"),
            )
            if missing_wheels:
                raise RuntimeError(
                    "Missing compatible offline wheels for: " + ", ".join(missing_wheels)
                )
            install_command = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--no-index",
                "--ignore-installed",
            ]
            for package_name in ("datasets", "trl", "peft", "mamba_ssm", "ninja", "packaging"):
                install_command.extend(str(path) for path in wheel_map.get(package_name, []))
            print("Installing offline packages from:", OFFLINE_PACKAGE_ROOT)
            print("Resolved wheel files:", {name: [path.name for path in paths] for name, paths in wheel_map.items()})
            subprocess.check_call(install_command)
            importlib.invalidate_caches()

        setup_summary = {
            "run_id": RUN_ID,
            "run_root": str(RUN_ROOT),
            "offline_package_root": str(OFFLINE_PACKAGE_ROOT),
            "model_dir": str(MODEL_DIR),
            "train_data_path": str(TRAIN_DATA_PATH),
            "torch_version": torch.__version__,
            "torch_cuda_build": torch.version.cuda,
            "gpu_name": torch.cuda.get_device_name(0),
            "gpu_capability": torch.cuda.get_device_capability(0),
            "active_extra_site_dirs": ACTIVE_EXTRA_SITE_DIRS,
            "required_status": REQUIRED_STATUS,
        }
        write_json(RUN_ROOT / "setup_summary.json", setup_summary)
        print(json.dumps(setup_summary, indent=2))
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
            patched = {"rmsnorm_modules": [], "slow_path_modules": []}

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
            copied_from = None
            for src in src_candidates:
                if src.exists():
                    shutil.copy2(src, dst)
                    os.chmod(dst, os.stat(dst).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                    os.environ["TRITON_PTXAS_PATH"] = str(dst)
                    os.environ["TRITON_PTXAS_BLACKWELL_PATH"] = str(dst)
                    copied_from = str(src)
                    break
            nv_compiler.get_ptxas_version = lambda arch: "12.0"
            return {"copied_from": copied_from, "ptxas_path": str(dst) if copied_from else None}

        runtime_patch_summary = {
            "preload_patch": patch_loaded_nemotron_modules(force_slow_path=False),
            "blackwell_triton": configure_blackwell_triton(),
        }
        write_json(RUN_ROOT / "runtime_patch_summary.json", runtime_patch_summary)
        print(json.dumps(runtime_patch_summary, indent=2))

        SUBSAMPLE_SIZE = 600
        LORA_RANK = 32
        MAX_SEQ_LEN = 1024
        NUM_EPOCHS = 1
        PER_DEVICE_BATCH_SIZE = 1
        GRAD_ACCUM = 4
        LEARNING_RATE = 2e-4
        OUTPUT_DIR = RUN_ROOT / "adapter"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        """
    ),
    code(
        r"""
        train_df = pd.read_csv(TRAIN_DATA_PATH).sample(n=SUBSAMPLE_SIZE, random_state=42).reset_index(drop=True)
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
                text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            except Exception:
                text = (
                    f"<|im_start|>user\n{user_msg}<|im_end|>\n"
                    f"<|im_start|>assistant\n{assistant_msg}<|im_end|>"
                )
            return {"text": text}

        train_hf = Dataset.from_pandas(train_df[["id", "prompt", "answer"]].copy(), preserve_index=False)
        train_hf = train_hf.map(build_training_text, remove_columns=train_hf.column_names)
        print(train_hf[0]["text"][:700])
        """
    ),
    code(
        r"""
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

        gc.collect()
        torch.cuda.empty_cache()

        model = AutoModelForCausalLM.from_pretrained(
            str(MODEL_DIR),
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
        )
        model.config.use_cache = False
        postload_patch_summary = patch_loaded_nemotron_modules(force_slow_path=True)
        write_json(RUN_ROOT / "postload_patch_summary.json", postload_patch_summary)
        print(json.dumps(postload_patch_summary, indent=2))

        lora_config = LoraConfig(
            r=LORA_RANK,
            lora_alpha=16,
            target_modules=r".*\.(in_proj|out_proj|up_proj|down_proj)$",
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
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
            logging_steps=max(1, total_steps // 20),
            bf16=True,
            max_grad_norm=1.0,
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
        write_json(RUN_ROOT / "train_metrics.json", train_result.metrics)
        print(json.dumps(train_result.metrics, indent=2))
        """
    ),
    code(
        r"""
        trainer.model.save_pretrained(OUTPUT_DIR)

        adapter_files = sorted(path.name for path in OUTPUT_DIR.iterdir() if path.is_file())
        print("Adapter files:")
        for name in adapter_files:
            print("-", name)

        zip_path = WORK_ROOT / "submission.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(OUTPUT_DIR.iterdir()):
                if path.is_file():
                    archive.write(path, path.name)

        with zipfile.ZipFile(zip_path, "r") as archive:
            names = sorted(archive.namelist())
        assert "adapter_config.json" in names, "Missing adapter_config.json!"

        packaging_summary = {
            "adapter_dir": str(OUTPUT_DIR),
            "adapter_files": adapter_files,
            "submission_zip": str(zip_path),
            "zip_contents": names,
        }
        write_json(RUN_ROOT / "packaging_summary.json", packaging_summary)
        print(json.dumps(packaging_summary, indent=2))
        print("submission.zip is ready.")
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
