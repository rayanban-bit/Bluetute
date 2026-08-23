"""
Export benchmark/cases.py to benchmark/cases.csv, and validate that every
expected_misconception_id / alt_misconception_id referenced actually
exists in the taxonomy (catches typos / drift between the two files).

Run: python3 benchmark/export_csv.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmark.cases import CASES, domain_counts, error_type_counts  # noqa: E402
from taxonomy.misconception_taxonomy import TAXONOMY_BY_ID  # noqa: E402

VALID_IDS = set(TAXONOMY_BY_ID.keys())

FIELDS = [
    "id", "domain", "problem", "correct_answer", "student_answer",
    "student_reasoning", "expected_error_type", "expected_misconception_id",
    "alt_misconception_id", "difficulty", "notes",
]


def validate() -> list[str]:
    errors = []
    seen_ids = set()
    for c in CASES:
        if c.id in seen_ids:
            errors.append(f"Duplicate case id: {c.id}")
        seen_ids.add(c.id)
        if c.expected_misconception_id not in VALID_IDS:
            errors.append(f"{c.id}: expected_misconception_id "
                           f"'{c.expected_misconception_id}' not in taxonomy")
        if c.alt_misconception_id and c.alt_misconception_id not in VALID_IDS:
            errors.append(f"{c.id}: alt_misconception_id "
                           f"'{c.alt_misconception_id}' not in taxonomy")
        if c.expected_error_type not in {"conceptual", "execution", "incomplete", "unknown"}:
            errors.append(f"{c.id}: invalid expected_error_type '{c.expected_error_type}'")
        if c.expected_error_type == "conceptual" and c.expected_misconception_id in {"execution_error", "unknown"}:
            errors.append(f"{c.id}: error_type=conceptual but misconception_id is a non-taxonomy escape hatch")
        if c.expected_error_type == "execution" and c.expected_misconception_id != "execution_error":
            errors.append(f"{c.id}: error_type=execution but misconception_id != 'execution_error'")
    return errors


def export(path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for c in CASES:
            writer.writerow({
                "id": c.id,
                "domain": c.domain,
                "problem": c.problem,
                "correct_answer": c.correct_answer,
                "student_answer": c.student_answer,
                "student_reasoning": " | ".join(c.student_reasoning),
                "expected_error_type": c.expected_error_type,
                "expected_misconception_id": c.expected_misconception_id,
                "alt_misconception_id": c.alt_misconception_id,
                "difficulty": c.difficulty,
                "notes": c.notes,
            })


if __name__ == "__main__":
    errs = validate()
    if errs:
        print("VALIDATION FAILED:")
        for e in errs:
            print(f"  - {e}")
        sys.exit(1)

    out_path = Path(__file__).resolve().parent / "cases.csv"
    export(out_path)
    print(f"Validated {len(CASES)} cases against taxonomy: OK")
    print(f"By domain: {domain_counts()}")
    print(f"By expected error_type: {error_type_counts()}")
    print(f"Exported: {out_path}")
