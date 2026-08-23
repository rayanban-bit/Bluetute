"""
Node 7 — Intervention Planner
================================
Purpose: choose a pedagogical STRATEGY (not the actual student-facing
text — that's Node 8) based on the diagnosed misconception and the
student's current level from the Student Model. Separating strategy
selection from message generation lets us evaluate/ablate them
independently (see docs/ablation.md, stage 4).

Recommended model: mid-tier model. This is closer to a policy/decision
task than open-ended generation.

Output schema: schemas.models.InterventionPlan
"""

from schemas.models import InterventionPlan  # noqa: F401

VERSION = "v1"

SYSTEM_PROMPT_V1 = """You are the Intervention Planner for Bluetute, a math \
tutoring diagnostic system. Given a final diagnosis and the student's \
current level on the relevant topic (from their student model), choose the \
single best pedagogical strategy for the next intervention.

Available strategies:
- socratic_question: ask a guiding question that leads the student to \
notice the error themselves. Best default for a first attempt at a \
moderate-confidence, non-persistent misconception.
- hint: give a small nudge without asking a question. Good when a full \
Socratic question risks being too oblique for the student's level.
- counterexample: show a case where the student's (flawed) rule clearly \
fails. Good for misconceptions the student holds with apparent confidence \
(e.g. treats an invalid rule as a general law).
- simpler_example: restate the same misconception in an easier numeric or \
structural context. Good when a "weak" skill level suggests the original \
problem's complexity itself is an obstacle.
- visual_explanation: describe a diagram/graph/visual framing. Best for \
Geometry and Functions misconceptions with a strong visual/spatial component.
- reteaching: directly reteach the underlying concept from scratch. Use \
only when the student model shows a `persistent_misconception` on this \
topic (i.e. prior Socratic attempts have already failed) — do not jump to \
reteaching on a first attempt.
- targeted_practice: assign a focused practice problem isolating just the \
misconception. Best after a misconception has just been resolved, to test \
transfer, OR as a low-stakes way to surface the error again if the student \
seems unsure.

Rules:
- Prefer socratic_question by default; only choose a more direct strategy \
(hint, counterexample, reteaching) when the misconception has persisted \
across multiple attempts (student model shows persistent_misconception or \
this is a repeat intervention on the same misconception) or the student's \
level on this topic is "weak".
- difficulty_adjustment should be "easier" if the student's level is weak \
or this is a repeat failed attempt, "harder" only when confirming transfer \
after resolution, otherwise "same".
- rationale must connect the SPECIFIC misconception and SPECIFIC student \
level to the strategy choice, not a generic justification.

Return ONLY the structured output matching the provided schema."""

USER_PROMPT_TEMPLATE_V1 = """Final diagnosis:
- misconception_id: {misconception_id}
- final_confidence: {confidence}
- evidence_summary: {evidence_summary}

Student model for this topic (may be "no prior data"):
- level: {student_level}
- attempts_seen: {attempts_seen}
- last_misconception_id: {last_misconception_id}

Is this a repeat intervention after a failed prior attempt on the SAME \
misconception in this session? {is_repeat}
"""


def build_prompt(misconception_id: str, confidence: float, evidence_summary: str,
                  student_level: str = "no prior data", attempts_seen: int = 0,
                  last_misconception_id: str = "none", is_repeat: bool = False) -> dict:
    return {
        "system": SYSTEM_PROMPT_V1,
        "user": USER_PROMPT_TEMPLATE_V1.format(
            misconception_id=misconception_id,
            confidence=confidence,
            evidence_summary=evidence_summary,
            student_level=student_level,
            attempts_seen=attempts_seen,
            last_misconception_id=last_misconception_id,
            is_repeat=is_repeat,
        ),
        "response_schema": "schemas.models.InterventionPlan",
        "version": VERSION,
    }


VERSION_NOTES = {
    "v1": "Initial version. Strategy-selection rules are hand-authored "
          "heuristics based on general pedagogy, not yet validated against "
          "actual resolution-rate data. Once the evaluation framework has "
          "enough Response Evaluator outcomes, v2 should adjust these rules "
          "based on which strategies actually correlate with "
          "MISCONCEPTION_RESOLVED per misconception category.",
}
