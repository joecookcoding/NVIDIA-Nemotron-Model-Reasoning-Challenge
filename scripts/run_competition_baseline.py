#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from nemotron_platform.competition_baseline import (  # noqa: E402
    BaselinePrediction,
    build_stratified_folds,
    exact_match_score,
    load_competition_rows,
    solve_row,
)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local competition baseline against train/test CSV files."
    )
    parser.add_argument(
        "--train-path",
        default=str(REPO_ROOT / "docs" / "train.csv"),
        help="Path to a competition-format train.csv file.",
    )
    parser.add_argument(
        "--test-path",
        default=str(REPO_ROOT / "docs" / "test.csv"),
        help="Path to a competition-format test.csv file.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory. Defaults to artifacts/competition_baseline/<timestamp>.",
    )
    parser.add_argument(
        "--folds",
        type=int,
        default=5,
        help="Number of stratified folds to assign for local validation bookkeeping.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Random seed used for fold assignment.",
    )
    parser.add_argument(
        "--skip-test-predictions",
        action="store_true",
        help="Skip generating predictions/submission.csv for the test split.",
    )
    return parser.parse_args()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_predictions_csv(path: Path, predictions: list[BaselinePrediction]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "task_id",
                "family",
                "prediction",
                "solver",
                "solved",
                "fold_index",
                "notes",
            ],
        )
        writer.writeheader()
        for prediction in predictions:
            writer.writerow(
                {
                    "task_id": prediction.task_id,
                    "family": prediction.family.value,
                    "prediction": prediction.prediction or "",
                    "solver": prediction.solver,
                    "solved": str(prediction.solved).lower(),
                    "fold_index": prediction.fold_index if prediction.fold_index is not None else "",
                    "notes": prediction.notes,
                }
            )


def write_submission_csv(path: Path, predictions: list[BaselinePrediction]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "answer"])
        writer.writeheader()
        for prediction in predictions:
            writer.writerow(
                {
                    "id": prediction.task_id,
                    "answer": prediction.prediction or "",
                }
            )


def build_train_summary(
    output_dir: Path,
    train_rows,
    folds: int,
    seed: int,
) -> dict[str, object]:
    fold_assignments = build_stratified_folds(train_rows, folds=folds, seed=seed)
    predictions = []
    for row in train_rows:
        prediction = solve_row(row)
        prediction.fold_index = fold_assignments.get(row.task_id)
        predictions.append(prediction)

    score, family_stats = exact_match_score(train_rows, predictions)
    solved_count = sum(1 for prediction in predictions if prediction.solved)

    fold_rows: dict[int, list] = defaultdict(list)
    fold_predictions: dict[int, list[BaselinePrediction]] = defaultdict(list)
    for row in train_rows:
        fold_index = fold_assignments[row.task_id]
        fold_rows[fold_index].append(row)
    for prediction in predictions:
        if prediction.fold_index is not None:
            fold_predictions[prediction.fold_index].append(prediction)

    fold_summaries = []
    for fold_index in sorted(fold_rows):
        fold_score, _ = exact_match_score(fold_rows[fold_index], fold_predictions[fold_index])
        fold_summaries.append(
            {
                "fold_index": fold_index,
                "row_count": len(fold_rows[fold_index]),
                "accuracy": fold_score,
            }
        )

    family_counts = Counter(row.family.value for row in train_rows)
    solved_by_family = Counter(
        prediction.family.value for prediction in predictions if prediction.solved
    )

    write_predictions_csv(output_dir / "train_predictions.csv", predictions)
    write_json(output_dir / "fold_assignments.json", fold_assignments)

    summary = {
        "train_row_count": len(train_rows),
        "overall_accuracy": score,
        "solved_count": solved_count,
        "solved_rate": (solved_count / len(train_rows)) if train_rows else 0.0,
        "family_counts": dict(sorted(family_counts.items())),
        "solved_by_family": dict(sorted(solved_by_family.items())),
        "family_accuracy": family_stats,
        "fold_summaries": fold_summaries,
        "artifacts": {
            "train_predictions": str((output_dir / "train_predictions.csv").relative_to(REPO_ROOT)),
            "fold_assignments": str((output_dir / "fold_assignments.json").relative_to(REPO_ROOT)),
        },
    }
    return summary


def build_test_predictions(output_dir: Path, test_rows) -> dict[str, str]:
    predictions = [solve_row(row) for row in test_rows]
    write_predictions_csv(output_dir / "test_predictions.csv", predictions)
    write_submission_csv(output_dir / "submission.csv", predictions)
    return {
        "test_predictions": str((output_dir / "test_predictions.csv").relative_to(REPO_ROOT)),
        "submission": str((output_dir / "submission.csv").relative_to(REPO_ROOT)),
    }


def main() -> int:
    args = parse_args()
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else (REPO_ROOT / "artifacts" / "competition_baseline" / utc_timestamp())
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    train_rows = load_competition_rows(Path(args.train_path))
    summary = build_train_summary(output_dir, train_rows, folds=args.folds, seed=args.seed)
    summary["train_path"] = str(Path(args.train_path))
    summary["test_path"] = str(Path(args.test_path))

    if not args.skip_test_predictions:
        test_rows = load_competition_rows(Path(args.test_path))
        summary["test_row_count"] = len(test_rows)
        summary["test_artifacts"] = build_test_predictions(output_dir, test_rows)

    write_json(output_dir / "summary.json", summary)

    print("Competition baseline summary")
    print("output_dir:", output_dir)
    print("train_row_count:", summary["train_row_count"])
    print("overall_accuracy:", f"{summary['overall_accuracy']:.4f}")
    print("solved_rate:", f"{summary['solved_rate']:.4f}")
    for family, stats in summary["family_accuracy"].items():
        print(
            f"family={family} accuracy={stats['accuracy']:.4f} "
            f"correct={stats['correct']} total={stats['total']}"
        )
    if "test_artifacts" in summary:
        print("submission:", output_dir / "submission.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
