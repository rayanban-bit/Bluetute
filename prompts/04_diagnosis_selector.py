"""
Node 6 — Diagnosis Selector
=============================
Purpose: reconcile the initial classification with the critic's review and
produce ONE final diagnosis, with no exposed chain-of-thought — just a
concise evidence summary and an actionable decision on whether an
intervention is even appropriate (low-confidence cases should suppress
intervention rather than guess).

Recommended model: mid-tier reasoning model. This is an arbitration task
over already-produced structured data (not raw student text), so it is a
good second candidate (after Node 1) for a cheaper model in the model
routing ablation.

Output schema: schemas.models.FinalDiagnosis
"""

from schemas.models import FinalDiagnosis  # noqa: F401

VERSION = "v1"

SYSTEM_PROMPT_V1 = """You are the Diagnosis Selector for Bluetute, a math \
tutoring diagnostic system. You receive an initial misconception \
classification and an adversarial critic's review of it. Your job is to \
produce the single final diagnosis that will drive the student-facing \
intervention.

Rules:
- If the critic's diagnosis_survives is true and no alternative hypothesis \
has meaningfully stronger evidence, keep the original misconception_id and \
apply the critic's confidence_adjustment to the original confidence \
(clamped to [0,1]).
- If diagnosis_survives is false, choose whichever hypothesis (the original \
or one of the critic's alternatives) has the strongest supporting evidence \
net of its contradicting evidence. If no hypothesis is well supported, use \
misconception_id "unknown".
- Set intervention_appropriate to false if final_confidence < 0.5 OR if \
misconception_id is "unknown" — in that case the system should ask a \
clarifying question rather than intervene on a guess (handled by a \
downstream fallback, not this node).
- evidence_summary must be concise (a few sentences, <=500 characters), \
citing only the specific evidence that justifies the final choice. Do NOT \
narrate your reasoning process or expose deliberation — state the \
conclusion and its direct support only.
- error_type should reflect the Reasoning Analyzer's original finding \
unless the critic's review specifically overturned it (e.g. revealed an \
execution slip mislabeled as conceptual).

Return ONLY the structured output matching the provided schema."""

USER_PROMPT_TEMPLATE_V1 = """Initial classification:
- misconception_id: {initial_id}
- confidence: {initial_confidence}
- evidence: {initial_evidence}
- error_type (from Reasoning Analyzer): {error_type}

Critic review:
- attempted_rebuttal: {rebuttal}
- alternative_hypotheses: {alternatives}
- diagnosis_survives: {survives}
- survival_rationale: {survival_rationale}
- confidence_adjustment: {confidence_adjustment}
"""


def build_prompt(initial_id: str, initial_confidence: float, initial_evidence: str,
                  error_type: str, rebuttal: str, alternatives: list[dict],
                  survives: bool, survival_rationale: str,
                  confidence_adjustment: float) -> dict:
    alt_str = "; ".join(
        f"{a['misconception_id']} (plausibility={a['plausibility']}, "
        f"support={a['supporting_evidence']}, contra={a['contradicting_evidence']})"
        for a in alternatives
    ) or "(none)"
    return {
        "system": SYSTEM_PROMPT_V1,
        "user": USER_PROMPT_TEMPLATE_V1.format(
            initial_id=initial_id,
            initial_confidence=initial_confidence,
            initial_evidence=initial_evidence,
            error_type=error_type,
            rebuttal=rebuttal,
            alternatives=alt_str,
            survives=survives,
            survival_rationale=survival_rationale,
            confidence_adjustment=confidence_adjustment,
        ),
        "response_schema": "schemas.models.FinalDiagnosis",
        "version": VERSION,
    }


VERSION_NOTES = {
    "v1": "Initial version. Hard confidence threshold (0.5) for "
          "intervention_appropriate is a starting heuristic, not tuned — "
          "the evaluation framework should sweep this threshold against "
          "benchmark labels to find a value that trades off false "
          "interventions vs. missed teaching opportunities, then record the "
          "chosen value here in v2.",
}
