#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import tarfile
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_if_needed(source: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if source.is_dir():
        return source, None

    scratch = tempfile.TemporaryDirectory(prefix="kaggle_run_import_")
    scratch_root = Path(scratch.name)

    if source.suffix == ".zip":
        with zipfile.ZipFile(source) as archive:
            archive.extractall(scratch_root)
        return scratch_root, scratch

    if source.suffixes[-2:] == [".tar", ".gz"] or source.suffix == ".tgz":
        with tarfile.open(source) as archive:
            archive.extractall(scratch_root)
        return scratch_root, scratch

    raise ValueError(f"Unsupported source format: {source}")


def find_run_root(search_root: Path) -> Path:
    direct_summary = search_root / "session_summary.json"
    if direct_summary.exists():
        return search_root

    candidates = sorted(search_root.rglob("session_summary.json"))
    if not candidates:
        raise FileNotFoundError(
            f"No session_summary.json found under {search_root}. "
            "Expected a Kaggle run folder or exported zip from /kaggle/working."
        )
    return candidates[0].parent


def update_index(index_path: Path, record: dict) -> None:
    existing: list[dict] = []
    if index_path.exists():
        existing = json.loads(index_path.read_text(encoding="utf-8"))

    filtered = [item for item in existing if item.get("run_id") != record.get("run_id")]
    filtered.insert(0, record)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(filtered, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import a Kaggle notebook run artifact folder or zip into repo artifacts."
    )
    parser.add_argument("source", help="Path to a Kaggle run directory or exported zip/tar.gz.")
    parser.add_argument(
        "--destination-root",
        default=None,
        help="Optional destination root. Defaults to <repo>/artifacts/kaggle_runs.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    source = Path(args.source).expanduser().resolve()
    destination_root = (
        Path(args.destination_root).expanduser().resolve()
        if args.destination_root
        else repo_root / "artifacts" / "kaggle_runs"
    )

    extracted_root, scratch = extract_if_needed(source)
    try:
        run_root = find_run_root(extracted_root)
        summary_path = run_root / "session_summary.json"
        events_path = run_root / "events.jsonl"

        if not events_path.exists():
            raise FileNotFoundError(f"Expected events log at {events_path}")

        summary = load_json(summary_path)
        run_id = str(summary.get("run_id") or run_root.name)

        destination_dir = destination_root / run_id
        destination_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(run_root, destination_dir, dirs_exist_ok=True)

        index_record = {
            "run_id": run_id,
            "imported_at": utc_now_iso(),
            "source": str(source),
            "destination_dir": str(destination_dir),
            "gpu_name": summary.get("runtime", {}).get("gpu_name"),
            "model_dir": summary.get("model_selection", {}).get("selected_model_dir"),
            "submission_path": summary.get("submission", {}).get("artifact_submission_path"),
            "export_bundle_path": summary.get("export_bundle_path"),
        }
        update_index(destination_root / "index.json", index_record)

        print("Imported Kaggle run")
        print("run_id:", run_id)
        print("source:", source)
        print("destination:", destination_dir)
        print("gpu_name:", index_record["gpu_name"])
        print("model_dir:", index_record["model_dir"])
        return 0
    finally:
        if scratch is not None:
            scratch.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
