from __future__ import annotations

import csv
import random
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path


class CompetitionFamily(str, Enum):
    BIT_MANIPULATION = "bit_manipulation"
    GRAVITY_CONSTANT = "gravity_constant"
    UNIT_CONVERSION = "unit_conversion"
    TEXT_DECRYPTION = "text_decryption"
    NUMERAL_SYSTEM = "numeral_system"
    EQUATION_TRANSFORM = "equation_transform"
    UNKNOWN = "unknown"


_FAMILY_PATTERNS: list[tuple[str, CompetitionFamily]] = [
    (
        "a secret bit manipulation rule transforms 8-bit binary numbers",
        CompetitionFamily.BIT_MANIPULATION,
    ),
    (
        "the gravitational constant has been secretly changed",
        CompetitionFamily.GRAVITY_CONSTANT,
    ),
    (
        "a secret unit conversion is applied to measurements",
        CompetitionFamily.UNIT_CONVERSION,
    ),
    (
        "secret encryption rules are used on text",
        CompetitionFamily.TEXT_DECRYPTION,
    ),
    (
        "numbers are secretly converted into a different numeral system",
        CompetitionFamily.NUMERAL_SYSTEM,
    ),
    (
        "a secret set of transformation rules is applied to equations",
        CompetitionFamily.EQUATION_TRANSFORM,
    ),
]

_ROMAN_NUMERALS: list[tuple[int, str]] = [
    (1000, "M"),
    (900, "CM"),
    (500, "D"),
    (400, "CD"),
    (100, "C"),
    (90, "XC"),
    (50, "L"),
    (40, "XL"),
    (10, "X"),
    (9, "IX"),
    (5, "V"),
    (4, "IV"),
    (1, "I"),
]


@dataclass(slots=True)
class CompetitionRow:
    task_id: str
    prompt: str
    answer: str | None
    family: CompetitionFamily


@dataclass(slots=True)
class BaselinePrediction:
    task_id: str
    family: CompetitionFamily
    prediction: str | None
    solver: str
    solved: bool
    fold_index: int | None = None
    notes: str = ""


def classify_prompt_family(prompt: str) -> CompetitionFamily:
    lowered = prompt.lower()
    for pattern, family in _FAMILY_PATTERNS:
        if pattern in lowered:
            return family
    return CompetitionFamily.UNKNOWN


def load_competition_rows(path: Path) -> list[CompetitionRow]:
    rows: list[CompetitionRow] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for record in reader:
            task_id = str(record.get("id", "")).strip()
            prompt = str(record.get("prompt", "")).strip()
            answer = record.get("answer")
            if not task_id or not prompt:
                continue
            rows.append(
                CompetitionRow(
                    task_id=task_id,
                    prompt=prompt,
                    answer=answer.strip() if isinstance(answer, str) else None,
                    family=classify_prompt_family(prompt),
                )
            )
    return rows


def build_stratified_folds(
    rows: list[CompetitionRow], folds: int = 5, seed: int = 7
) -> dict[str, int]:
    by_family: dict[CompetitionFamily, list[CompetitionRow]] = {}
    for row in rows:
        by_family.setdefault(row.family, []).append(row)

    rng = random.Random(seed)
    assignments: dict[str, int] = {}
    for family_rows in by_family.values():
        shuffled = family_rows[:]
        rng.shuffle(shuffled)
        for index, row in enumerate(shuffled):
            assignments[row.task_id] = index % folds
    return assignments


def exact_match_score(
    rows: list[CompetitionRow], predictions: list[BaselinePrediction]
) -> tuple[float, dict[str, dict[str, float | int]]]:
    prediction_map = {prediction.task_id: prediction for prediction in predictions}
    correct = 0
    total = 0
    family_stats: dict[str, dict[str, float | int]] = {}

    for row in rows:
        if row.answer is None:
            continue
        total += 1
        prediction = prediction_map.get(row.task_id)
        predicted_text = prediction.prediction if prediction is not None else None
        matched = predicted_text == row.answer
        if matched:
            correct += 1

        stats = family_stats.setdefault(
            row.family.value,
            {"total": 0, "correct": 0, "accuracy": 0.0},
        )
        stats["total"] = int(stats["total"]) + 1
        if matched:
            stats["correct"] = int(stats["correct"]) + 1

    for stats in family_stats.values():
        total_count = int(stats["total"])
        correct_count = int(stats["correct"])
        stats["accuracy"] = (correct_count / total_count) if total_count else 0.0

    return (correct / total) if total else 0.0, family_stats


