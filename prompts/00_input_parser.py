"""
Node 1 — Input Parser
======================
Purpose: normalize raw human input (problem text, student answer, optional
shown work, optional prior attempts) into the structured `ParsedInput`
schema every downstream node consumes. This node does NOT diagnose
anything — it only cleans and structures.

Recommended model: a small/cheap fast model (e.g. Gemini 1.5 Flash /
Gemini 2.0 Flash, or similarly cheap tier). This is a low-reasoning
structuring task; spending a frontier model's budget here is wasteful and
the ablation study (see docs/ablation.md) should confirm cheap-model
parity before locking this in.

Output schema: schemas.models.ParsedInput
"""

from schemas.models import ParsedInput  # noqa: F401  (imported for type reference)

VERSION = "v1"

SYSTEM_PROMPT_V1 = """You are the Input Parser for Bluetute, a math tutoring \
diagnostic system. Your ONLY job is to take raw, possibly messy human input \
about a student's math attempt and normalize it into structured fields. \

Rules:
- Do not evaluate correctness. Do not diagnose errors. Do not add commentary.
- If the student showed no work, return an empty list for student_reasoning_steps.
- Split shown work into discrete, atomic reasoning steps in the order the \
student wrote them. Do not merge multiple operations into one step.
- Classify the problem's domain as one of: Algebra, Functions, Geometry, \
Probability, Mixed, Other. Use "Mixed" only if the problem genuinely spans \
more than one domain; use "Other" only if none apply.
- If anything is ambiguous (e.g. illegible notation, unclear which value is \
the final answer), make the most reasonable interpretation and record what \
you resolved in `parse_notes`. Never fabricate information that was not \
given.
- Return ONLY the structured output matching the provided schema."""

USER_PROMPT_TEMPLATE_V1 = """Problem statement:
{problem_statement}

Student's final answer:
{student_answer}

Student's shown work (raw, may be empty or unstructured):
{student_reasoning_raw}

Known correct answer (may be blank if unknown):
{correct_answer}

Previous attempts on this problem (may be empty):
{previous_attempts}
"""


def build_prompt(problem_statement: str, student_answer: str,
                  student_reasoning_raw: str = "", correct_answer: str = "",
                  previous_attempts: str = "") -> dict:
    return {
        "system": SYSTEM_PROMPT_V1,
        "user": USER_PROMPT_TEMPLATE_V1.format(
            problem_statement=problem_statement,
            student_answer=student_answer,
            student_reasoning_raw=student_reasoning_raw or "(none provided)",
            correct_answer=correct_answer or "(unknown)",
            previous_attempts=previous_attempts or "(none)",
        ),
        "response_schema": "schemas.models.ParsedInput",
        "version": VERSION,
    }


# --------------------------------------------------------------------------- #
# Version history (append new entries here as prompts are revised)
# --------------------------------------------------------------------------- #
VERSION_NOTES = {
    "v1": "Initial version. Minimal constraints, relies on model's default "
          "step-splitting judgment. Watch for over-merging of steps in "
          "failure analysis; if seen, v2 should add explicit examples of "
          "atomic vs. merged steps.",
}
