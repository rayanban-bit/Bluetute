"""
Generates baseline/RUNBOOK.md — a copy-paste-ready set of prompts for
running the single-prompt baseline manually in Google AI Studio (no API
key wiring needed).

Run: python3 baseline/generate_runbook.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from baseline.single_prompt_baseline import SYSTEM_PROMPT_V1  # noqa: E402
from benchmark.cases import CASES  # noqa: E402
from taxonomy.misconception_taxonomy import taxonomy_prompt_block  # noqa: E402

JSON_INSTRUCTION = """

Respond with ONLY valid JSON, no markdown code fences, no extra text, in \
exactly this shape:
{
  "tutoring_response": "<the message to the student>",
  "claimed_misconception_id": "<a taxonomy id, or 'execution_error', or 'unknown'>"
}"""

SYSTEM_TEXT = SYSTEM_PROMPT_V1.format(taxonomy_block=taxonomy_prompt_block()) + JSON_INSTRUCTION


def build_user_prompt(c) -> str:
    reasoning = " | ".join(c.student_reasoning) if c.student_reasoning else "(none provided)"
    return (f"Problem: {c.problem}\n\n"
            f"Student's answer: {c.student_answer}\n\n"
            f"Student's shown work (may be empty): {reasoning}")


def main():
    lines = []
    lines.append("# Bluetute — Baseline Runbook (Google AI Studio)\n")
    lines.append(
        "How to use this file:\n\n"
        "1. Open https://aistudio.google.com, create a new chat/prompt.\n"
        "2. Pick a model (recommended: the same model you'll use for the "
        "full workflow, e.g. Gemini 2.0 Flash or 1.5 Pro — see "
        "docs/model_routing.md once written) and use it for ALL 30 cases, "
        "so the comparison against Bluetute stays apples-to-apples.\n"
        "3. Paste the **System Instructions** block below into AI Studio's "
        "'System instructions' panel ONCE. It stays the same for every case.\n"
        "4. For each case (A01...M05 below), paste ONLY that case's "
        "**User Prompt** as your chat message, in a FRESH chat/turn (not a "
        "continued conversation — each case must be independent, or later "
        "answers could leak context from earlier ones).\n"
        "5. Copy the model's raw JSON reply and append it to "
        "`results/baseline_raw_responses.txt` using the exact delimiter "
        "format shown at the bottom of this file, then run "
        "`python3 eval/ingest_baseline.py` to score it.\n"
    )
    lines.append("---\n\n## System Instructions (paste once, reuse for all 30 cases)\n")
    lines.append("```\n" + SYSTEM_TEXT + "\n```\n")
    lines.append("---\n\n## User Prompts (one per case, 30 total)\n")
    for c in CASES:
        lines.append(f"### Case {c.id}  ({c.domain}, difficulty={c.difficulty})\n")
        lines.append("```\n" + build_user_prompt(c) + "\n```\n")
    lines.append("---\n\n## Where to paste results\n")
    lines.append(
        "Append each response to `results/baseline_raw_responses.txt` like this "
        "(one block per case, in any order, blank lines between blocks OK):\n\n"
        "```\n### A01\n{\n  \"tutoring_response\": \"...\",\n"
        "  \"claimed_misconception_id\": \"algebra.sign_error\"\n}\n\n"
        "### A02\n{ ... }\n```\n\n"
        "Then run: `python3 eval/ingest_baseline.py`\n"
    )
    out = Path(__file__).resolve().parent / "RUNBOOK.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({len(CASES)} cases)")


if __name__ == "__main__":
    main()
