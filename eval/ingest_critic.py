"""
Parses results/critic_raw_responses.txt — a single JSON array pasted from
one batched AI Studio turn for Node 5 (Adversarial Critic) — validates
each element, joins with the Classifier's results and the benchmark
answer key, and reports:
  - diagnosis_survives rate (spec section 5 / prompts/03 VERSION_NOTES:
    a rate near 0% or 100% signals the critic isn't doing real work)
  - for cases where the Classifier was WRONG, whether the critic's
    alternative_hypotheses actually surfaced the correct id (the critic's
    core job) and/or correctly flagged diagnosis_survives=False
  - for cases where the Classifier was RIGHT, whether the critic wrongly
    overturned a correct diagnosis (false-alarm rate)

Run: python3 eval/ingest_critic.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError  # noqa: E402

from benchmark.cases import CASES_BY_ID  # noqa: E402
from eval.batch_common import clean_text, extract_json_array  # noqa: E402
from schemas.models import CriticReview  # noqa: E402

RAW_PATH = Path(__file__).resolve().parent.parent / "results" / "critic_raw_responses.txt"
CLASSIFIER_CSV = Path(__file__).resolve().parent.parent / "results" / "classifier_results.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "results" / "critic_results.csv"


def main():
    if not RAW_PATH.exists() or not RAW_PATH.read_text(encoding="utf-8").strip():
        print(f"No raw responses found at {RAW_PATH}.")
        print("Run prompts/RUNBOOK_adversarial_critic.md in AI Studio, paste "
              "the JSON array reply into that file, then rerun this script.")
        sys.exit(1)

    if not CLASSIFIER_CSV.exists():
        print(f"{CLASSIFIER_CSV} not found — run the Classifier step first.")
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
    n_survives = 0
    n_classifier_wrong = 0
    n_critic_caught_wrong = 0   # classifier wrong AND (survives=False OR correct id in alternatives)
    n_classifier_right = 0
    n_critic_overturned_right = 0  # classifier right BUT critic said survives=False

    for case_id, classifier_row in classifier_by_id.items():
        case = CASES_BY_ID[case_id]
        row = {
            "case_id": case_id,
            "domain": case.domain,
            "expected_misconception_id": case.expected_misconception_id,
            "classifier_claimed_id": classifier_row["claimed_misconception_id"],
            "classifier_was_correct": classifier_row["correct"],
            "diagnosis_survives": "",
            "confidence_adjustment": "",
            "alternative_ids_proposed": "",
            "surfaced_correct_alt": "",
            "attempted_rebuttal": "",
            "parse_error": "",
        }

        if case_id not in by_case_id:
            row["parse_error"] = "MISSING: no element with this case_id in the JSON array"
            rows.append(row)
            continue

        payload = dict(by_case_id[case_id])
        payload.pop("case_id", None)
        try:
            resp = CriticReview.model_validate(payload)
        except ValidationError as e:
            row["parse_error"] = f"schema validation failed: {e}"
            rows.append(row)
            continue

        n_scored += 1
        row["diagnosis_survives"] = resp.diagnosis_survives
        row["confidence_adjustment"] = resp.confidence_adjustment
        row["attempted_rebuttal"] = clean_text(resp.attempted_rebuttal)
        alt_ids = [h.misconception_id for h in resp.alternative_hypotheses]
        row["alternative_ids_proposed"] = "|".join(alt_ids)
        surfaced_correct = case.expected_misconception_id in alt_ids
        row["surfaced_correct_alt"] = "yes" if surfaced_correct else "no"

        if resp.diagnosis_survives:
            n_survives += 1

        was_correct = classifier_row["correct"] == "yes"
        if was_correct:
            n_classifier_right += 1
            if not resp.diagnosis_survives:
                n_critic_overturned_right += 1
        else:
            n_classifier_wrong += 1
            if surfaced_correct or not resp.diagnosis_survives:
                n_critic_caught_wrong += 1

        rows.append(row)

    fieldnames = list(rows[0].keys())
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(classifier_by_id)
    print(f"Parsed {len(by_case_id)}/{total} cases from the JSON array. Schema-valid: {n_scored}.")
    if n_scored:
        print(f"\ndiagnosis_survives rate: {n_survives}/{n_scored} = {n_survives/n_scored:.1%} "
              f"(spec flags this as a problem if near 0% or 100%)")
        if n_classifier_wrong:
            print(f"Of {n_classifier_wrong} cases the Classifier got WRONG: critic caught "
                  f"{n_critic_caught_wrong}/{n_classifier_wrong} "
                  f"({n_critic_caught_wrong/n_classifier_wrong:.1%}) via survives=False or "
                  f"a correct alternative hypothesis")
        if n_classifier_right:
            print(f"Of {n_classifier_right} cases the Classifier got RIGHT: critic wrongly "
                  f"overturned {n_critic_overturned_right}/{n_classifier_right} "
                  f"({n_critic_overturned_right/n_classifier_right:.1%}) — false-alarm rate")
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
