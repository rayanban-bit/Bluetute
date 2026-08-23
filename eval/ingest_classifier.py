"""
Parses results/classifier_raw_responses.txt — a single JSON array pasted
from one batched AI Studio turn for Node 3 (Misconception Classifier) —
validates each element, joins with the benchmark answer key, and scores
misconception_id accuracy (exact match, and exact-or-alternative for the
deliberately ambiguous cases).

Run: python3 eval/ingest_classifier.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError  # noqa: E402

from benchmark.cases import CASES_BY_ID  # noqa: E402
from eval.batch_common import clean_text, extract_json_array  # noqa: E402
from schemas.models import MisconceptionClassification  # noqa: E402
from taxonomy.misconception_taxonomy import TAXONOMY_BY_ID  # noqa: E402

RAW_PATH = Path(__file__).resolve().parent.parent / "results" / "classifier_raw_responses.txt"
OUT_PATH = Path(__file__).resolve().parent.parent / "results" / "classifier_results.csv"


def main():
    if not RAW_PATH.exists() or not RAW_PATH.read_text(encoding="utf-8").strip():
        print(f"No raw responses found at {RAW_PATH}.")
        print("Run prompts/RUNBOOK_misconception_classifier.md in AI Studio "
              "(one batched turn), paste the JSON array reply into that file, "
              "then rerun this script.")
        sys.exit(1)

    text = RAW_PATH.read_text(encoding="utf-8")
    try:
        items = extract_json_array(text)
    except Exception as e:
        print(f"Could not parse a JSON array from the raw responses file: {e}")
        sys.exit(1)

    by_case_id = {item.get("case_id"): item for item in items if isinstance(item, dict) and item.get("case_id")}

    rows = []
    n_scored = 0
    n_correct = 0
    n_correct_or_alt = 0
    n_invented_id = 0

    for case_id, item in by_case_id.items():
        if case_id not in CASES_BY_ID:
            continue  # stray/unknown case id in the reply — ignore rather than crash
        case = CASES_BY_ID[case_id]
        row = {
            "case_id": case_id,
            "domain": case.domain,
            "expected_misconception_id": case.expected_misconception_id,
            "alt_misconception_id": case.alt_misconception_id,
            "claimed_misconception_id": "",
            "label": "",
            "correct": "",
            "correct_or_alt": "",
            "id_in_taxonomy": "",
            "confidence": "",
            "evidence": "",
            "alternative_candidate_ids": "",
            "parse_error": "",
        }

        payload = dict(item)
        payload.pop("case_id", None)
        try:
            resp = MisconceptionClassification.model_validate(payload)
        except ValidationError as e:
            row["parse_error"] = f"schema validation failed: {e}"
            rows.append(row)
            continue

        row["claimed_misconception_id"] = resp.misconception_id
        row["label"] = resp.label
        row["confidence"] = resp.confidence
        row["evidence"] = clean_text(resp.evidence)
        row["alternative_candidate_ids"] = "|".join(resp.alternative_candidate_ids)

        valid_id = resp.misconception_id in TAXONOMY_BY_ID or resp.misconception_id == "unknown"
        row["id_in_taxonomy"] = "yes" if valid_id else "no — INVENTED ID"
        if not valid_id:
            n_invented_id += 1

        n_scored += 1
        is_correct = resp.misconception_id == case.expected_misconception_id
        is_correct_or_alt = is_correct or (
            case.alt_misconception_id and resp.misconception_id == case.alt_misconception_id
        )
        row["correct"] = "yes" if is_correct else "no"
        row["correct_or_alt"] = "yes" if is_correct_or_alt else "no"
        if is_correct:
            n_correct += 1
        if is_correct_or_alt:
            n_correct_or_alt += 1

        rows.append(row)

    for case_id, case in CASES_BY_ID.items():
        if case.expected_error_type != "conceptual" or case_id in by_case_id:
            continue
        rows.append({
            "case_id": case_id, "domain": case.domain,
            "expected_misconception_id": case.expected_misconception_id,
            "alt_misconception_id": case.alt_misconception_id,
            "claimed_misconception_id": "", "correct": "", "correct_or_alt": "",
            "id_in_taxonomy": "", "confidence": "", "evidence": "",
            "parse_error": "MISSING: expected conceptual case not present in classifier reply",
        })

    if not rows:
        print("No scoreable rows produced — check the input file.")
        sys.exit(1)

    fieldnames = list(rows[0].keys())
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Scored {n_scored} classified cases.")
    if n_scored:
        print(f"Exact-match accuracy: {n_correct}/{n_scored} = {n_correct/n_scored:.1%}")
        print(f"Exact-or-alternative accuracy: {n_correct_or_alt}/{n_scored} = {n_correct_or_alt/n_scored:.1%}")
        print(f"Invented (non-taxonomy) ids: {n_invented_id}/{n_scored}")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
