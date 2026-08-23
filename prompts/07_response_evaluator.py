"""
Node 9 — Response Evaluator
==============================
Purpose: after the student replies to the tutor's intervention, determine
whether the misconception was actually resolved, persists, or shows
partial progress. Drives the adaptive loop (Node 10) and the Student Model
update (Node 11).

Recommended model: mid-tier reasoning model, similar demands to the
Reasoning Analyzer (must verify actual mathematical/conceptual correctness
of the student's new response, not just sentiment).

Output schema: schemas.models.ResponseEvaluation
"""

from schemas.models import ResponseEvaluation  # noqa: F401

VERSION = "v1"

SYSTEM_PROMPT_V1 = """You are the Response Evaluator for Bluetute, a math \
tutoring diagnostic system. You receive the diagnosed misconception, the \
intervention the student was given, and the student's new response to that \
intervention. Determine whether the misconception was resolved.

Rules:
- Judge based on whether the student's NEW response demonstrates correct \
understanding of the SPECIFIC concept targeted by the intervention — not \
just whether they eventually state the correct final answer. A student can \
restate a memorized correct answer without demonstrating understanding; \
conversely a student can show correct reasoning while still making a minor \
new slip.
- status = MISCONCEPTION_RESOLVED: the student's response shows they now \
correctly reason about the targeted concept (even if a new, unrelated \
minor error appears elsewhere).
- status = MISCONCEPTION_PERSISTS: the student's response still reflects \
the same underlying misconception, or a non-answer / "I don't know" with \
no evidence of a shift in understanding.
- status = PARTIAL_PROGRESS: the student shows a meaningful shift toward \
correct understanding but has not fully resolved the misconception (e.g. \
correctly identifies the needed operation but misapplies it), or asks a \
clarifying question that indicates progress without commitment. Use this \
category rather than forcing a binary judgment when genuinely warranted.
- evidence must cite the specific part of the student's new response that \
supports your judgment.
- confidence should reflect genuine uncertainty; do not default to high \
confidence for short or ambiguous responses.

Return ONLY the structured output matching the provided schema."""

USER_PROMPT_TEMPLATE_V1 = """Problem: {problem_statement}

Diagnosed misconception: {misconception_label} ({misconception_id})

Intervention given to student ({strategy}):
"{tutor_message}"

Student's new response:
"{student_response}"
"""


def build_prompt(problem_statement: str, misconception_label: str,
                  misconception_id: str, strategy: str, tutor_message: str,
                  student_response: str) -> dict:
    return {
        "system": SYSTEM_PROMPT_V1,
        "user": USER_PROMPT_TEMPLATE_V1.format(
            problem_statement=problem_statement,
            misconception_label=misconception_label,
            misconception_id=misconception_id,
            strategy=strategy,
            tutor_message=tutor_message,
            student_response=student_response,
        ),
        "response_schema": "schemas.models.ResponseEvaluation",
        "version": VERSION,
    }


VERSION_NOTES = {
    "v1": "Initial version. Added PARTIAL_PROGRESS as a third outcome beyond "
          "the spec's binary RESOLVED/PERSISTS to avoid forcing ambiguous "
          "cases into a false binary, since this directly affects Student "
          "Model accuracy. If benchmark testing shows PARTIAL_PROGRESS is "
          "rarely or inconsistently used, consider collapsing back to a "
          "binary for v2 to match the original spec and simplify downstream "
          "adaptive-loop logic.",
}
