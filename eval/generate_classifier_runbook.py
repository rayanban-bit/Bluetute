"""
Generates prompts/RUNBOOK_misconception_classifier.md — ONE batched prompt
for Node 3 (Misconception Classifier), chained automatically from the real
Reasoning Analyzer results (results/analyzer_results.csv).

Per spec, Node 3 is only meaningful when Node 2 found error_type ==
"conceptual" — execution/incomplete/unknown cases skip classification
entirely (see prompts/02_misconception_classifier.py docstring). So this
script only includes cases where the Analyzer actually claimed
"conceptual", using the ANALYZER'S OWN evidence/confidence as input (not
the benchmark's ground truth) — this is what makes it a real end-to-end
chain instead of a component test in isolation.

Requires results/analyzer_results.csv to exist first (run
prompts/RUNBOOK_reasoning_analyzer.md + eval/ingest_analyzer.py).

Run: python3 eval/generate_classifier_runbook.py
"""

import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmark.cases import CASES_BY_ID  # noqa: E402
from eval.batch_common import batch_json_instruction, build_batch_user_message  # noqa: E402

ANALYZER_CSV = ROOT / "results" / "analyzer_results.csv"


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
  "case_id": "<echo the case id, e.g. 'A01'>",
  "misconception_id": "<must exactly match an id from the taxonomy above, or 'unknown'>",
  "label": "<the taxonomy label for that id>",
  "domain": "<Algebra|Functions|Geometry|Probability>",
  "evidence": "<specific reasoning text supporting this classification>",
  "confidence": <float 0.0-1.0>,
  "alternative_candidate_ids": ["<other plausible taxonomy ids, if any>"]
}"""


def main():
    if not ANALYZER_CSV.exists():
        print(f"{ANALYZER_CSV} not found.")
        print("Run prompts/RUNBOOK_reasoning_analyzer.md in AI Studio and "
              "`python3 eval/ingest_analyzer.py` first — the Classifier "
              "runbook is generated FROM the Analyzer's real output so the "
              "chain is genuine, not a component test in isolation.")
        sys.exit(1)

    node = _load_node("02_misconception_classifier.py")

    with open(ANALYZER_CSV, encoding="utf-8") as f:
        analyzer_rows = {r["case_id"]: r for r in csv.DictReader(f)}

    if not analyzer_rows:
        print(f"{ANALYZER_CSV} is empty — nothing to chain from.")
        sys.exit(1)

    conceptual_rows = [
        r for r in analyzer_rows.values()
        if r.get("schema_valid") == "yes" and r.get("claimed_error_type") == "conceptual"
    ]
    skipped = len(analyzer_rows) - len(conceptual_rows)

    if not conceptual_rows:
        print("No cases with error_type == 'conceptual' found in analyzer_results.csv "
              "(either the Analyzer hasn't been scored yet, or genuinely found no "
              "conceptual errors). Nothing to classify.")
        sys.exit(1)

    case_blocks = []
    for r in conceptual_rows:
        case = CASES_BY_ID[r["case_id"]]
        prompt = node.build_prompt(
            domain=case.domain,
            problem_statement=case.problem,
            numbered_steps=_number_steps(case.student_reasoning),
            first_invalid_step_index=r.get("first_invalid_step_index") or "null",
            error_type=r.get("claimed_error_type"),
            analyzer_evidence=r.get("evidence", ""),
            analyzer_confidence=r.get("confidence", ""),
        )
        case_blocks.append((case.id, prompt["user"]))

    user_message = build_batch_user_message(
        f"Classify the misconception for the following student attempts. "
        f"There are {len(case_blocks)} independent cases, each already confirmed "
        f"by the Reasoning Analyzer to be a CONCEPTUAL error (not an execution slip).",
        case_blocks,
    )

    system_text = node.SYSTEM_PROMPT_V1.format(
        taxonomy_block=__import__(
            "taxonomy.misconception_taxonomy", fromlist=["taxonomy_prompt_block"]
        ).taxonomy_prompt_block()
    ) + batch_json_instruction(SCHEMA_HINT)

    lines = []
    lines.append(f"# Bluetute — Misconception Classifier Runbook (BATCHED, prompt {node.VERSION})\n")
    lines.append(
        f"Chained from real Analyzer output: {len(conceptual_rows)} of "
        f"{len(analyzer_rows)} cases were claimed 'conceptual' by the Analyzer "
        f"({skipped} were execution/incomplete/unknown and are correctly excluded "
        "here — Node 3 only runs on conceptual errors).\n\n"
        "1. New chat in AI Studio, same model as before.\n"
        "2. Paste **System Instructions** once.\n"
        "3. Paste the **Batch User Message** once.\n"
        "4. Save the JSON array reply into `results/classifier_raw_responses.txt`.\n"
        "5. Run `python3 eval/ingest_classifier.py`.\n"
    )
    lines.append("---\n\n## System Instructions (paste once)\n")
    lines.append("```\n" + system_text + "\n```\n")
    lines.append(f"---\n\n## Batch User Message ({len(case_blocks)} cases)\n")
    lines.append("```\n" + user_message + "\n```\n")
    out = ROOT / "prompts" / "RUNBOOK_misconception_classifier.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({len(case_blocks)} conceptual cases, batched)")


if __name__ == "__main__":
    main()
