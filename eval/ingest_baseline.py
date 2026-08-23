"""
Parses results/baseline_raw_responses.txt (raw JSON pasted from Google AI
Studio, one block per case delimited by "### <case_id>"), validates each
against schemas.models.BaselineResponse, joins with the benchmark answer
key, scores diagnosis accuracy, and writes results/baseline_results.csv.

Run: python3 eval/ingest_baseline.py
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError  # noqa: E402

from benchmark.cases import CASES_BY_ID  # noqa: E402
from schemas.models import BaselineResponse  # noqa: E402

RAW_PATH = Path(__file__).resolve().parent.parent / "results" / "baseline_raw_responses.txt"
OUT_PATH = Path(__file__).resolve().parent.parent / "results" / "baseline_results.csv"

BLOCK_RE = re.compile(r"^#*\s*###\s*([A-Z]\d+)\s*$", re.MULTILINE)


def parse_blocks(text: str) -> dict[str, str]:
    """Split the raw file into {case_id: raw_json_text} blocks."""
    positions = [(m.group(1), m.end()) for m in BLOCK_RE.finditer(text)]
    blocks = {}
    for i, (case_id, start) in enumerate(positions):
        end = positions[i + 1][1] - len(f"### {positions[i+1][0]}") if i + 1 < len(positions) else len(text)
        # Simpler and more robust: find next "### " after start, or end of text.
        next_match = BLOCK_RE.search(text, start)
        end = next_match.start() if next_match else len(text)
        blocks[case_id] = text[start:end].strip()
    return blocks


def extract_json(raw: str) -> str:
    """
    Isolate the JSON object inside a pasted block, tolerating markdown code
    fences, stray comment characters, and leading/trailing prose the user
    may have left in accidentally. Finds the outermost {...} by brace
    counting rather than assuming the block is pure JSON.
    """
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()

    start = raw.find("{")
    if start == -1:
        return raw  # let json.loads report a clear error

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(raw)):
        ch = raw[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return raw[start:i + 1]
    return raw[start:]  # unbalanced — let json.loads report a clear error


def loads_lenient(raw_json: str):
    """
    Parse JSON, falling back to strict=False so raw control characters
    (e.g. literal newlines pasted from rendered math) inside string values
    don't hard-fail the whole case.
    """
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError:
        return json.loads(raw_json, strict=False)


def clean_text(s: str) -> str:
    """Collapse runs of whitespace/newlines into single spaces for the CSV."""
    return re.sub(r"\s+", " ", s).strip() if isinstance(s, str) else s


def main():
    if not RAW_PATH.exists():
        print(f"No raw responses file found at {RAW_PATH}.")
        print("Run the RUNBOOK.md cases in Google AI Studio first, then paste "
              "results into that file (see RUNBOOK.md for the exact format).")
        sys.exit(1)

    text = RAW_PATH.read_text(encoding="utf-8")
    blocks = parse_blocks(text)

    if not blocks:
        print("No '### <case_id>' blocks found in the raw responses file. "
              "Check the delimiter format described in RUNBOOK.md.")
        sys.exit(1)

    rows = []
    n_valid_json = 0
    n_valid_schema = 0
    n_correct = 0
    n_scored = 0

    for case_id, case in CASES_BY_ID.items():
        row = {
            "case_id": case_id,
            "domain": case.domain,
            "expected_error_type": case.expected_error_type,
            "expected_misconception_id": case.expected_misconception_id,
            "alt_misconception_id": case.alt_misconception_id,
            "claimed_misconception_id": "",
            "correct": "",
            "correct_or_alt": "",
            "json_valid": "",
            "schema_valid": "",
            "tutoring_response": "",
            "parse_error": "",
        }

        if case_id not in blocks:
            row["parse_error"] = "MISSING: no block found in raw responses file"
            rows.append(row)
            continue

        raw_json = extract_json(blocks[case_id])
        try:
            parsed = loads_lenient(raw_json)
            n_valid_json += 1
        except json.JSONDecodeError as e:
            row["parse_error"] = f"invalid JSON: {e}"
            rows.append(row)
            continue

        try:
            resp = BaselineResponse.model_validate(parsed)
            n_valid_schema += 1
        except ValidationError as e:
            row["json_valid"] = "yes"
            row["parse_error"] = f"schema validation failed: {e}"
            rows.append(row)
            continue

        row["json_valid"] = "yes"
        row["schema_valid"] = "yes"
        row["tutoring_response"] = clean_text(resp.tutoring_response)
        row["claimed_misconception_id"] = resp.claimed_misconception_id or ""

        n_scored += 1
        is_correct = resp.claimed_misconception_id == case.expected_misconception_id
        is_correct_or_alt = is_correct or (
            case.alt_misconception_id and resp.claimed_misconception_id == case.alt_misconception_id
        )
        row["correct"] = "yes" if is_correct else "no"
        row["correct_or_alt"] = "yes" if is_correct_or_alt else "no"
        if is_correct:
            n_correct += 1

        rows.append(row)

    fieldnames = list(rows[0].keys())
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(CASES_BY_ID)
    print(f"Parsed {len(blocks)} blocks out of {total} expected cases.")
    print(f"Valid JSON: {n_valid_json}/{len(blocks)}")
    print(f"Valid schema: {n_valid_schema}/{len(blocks)}")
    if n_scored:
        print(f"Diagnosis accuracy (exact match): {n_correct}/{n_scored} = {n_correct/n_scored:.1%}")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
