"""
Generates prompts/RUNBOOK_classifier_followup.md — classifies ONLY the
cases newly flagged 'conceptual' by the v2 Reasoning Analyzer that
weren't already classified under v1 (A01, A07, M02 — the sign-error
fixes). Small, targeted follow-up rather than re-running all 23.

Run: python3 eval/generate_classifier_followup.py
"""

import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmark.cases import CASES_BY_ID  # noqa: E402
from eval.batch_common import batch_json_instruction, build_batch_user_message  # noqa: E402

V2_CSV = ROOT / "results" / "analyzer_v2_results.csv"


def _load_node(module_filename: str):
    path = ROOT / "prompts" / module_filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _number_steps(steps: list[str]) -> str:
    if not steps:
        return "(no work shown)"
    return "\n".join(f"[{i}] {s}" for i, s in enumerate(steps))


SCHEMA_HINT = """{
  "case_id": "<echo the case id>",
  "misconception_id": "<must exactly match an id from the taxonomy above, or 'unknown'>",
  "label": "<the taxonomy label for that id>",
  "domain": "<Algebra|Functions|Geometry|Probability>",
  "evidence": "<specific reasoning text supporting this classification>",
  "confidence": <float 0.0-1.0>,
  "alternative_candidate_ids": ["<other plausible taxonomy ids, if any>"]
}"""


def main():
    if not V2_CSV.exists():
        print(f"{V2_CSV} not found — run the v2 Analyzer step first.")
        sys.exit(1)

    node = _load_node("02_misconception_classifier.py")

    with open(V2_CSV, encoding="utf-8") as f:
        v2_rows = {r["case_id"]: r for r in csv.DictReader(f)}

    newly_conceptual = [
        r for r in v2_rows.values()
        if r.get("changed_v1_to_v2") == "yes" and r.get("v2_claimed") == "conceptual"
    ]

    if not newly_conceptual:
        print("No newly-conceptual cases found (nothing changed from v1 to v2).")
        sys.exit(1)

    case_blocks = []
    for r in newly_conceptual:
        case = CASES_BY_ID[r["case_id"]]
        prompt = node.build_prompt(
            domain=case.domain,
            problem_statement=case.problem,
            numbered_steps=_number_steps(case.student_reasoning),
            first_invalid_step_index="see evidence",
            error_type="conceptual",
            analyzer_evidence=r.get("v2_evidence", ""),
            analyzer_confidence="1.0",
        )
        case_blocks.append((case.id, prompt["user"]))

    user_message = build_batch_user_message(
        f"Classify the misconception for the following student attempts. "
        f"There are {len(case_blocks)} independent cases, each confirmed by "
        f"the Reasoning Analyzer (v2) to be a CONCEPTUAL sign-handling error.",
        case_blocks,
    )
    system_text = node.SYSTEM_PROMPT_V1.format(
        taxonomy_block=__import__(
            "taxonomy.misconception_taxonomy", fromlist=["taxonomy_prompt_block"]
        ).taxonomy_prompt_block()
    ) + batch_json_instruction(SCHEMA_HINT)

    lines = []
    lines.append(f"# Bluetute — Classifier Follow-up Runbook ({len(case_blocks)} newly-conceptual cases from v2 Analyzer)\n")
    lines.append(
        f"Cases: {', '.join(c[0] for c in case_blocks)} — these flipped from "
        "'execution' (v1) to 'conceptual' (v2) after the sign-error prompt fix, "
        "and were never classified before.\n\n"
        "1. New chat in AI Studio.\n2. Paste System Instructions once.\n"
        "3. Paste Batch User Message once.\n"
        "4. Save reply into `results/classifier_followup_raw_responses.txt`.\n"
        "5. Run `python3 eval/ingest_classifier_followup.py`.\n"
    )
    lines.append("---\n\n## System Instructions (paste once)\n")
    lines.append("```\n" + system_text + "\n```\n")
    lines.append(f"---\n\n## Batch User Message ({len(case_blocks)} cases)\n")
    lines.append("```\n" + user_message + "\n```\n")
    out = ROOT / "prompts" / "RUNBOOK_classifier_followup.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({len(case_blocks)} cases: {[c[0] for c in case_blocks]})")


if __name__ == "__main__":
    main()
