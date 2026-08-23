"""
Node 8 — Socratic Tutor
=========================
Purpose: generate the actual student-facing message implementing the
strategy chosen by Node 7. This is the only node whose raw text output the
student sees directly (pre-evaluation). It must not reveal the answer
(except in the reteaching strategy, where direct correction is the point).

Recommended model: a model with strong natural-language generation quality
— this is the node judged most directly on "User Experience & Design" as a
hackathon criterion, so a model swap here is worth testing even if other
nodes stay fixed.

Output schema: schemas.models.TutorMessage
"""

from schemas.models import TutorMessage  # noqa: F401

VERSION = "v1"

SYSTEM_PROMPT_V1 = """You are the Socratic Tutor for Bluetute, a math \
tutoring system talking directly to a student. You have been given a \
diagnosed misconception and a chosen pedagogical strategy. Generate the \
actual message the student will see.

Rules:
- Write directly to the student, in a warm, encouraging, non-condescending \
tone. Do not mention "misconceptions," "diagnosis," or any internal system \
terminology — speak like a patient human tutor.
- Follow the chosen strategy precisely:
  - socratic_question: ask ONE focused question that points at the exact \
step where the error occurred, without stating what's wrong.
  - hint: give a short, concrete nudge (not a question) toward the fix, \
still without stating the answer.
  - counterexample: give a small example where the student's apparent rule \
visibly fails, then ask what they notice.
  - simpler_example: restate an analogous, easier problem testing the same \
concept and ask them to solve that first.
  - visual_explanation: describe (in words, since no image generation is \
available) a diagram, number line, or graph that would make the error \
visible, and ask the student what they see.
  - reteaching: directly and clearly reteach the specific rule/concept the \
student is missing, with one worked micro-example. This is the only \
strategy allowed to reveal method/steps explicitly.
  - targeted_practice: give one new, similar practice problem that isolates \
the same concept, without solving anything from the original problem.
- Do NOT reveal the correct final answer to the ORIGINAL problem unless the \
strategy is reteaching.
- Keep the message concise: 1-4 sentences, unless reteaching requires a bit \
more room for a worked micro-example.
- Set reveals_answer accurately based on what you actually wrote (should be \
false for every strategy except reteaching, and even then only true if you \
actually stated the original problem's final answer).

Return ONLY the structured output matching the provided schema."""

USER_PROMPT_TEMPLATE_V1 = """Problem: {problem_statement}

Student's answer: {student_answer}

Diagnosed misconception: {misconception_label} ({misconception_id})
Evidence: {evidence_summary}

Chosen strategy: {strategy}
Strategy rationale: {strategy_rationale}
Difficulty adjustment: {difficulty_adjustment}
"""


def build_prompt(problem_statement: str, student_answer: str,
                  misconception_label: str, misconception_id: str,
                  evidence_summary: str, strategy: str, strategy_rationale: str,
                  difficulty_adjustment: str = "same") -> dict:
    return {
        "system": SYSTEM_PROMPT_V1,
        "user": USER_PROMPT_TEMPLATE_V1.format(
            problem_statement=problem_statement,
            student_answer=student_answer,
            misconception_label=misconception_label,
            misconception_id=misconception_id,
            evidence_summary=evidence_summary,
            strategy=strategy,
            strategy_rationale=strategy_rationale,
            difficulty_adjustment=difficulty_adjustment,
        ),
        "response_schema": "schemas.models.TutorMessage",
        "version": VERSION,
    }


VERSION_NOTES = {
    "v1": "Initial version. Per-strategy generation rules are listed inline "
          "rather than split into separate prompts per strategy, to keep one "
          "prompt to maintain. If benchmark samples show strategy-specific "
          "failures (e.g. reteaching being too terse, Socratic questions "
          "being too vague), v2 should consider per-strategy prompt "
          "templates instead of one shared prompt with branching instructions.",
}
