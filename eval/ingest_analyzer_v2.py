"""
Parses results/analyzer_v2_raw_responses.txt, scores v2 error_type
accuracy against the benchmark, AND diffs it against the already-saved v1
results (results/analyzer_results.csv) so the sign-error fix's actual
effect — and any regressions — are visible immediately.

Run: python3 eval/ingest_analyzer_v2.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError  # noqa: E402

from benchmark.cases import CASES_BY_ID  # noqa: E402
from eval.batch_common import clean_text, extract_json_array  # noqa: E402
from schemas.models import ReasoningAnalysis  # noqa: E402

RAW_PATH = Path(__file__).resolve().parent.parent / "results" / "analyzer_v2_raw_responses.txt"
V1_CSV = Path(__file__).resolve().parent.parent / "results" / "analyzer_results.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "results" / "analyzer_v2_results.csv"

ERROR_TYPES = ["conceptual", "execution", "incomplete", "unknown"]


def main():
    if not RAW_PATH.exists() or not RAW_PATH.read_text(encoding="utf-8").strip():
        print(f"No raw responses found at {RAW_PATH}.")
        print("Run prompts/RUNBOOK_reasoning_analyzer_v2.md in AI Studio, "
              "paste the JSON array reply into that file, then rerun this script.")
        sys.exit(1)

    v1_by_id = {}
    if V1_CSV.exists():
        with open(V1_CSV, encoding="utf-8") as f:
            v1_by_id = {r["case_id"]: r for r in csv.DictReader(f)}

    text = RAW_PATH.read_text(encoding="utf-8")
    try:
        items = extract_json_array(text)
    except Exception as e:
        print(f"Could not parse a JSON array from the raw responses file: {e}")
        sys.exit(1)

    by_case_id = {item.get("case_id"): item for item in items if isinstance(item, dict) and item.get("case_id")}

    rows = []
    confusion = {exp: {c: 0 for c in ERROR_TYPES} for exp in ERROR_TYPES}
    n_scored = 0
    n_correct = 0
    n_fixed = 0     # v1 wrong -> v2 right
    n_regressed = 0  # v1 right -> v2 wrong
    changes = []

    for case_id, case in CASES_BY_ID.items():
        row = {
            "case_id": case_id, "domain": case.domain,
            "expected_error_type": case.expected_error_type,
            "v1_claimed": v1_by_id.get(case_id, {}).get("claimed_error_type", ""),
            "v2_claimed": "", "v2_correct": "", "changed_v1_to_v2": "",
            "v2_evidence": "", "parse_error": "",
        }

        if case_id not in by_case_id:
            row["parse_error"] = "MISSING from v2 reply"
            rows.append(row)
            continue

        payload = dict(by_case_id[case_id])
        payload.pop("case_id", None)
        try:
            resp = ReasoningAnalysis.model_validate(payload)
        except ValidationError as e:
            row["parse_error"] = f"schema validation failed: {e}"
            rows.append(row)
            continue

        n_scored += 1
        row["v2_claimed"] = resp.error_type.value
        row["v2_evidence"] = clean_text(resp.evidence)
        is_correct = resp.error_type.value == case.expected_error_type
        row["v2_correct"] = "yes" if is_correct else "no"
        if is_correct:
            n_correct += 1
        if case.expected_error_type in confusion and resp.error_type.value in ERROR_TYPES:
            confusion[case.expected_error_type][resp.error_type.value] += 1

        v1_claimed = row["v1_claimed"]
        if v1_claimed and v1_claimed != resp.error_type.value:
            row["changed_v1_to_v2"] = "yes"
            v1_was_correct = v1_claimed == case.expected_error_type
            changes.append((case_id, v1_claimed, resp.error_type.value,
                             v1_was_correct, is_correct))
            if not v1_was_correct and is_correct:
                n_fixed += 1
            elif v1_was_correct and not is_correct:
                n_regressed += 1

        rows.append(row)

    fieldnames = list(rows[0].keys())
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Parsed {len(by_case_id)}/30 cases. Schema-valid: {n_scored}.")
    if n_scored:
        print(f"\nv2 error_type accuracy: {n_correct}/{n_scored} = {n_correct/n_scored:.1%}")
        v1_correct = sum(1 for r in v1_by_id.values() if r.get("error_type_correct") == "yes")
        if v1_by_id:
            print(f"(v1 was: {v1_correct}/{len(v1_by_id)} = {v1_correct/len(v1_by_id):.1%})")
        print(f"\nChanged v1 -> v2: {len(changes)}")
        print(f"  fixed (v1 wrong -> v2 right): {n_fixed}")
        print(f"  regressed (v1 right -> v2 wrong): {n_regressed}")
        for c in changes:
            tag = "FIXED" if (not c[3] and c[4]) else ("REGRESSED" if (c[3] and not c[4]) else "changed")
            print(f"    [{tag}] {c[0]}: {c[1]} -> {c[2]}")
        print()
        header = "expected \\ claimed".ljust(20) + "".join(c.ljust(12) for c in ERROR_TYPES)
        print(header)
        for exp in ERROR_TYPES:
            print(exp.ljust(20) + "".join(str(confusion[exp][c]).ljust(12) for c in ERROR_TYPES))
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
