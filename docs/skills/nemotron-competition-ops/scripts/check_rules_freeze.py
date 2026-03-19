#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    repo_root = Path(__file__).resolve().parents[4]
    competition_dir = repo_root / "docs" / "competition"
    required = [
        competition_dir / "source_capture.md",
        competition_dir / "compliance_matrix.md",
        competition_dir / "submission_contract.md",
    ]

    missing = [path for path in required if not path.exists()]
    if missing:
        for path in missing:
            print(f"MISSING {path.relative_to(repo_root)}")
        return 1

    print("Competition source capture files are present.")
    frozen_flag = competition_dir / "rules_frozen.md"
    if frozen_flag.exists():
        print("Rules freeze marker detected.")
    else:
        print("Rules freeze marker not detected; treat submission assumptions as provisional.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

