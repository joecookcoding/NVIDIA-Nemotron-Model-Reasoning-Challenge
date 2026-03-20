from __future__ import annotations

from pathlib import Path
import unittest

from nemotron_platform.competition_baseline import (
    CompetitionFamily,
    build_stratified_folds,
    classify_prompt_family,
    exact_match_score,
    load_competition_rows,
    solve_row,
)


class CompetitionBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        cls.rows = load_competition_rows(repo_root / "docs" / "train.csv")
        cls.by_id = {row.task_id: row for row in cls.rows}

    def test_classify_prompt_family_covers_known_templates(self) -> None:
        self.assertEqual(
            classify_prompt_family(self.by_id["00066667"].prompt),
            CompetitionFamily.BIT_MANIPULATION,
        )
        self.assertEqual(
            classify_prompt_family(self.by_id["00189f6a"].prompt),
            CompetitionFamily.TEXT_DECRYPTION,
        )
        self.assertEqual(
            classify_prompt_family(self.by_id["001b24c4"].prompt),
            CompetitionFamily.NUMERAL_SYSTEM,
        )

    def test_roman_solver_returns_expected_answer(self) -> None:
        prediction = solve_row(self.by_id["001b24c4"])
        self.assertEqual(prediction.prediction, "XXXVIII")

    def test_gravity_solver_returns_expected_answer(self) -> None:
        prediction = solve_row(self.by_id["0040ff76"])
        self.assertEqual(prediction.prediction, "154.62")

    def test_unit_conversion_solver_returns_expected_answer(self) -> None:
        prediction = solve_row(self.by_id["00208201"])
        self.assertEqual(prediction.prediction, "16.65")

    def test_decryption_solver_can_solve_supported_prompt(self) -> None:
        solvable_row = next(
            row
            for row in self.rows
            if row.family == CompetitionFamily.TEXT_DECRYPTION
            and solve_row(row).prediction is not None
        )
        prediction = solve_row(solvable_row)
        self.assertEqual(prediction.prediction, solvable_row.answer)

    def test_bit_manipulation_solver_can_solve_supported_prompt(self) -> None:
        solvable_row = next(
            row
            for row in self.rows
            if row.family == CompetitionFamily.BIT_MANIPULATION
            and solve_row(row).prediction is not None
        )
        prediction = solve_row(solvable_row)
        self.assertEqual(prediction.prediction, solvable_row.answer)

    def test_build_stratified_folds_assigns_every_row(self) -> None:
        assignments = build_stratified_folds(self.rows[:100], folds=5, seed=7)
        self.assertEqual(len(assignments), 100)
        self.assertTrue(all(0 <= fold < 5 for fold in assignments.values()))

    def test_exact_match_score_reports_family_stats(self) -> None:
        subset = self.rows[:20]
        predictions = [solve_row(row) for row in subset]
        score, family_stats = exact_match_score(subset, predictions)

        self.assertGreaterEqual(score, 0.0)
        self.assertIn(CompetitionFamily.BIT_MANIPULATION.value, family_stats)


if __name__ == "__main__":
    unittest.main()
