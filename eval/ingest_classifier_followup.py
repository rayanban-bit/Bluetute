"""
Scores results/classifier_followup_raw_responses.txt (the 3 newly-
conceptual sign-error cases) and merges them into a combined
results/classifier_results_v2.csv = original 20 classifier_results.csv
rows + these 3 new ones, so the full-pipeline recount has all 23.

Run: python3 eval/ingest_classifier_followup.py
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

RAW_PATH = Path(__file__).resolve().parent.parent / "results" / "classifier_followup_raw_responses.txt"
ORIGINAL_CSV = Path(__file__).resolve().parent.parent / "results" / "classifier_results.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "results" / "classifier_results_v2.csv"


def main():
    if not RAW_PATH.exists() or not RAW_PATH.read_text(encoding="utf-8").strip():
        print(f"No raw responses found at {RAW_PATH}.")
        sys.exit(1)

    with open(ORIGINAL_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())

    text = RAW_PATH.read_text(encoding="utf-8")
    items = extract_json_array(text)
    new_ids = {item.get("case_id") for item in items if isinstance(item, dict) and item.get("case_id")}

    # Drop any existing row (e.g. an earlier "MISSING" placeholder) for a
    # case_id we're about to add a real result for, so the merge doesn't
    # duplicate that case.
    rows = [r for r in rows if r.get("case_id") not in new_ids]

    for item in items:
        cid = item.get("case_id")
        if not cid or cid not in CASES_BY_ID:
            continue
        case = CASES_BY_ID[cid]
        payload = dict(item)
        payload.pop("case_id", None)
        row = {k: "" for k in fieldnames}
        row["case_id"] = cid
        row["domain"] = case.domain
        row["expected_misconception_id"] = case.expected_misconception_id
        row["alt_misconception_id"] = case.alt_misconception_id
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
        is_correct = resp.misconception_id == case.expected_misconception_id
        row["correct"] = "yes" if is_correct else "no"
        row["correct_or_alt"] = "yes" if (is_correct or (
            case.alt_misconception_id and resp.misconception_id == case.alt_misconception_id)) else "no"
        rows.append(row)
        print(f"{cid}: claimed={resp.misconception_id} expected={case.expected_misconception_id} "
              f"-> {'CORRECT' if is_correct else 'WRONG'}")

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    n_correct = sum(1 for r in rows if r.get("correct") == "yes")
    print(f"\nCombined classifier_results_v2.csv: {len(rows)} cases, {n_correct} correct "
          f"({n_correct/len(rows):.1%})")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
