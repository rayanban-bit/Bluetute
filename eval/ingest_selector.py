"""
Parses results/selector_raw_responses.txt — a single JSON array pasted
from one batched AI Studio turn for Node 6 (Diagnosis Selector) — scores
final misconception_id accuracy against the benchmark, and reports how
often the selector changed the answer relative to the Classifier alone
(the key "did the pipeline actually do something" check for the ablation
study, spec section 15).

Run: python3 eval/ingest_selector.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError  # noqa: E402

from benchmark.cases import CASES_BY_ID  # noqa: E402
from eval.batch_common import clean_text, extract_json_array  # noqa: E402
from schemas.models import FinalDiagnosis  # noqa: E402

RAW_PATH = Path(__file__).resolve().parent.parent / "results" / "selector_raw_responses.txt"
CLASSIFIER_CSV = Path(__file__).resolve().parent.parent / "results" / "classifier_results.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "results" / "selector_results.csv"


def main():
    if not RAW_PATH.exists() or not RAW_PATH.read_text(encoding="utf-8").strip():
        print(f"No raw responses found at {RAW_PATH}.")
        print("Run prompts/RUNBOOK_diagnosis_selector.md in AI Studio, paste "
              "the JSON array reply into that file, then rerun this script.")
        sys.exit(1)

    with open(CLASSIFIER_CSV, encoding="utf-8") as f:
        classifier_by_id = {r["case_id"]: r for r in csv.DictReader(f) if r.get("claimed_misconception_id")}

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
    n_changed_from_classifier = 0
    n_fixed = 0     # classifier wrong -> selector right
    n_broke = 0     # classifier right -> selector wrong
    n_suppressed = 0  # intervention_appropriate == False

    for case_id, classifier_row in classifier_by_id.items():
        case = CASES_BY_ID[case_id]
        row = {
            "case_id": case_id,
            "domain": case.domain,
            "expected_misconception_id": case.expected_misconception_id,
            "classifier_claimed_id": classifier_row["claimed_misconception_id"],
            "classifier_was_correct": classifier_row["correct"],
            "final_misconception_id": "",
            "final_error_type": "",
            "final_confidence": "",
            "correct": "",
            "changed_from_classifier": "",
            "intervention_appropriate": "",
            "evidence_summary": "",
            "parse_error": "",
        }

        if case_id not in by_case_id:
            row["parse_error"] = "MISSING: no element with this case_id in the JSON array"
            rows.append(row)
            continue

        payload = dict(by_case_id[case_id])
        payload.pop("case_id", None)
        try:
            resp = FinalDiagnosis.model_validate(payload)
        except ValidationError as e:
            row["parse_error"] = f"schema validation failed: {e}"
            rows.append(row)
            continue

        n_scored += 1
        row["final_misconception_id"] = resp.misconception_id
        row["final_error_type"] = resp.error_type.value
        row["final_confidence"] = resp.final_confidence
        row["intervention_appropriate"] = resp.intervention_appropriate
        row["evidence_summary"] = clean_text(resp.evidence_summary)

        is_correct = resp.misconception_id == case.expected_misconception_id
        row["correct"] = "yes" if is_correct else "no"
        if is_correct:
            n_correct += 1
        if not resp.intervention_appropriate:
            n_suppressed += 1

        changed = resp.misconception_id != classifier_row["claimed_misconception_id"]
        row["changed_from_classifier"] = "yes" if changed else "no"
        if changed:
            n_changed_from_classifier += 1
            was_correct_before = classifier_row["correct"] == "yes"
            if was_correct_before and not is_correct:
                n_broke += 1
            elif not was_correct_before and is_correct:
                n_fixed += 1

        rows.append(row)

    fieldnames = list(rows[0].keys())
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(classifier_by_id)
    print(f"Parsed {len(by_case_id)}/{total} cases. Schema-valid: {n_scored}.")
    if n_scored:
        print(f"\nFinal misconception_id accuracy: {n_correct}/{n_scored} = {n_correct/n_scored:.1%}")
        print(f"Changed answer vs. Classifier alone: {n_changed_from_classifier}/{n_scored}")
        print(f"  -> fixed a wrong Classifier answer: {n_fixed}")
        print(f"  -> broke a right Classifier answer: {n_broke}")
        print(f"intervention_appropriate=False (suppressed): {n_suppressed}/{n_scored}")
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
