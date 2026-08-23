"""
Parses results/analyzer_raw_responses.txt — a SINGLE JSON array (one
element per case, each with a "case_id" field) pasted from one batched
Google AI Studio turn — validates each element against
schemas.models.ReasoningAnalysis, joins with the benchmark answer key, and
scores error_type accuracy (the core measurable claim from spec section 2)
plus a confusion matrix.

Run: python3 eval/ingest_analyzer.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError  # noqa: E402

from benchmark.cases import CASES_BY_ID  # noqa: E402
from eval.batch_common import clean_text, extract_json_array  # noqa: E402
from schemas.models import ReasoningAnalysis  # noqa: E402

RAW_PATH = Path(__file__).resolve().parent.parent / "results" / "analyzer_raw_responses.txt"
OUT_PATH = Path(__file__).resolve().parent.parent / "results" / "analyzer_results.csv"

ERROR_TYPES = ["conceptual", "execution", "incomplete", "unknown"]


def main():
    if not RAW_PATH.exists() or not RAW_PATH.read_text(encoding="utf-8").strip():
        print(f"No raw responses found at {RAW_PATH}.")
        print("Run prompts/RUNBOOK_reasoning_analyzer.md in Google AI Studio "
              "(one batched turn), paste the JSON array reply into that file, "
              "then rerun this script.")
        sys.exit(1)

    text = RAW_PATH.read_text(encoding="utf-8")
    try:
        items = extract_json_array(text)
    except (ValueError, Exception) as e:
        print(f"Could not parse a JSON array from the raw responses file: {e}")
        sys.exit(1)

    by_case_id = {}
    for item in items:
        cid = item.get("case_id") if isinstance(item, dict) else None
        if cid:
            by_case_id[cid] = item

    rows = []
    confusion = {exp: {c: 0 for c in ERROR_TYPES} for exp in ERROR_TYPES}
    n_scored = 0
    n_correct = 0
    n_schema_valid = 0

    for case_id, case in CASES_BY_ID.items():
        row = {
            "case_id": case_id,
            "domain": case.domain,
            "expected_error_type": case.expected_error_type,
            "claimed_error_type": "",
            "error_type_correct": "",
            "first_invalid_step_index": "",
            "confidence": "",
            "evidence": "",
            "schema_valid": "",
            "parse_error": "",
        }

        if case_id not in by_case_id:
            row["parse_error"] = "MISSING: no element with this case_id in the JSON array"
            rows.append(row)
            continue

        item = dict(by_case_id[case_id])
        item.pop("case_id", None)

        try:
            resp = ReasoningAnalysis.model_validate(item)
            n_schema_valid += 1
        except ValidationError as e:
            row["parse_error"] = f"schema validation failed: {e}"
            rows.append(row)
            continue

        row["schema_valid"] = "yes"
        row["claimed_error_type"] = resp.error_type.value
        row["first_invalid_step_index"] = (
            "" if resp.first_invalid_step_index is None else resp.first_invalid_step_index
        )
        row["confidence"] = resp.confidence
        row["evidence"] = clean_text(resp.evidence)

        n_scored += 1
        is_correct = resp.error_type.value == case.expected_error_type
        row["error_type_correct"] = "yes" if is_correct else "no"
        if is_correct:
            n_correct += 1
        if case.expected_error_type in confusion and resp.error_type.value in ERROR_TYPES:
            confusion[case.expected_error_type][resp.error_type.value] += 1

        rows.append(row)

    fieldnames = list(rows[0].keys())
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(CASES_BY_ID)
    print(f"Parsed {len(by_case_id)}/{total} cases from the JSON array.")
    print(f"Schema-valid: {n_schema_valid}/{len(by_case_id) or 1}")
    if n_scored:
        print(f"error_type accuracy: {n_correct}/{n_scored} = {n_correct/n_scored:.1%}\n")
        header = "expected \\ claimed".ljust(20) + "".join(c.ljust(12) for c in ERROR_TYPES)
        print(header)
        for exp in ERROR_TYPES:
            print(exp.ljust(20) + "".join(str(confusion[exp][c]).ljust(12) for c in ERROR_TYPES))
    missing = [cid for cid in CASES_BY_ID if cid not in by_case_id]
    if missing:
        print(f"\nMissing case_ids (model dropped them or truncated output): {missing}")
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
