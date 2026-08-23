"""
Generates prompts/RUNBOOK_reasoning_analyzer.md — ONE batched prompt that
runs all 30 benchmark cases through Node 2 (Reasoning Analyzer) in a
single Google AI Studio turn (see eval/batch_common.py for why batching).

Run: python3 eval/generate_analyzer_runbook.py
"""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmark.cases import CASES  # noqa: E402
from eval.batch_common import batch_json_instruction, build_batch_user_message  # noqa: E402


def _load_node(module_filename: str):
    path = ROOT / "prompts" / module_filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


node = _load_node("01_reasoning_analyzer.py")

SCHEMA_HINT = """{
  "case_id": "<echo the case id, e.g. 'A01'>",
  "step_judgments": [{"step_index": 0, "step_text": "...", "is_valid": true, "note": "..."}],
  "first_invalid_step_index": <int or null>,
  "error_type": "<one of: conceptual, execution, incomplete, unknown>",
  "evidence": "<concise, specific, verifiable justification>",
  "confidence": <float 0.0-1.0>
}"""

SYSTEM_TEXT = node.SYSTEM_PROMPT_V1 + batch_json_instruction(SCHEMA_HINT)


def main():
    case_blocks = []
    for c in CASES:
        prompt = node.build_prompt(
            domain=c.domain,
            problem_statement=c.problem,
            correct_answer=c.correct_answer,
            student_answer=c.student_answer,
            student_reasoning_steps=c.student_reasoning,
        )
        case_blocks.append((c.id, prompt["user"]))

    user_message = build_batch_user_message(
        "Analyze the following student attempts. There are 30 independent cases.",
        case_blocks,
    )

    lines = []
    lines.append(f"# Bluetute — Reasoning Analyzer Runbook (BATCHED, prompt {node.VERSION})\n")
    lines.append(
        "This runs all 30 cases in ONE AI Studio turn instead of 30 separate ones.\n\n"
        "1. New chat in https://aistudio.google.com, same model used for the baseline.\n"
        "2. Paste **System Instructions** into the system instructions panel.\n"
        "3. Paste the **Batch User Message** (all 30 cases) as your one chat message.\n"
        "4. Copy the ENTIRE JSON array reply into "
        "`results/analyzer_raw_responses.txt` (overwrite the whole file with just "
        "that array — no need for the old `### case_id` delimiters anymore).\n"
        "5. Run `python3 eval/ingest_analyzer.py`.\n\n"
        "If the model truncates the array (30 cases can be a lot of output), ask it "
        "to continue from the last complete case_id in the same chat and append the "
        "rest — the ingestion script tolerates a single array split across multiple "
        "pasted fragments as long as each fragment parses as valid JSON on its own "
        "(wrap each fragment's cases in [ ] if you split it).\n"
    )
    lines.append("---\n\n## System Instructions (paste once)\n")
    lines.append("```\n" + SYSTEM_TEXT + "\n```\n")
    lines.append("---\n\n## Batch User Message (paste once, all 30 cases)\n")
    lines.append("```\n" + user_message + "\n```\n")
    out = ROOT / "prompts" / "RUNBOOK_reasoning_analyzer.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({len(CASES)} cases, batched)")


if __name__ == "__main__":
    main()