def solve_row(row: CompetitionRow) -> BaselinePrediction:
    solver_name = f"{row.family.value}_baseline"
    prediction: str | None = None
    notes = ""

    if row.family == CompetitionFamily.NUMERAL_SYSTEM:
        prediction = _solve_roman_numeral(row.prompt)
    elif row.family == CompetitionFamily.GRAVITY_CONSTANT:
        prediction = _solve_gravity_constant(row.prompt)
    elif row.family == CompetitionFamily.UNIT_CONVERSION:
        prediction = _solve_unit_conversion(row.prompt)
    elif row.family == CompetitionFamily.TEXT_DECRYPTION:
        prediction = _solve_text_decryption(row.prompt)
    elif row.family == CompetitionFamily.BIT_MANIPULATION:
        prediction = _solve_bit_manipulation_affine(row.prompt)
    else:
        notes = "No heuristic solver is implemented for this family yet."

    if prediction is None and not notes:
        notes = "Heuristic solver could not infer a deterministic answer."

    return BaselinePrediction(
        task_id=row.task_id,
        family=row.family,
        prediction=prediction,
        solver=solver_name,
        solved=prediction is not None,
        notes=notes,
    )


def _solve_roman_numeral(prompt: str) -> str | None:
    match = re.search(
        r"Now, write the number ([0-9]+) in the Wonderland numeral system\.", prompt
    )
    if match is None:
        return None
    value = int(match.group(1))
    pieces: list[str] = []
    for amount, symbol in _ROMAN_NUMERALS:
        while value >= amount:
            value -= amount
            pieces.append(symbol)
    return "".join(pieces)


def _solve_gravity_constant(prompt: str) -> str | None:
    examples = [
        (Decimal(time_value), Decimal(distance_value))
        for time_value, distance_value in re.findall(
            r"For t = ([0-9.]+)s, distance = ([0-9.]+) m", prompt
        )
    ]
    query_match = re.search(
        r"for t = ([0-9.]+)s given d = 0.5\*g\*t\^2", prompt
    )
    if not examples or query_match is None:
        return None

    lower_bound: Decimal | None = None
    upper_bound: Decimal | None = None
    for time_value, distance_value in examples:
        time_squared = time_value * time_value
        local_lower = (Decimal("2") * (distance_value - Decimal("0.005"))) / time_squared
        local_upper = (Decimal("2") * (distance_value + Decimal("0.005"))) / time_squared
        lower_bound = local_lower if lower_bound is None else max(lower_bound, local_lower)
        upper_bound = local_upper if upper_bound is None else min(upper_bound, local_upper)

    if lower_bound is None or upper_bound is None or not lower_bound < upper_bound:
        gravity_constant = sum(
            (Decimal("2") * distance_value) / (time_value * time_value)
            for time_value, distance_value in examples
        ) / Decimal(len(examples))
    else:
        gravity_constant = (lower_bound + upper_bound) / Decimal("2")

    query_time = Decimal(query_match.group(1))
    predicted_distance = Decimal("0.5") * gravity_constant * query_time * query_time
    return _format_decimal(predicted_distance, keep_two_places=False)


def _solve_unit_conversion(prompt: str) -> str | None:
    examples = [
        (Decimal(source_value), Decimal(target_value))
        for source_value, target_value in re.findall(
            r"([0-9.]+) m becomes ([0-9.]+)", prompt
        )
    ]
    query_match = re.search(
        r"Now, convert the following measurement: ([0-9.]+) m", prompt
    )
    if not examples or query_match is None:
        return None

    lower_bound: Decimal | None = None
    upper_bound: Decimal | None = None
    for source_value, target_value in examples:
        local_lower = (target_value - Decimal("0.005")) / source_value
        local_upper = (target_value + Decimal("0.005")) / source_value
        lower_bound = local_lower if lower_bound is None else max(lower_bound, local_lower)
        upper_bound = local_upper if upper_bound is None else min(upper_bound, local_upper)

    if lower_bound is None or upper_bound is None or not lower_bound < upper_bound:
        multiplier = sum(target / source for source, target in examples) / Decimal(
            len(examples)
        )
    else:
        multiplier = (lower_bound + upper_bound) / Decimal("2")

    query_value = Decimal(query_match.group(1))
    predicted_value = multiplier * query_value
    return _format_decimal(predicted_value, keep_two_places=True)


