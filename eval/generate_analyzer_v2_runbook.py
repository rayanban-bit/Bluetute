"""
Generates prompts/RUNBOOK_reasoning_analyzer_v2.md — the v2 Reasoning
Analyzer prompt (sign-error fix, see VERSION_NOTES in
prompts/01_reasoning_analyzer.py) run on all 30 benchmark cases, so v1 vs
v2 can be compared for BOTH the fix (does it flip A01/A07/M02 to
conceptual?) and regressions (does anything else change for the worse?).

This is the "test 3 prompt versions" step (spec section 22, step 5) —
v1 and v2 are the first two; a v3 will follow if v2's results warrant it.

Run: python3 eval/generate_analyzer_v2_runbook.py
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

SYSTEM_TEXT = node.SYSTEM_PROMPT_V2 + batch_json_instruction(SCHEMA_HINT)


def main():
    case_blocks = []
    for c in CASES:
        user = node.USER_PROMPT_TEMPLATE_V1.format(
            domain=c.domain,
            problem_statement=c.problem,
            correct_answer=c.correct_answer,
            student_answer=c.student_answer,
            numbered_steps=node._number_steps(c.student_reasoning),
        )
        case_blocks.append((c.id, user))

    user_message = build_batch_user_message(
        "Analyze the following student attempts. There are 30 independent cases.",
        case_blocks,
    )

    lines = []
    lines.append("# Bluetute — Reasoning Analyzer Runbook v2 (sign-error fix, BATCHED)\n")
    lines.append(
        "This is prompt v2 (see VERSION_NOTES in prompts/01_reasoning_analyzer.py) "
        "run on all 30 cases — same benchmark as v1, so results are directly "
        "comparable. Expected: A01, A07, M02 should flip from 'execution' to "
        "'conceptual'; everything else should stay the same (no regressions).\n\n"
        "1. New chat in AI Studio, SAME model used for v1 (fair comparison).\n"
        "2. Paste **System Instructions** once.\n"
        "3. Paste the **Batch User Message** once.\n"
        "4. Save the JSON array reply into `results/analyzer_v2_raw_responses.txt`.\n"
        "5. Run `python3 eval/ingest_analyzer_v2.py` — it scores v2 AND diffs "
        "it against the saved v1 results automatically.\n"
    )
    lines.append("---\n\n## System Instructions (paste once)\n")
    lines.append("```\n" + SYSTEM_TEXT + "\n```\n")
    lines.append("---\n\n## Batch User Message (30 cases)\n")
    lines.append("```\n" + user_message + "\n```\n")
    out = ROOT / "prompts" / "RUNBOOK_reasoning_analyzer_v2.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({len(CASES)} cases, batched, prompt v2)")


if __name__ == "__main__":
    main()