def _solve_text_decryption(prompt: str) -> str | None:
    parts = prompt.split("Now, decrypt the following text:")
    if len(parts) != 2:
        return None
    examples_text, query_text = parts
    example_pairs = re.findall(r"([^\n]+?) -> ([^\n]+)", examples_text)

    source_to_target: dict[str, str] = {}
    target_to_source: dict[str, str] = {}
    for source, target in example_pairs:
        if len(source) != len(target):
            return None
        for source_char, target_char in zip(source, target):
            if source_to_target.get(source_char, target_char) != target_char:
                return None
            if target_to_source.get(target_char, source_char) != source_char:
                return None
            source_to_target[source_char] = target_char
            target_to_source[target_char] = source_char

    query = query_text.strip()
    if any(char != " " and char not in source_to_target for char in query):
        return None
    return "".join(source_to_target.get(char, char) for char in query)


def _solve_bit_manipulation_affine(prompt: str) -> str | None:
    examples = [
        (source, target)
        for source, target in re.findall(r"([01]{8}) -> ([01]{8})", prompt)
    ]
    query_match = re.search(r"output for: ([01]{8})", prompt)
    if not examples or query_match is None:
        return None

    matrix: list[list[int]] = []
    targets: list[list[int]] = [[] for _ in range(8)]
    for source, target in examples:
        source_bits = [int(char) for char in source] + [1]
        matrix.append(source_bits)
        for index, target_char in enumerate(target):
            targets[index].append(int(target_char))

    coefficients: list[list[int]] = []
    for target_bits in targets:
        solution = _solve_gf2(matrix, target_bits)
        if solution is None:
            return None
        coefficients.append(solution)

    for source, target in examples:
        source_bits = [int(char) for char in source] + [1]
        predicted = "".join(
            str(_apply_gf2_solution(solution, source_bits))
            for solution in coefficients
        )
        if predicted != target:
            return None

    query_bits = [int(char) for char in query_match.group(1)] + [1]
    return "".join(
        str(_apply_gf2_solution(solution, query_bits)) for solution in coefficients
    )


def _solve_gf2(matrix: list[list[int]], vector: list[int]) -> list[int] | None:
    rows = [row[:] + [value] for row, value in zip(matrix, vector)]
    row_count = len(rows)
    column_count = len(matrix[0]) if matrix else 0
    pivot_columns: list[int] = []
    pivot_row = 0

    for column in range(column_count):
        pivot = None
        for candidate in range(pivot_row, row_count):
            if rows[candidate][column] == 1:
                pivot = candidate
                break
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        pivot_columns.append(column)
        for candidate in range(row_count):
            if candidate == pivot_row or rows[candidate][column] == 0:
                continue
            for index in range(column, column_count + 1):
                rows[candidate][index] = (
                    rows[candidate][index] + rows[pivot_row][index]
                ) % 2
        pivot_row += 1
        if pivot_row == row_count:
            break

    for candidate in range(row_count):
        if (
            any(rows[candidate][column] == 1 for column in range(column_count))
            is False
            and rows[candidate][column_count] == 1
        ):
            return None

    solution = [0] * column_count
    for row_index, column in enumerate(pivot_columns):
        solution[column] = rows[row_index][column_count]
    return solution


def _apply_gf2_solution(solution: list[int], bits: list[int]) -> int:
    value = 0
    for coefficient, bit in zip(solution, bits):
        value = (value + (coefficient * bit)) % 2
    return value


def _format_decimal(value: Decimal, keep_two_places: bool) -> str:
    quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    text = format(quantized, "f")
    if keep_two_places:
        if "." not in text:
            text = f"{text}.00"
        decimals = text.split(".", 1)[1]
        if len(decimals) == 1:
            text = f"{text}0"
        return text

    if "." not in text:
        return f"{text}.0"
    whole, decimals = text.split(".", 1)
    if decimals == "00":
        return f"{whole}.0"
    if decimals.endswith("0"):
        return f"{whole}.{decimals[0]}"
    return text
