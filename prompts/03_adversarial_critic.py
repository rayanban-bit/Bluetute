"""
Node 5 — Adversarial Critic
=============================
Purpose: the core differentiating feature of Bluetute. A second model
independently tries to DISPROVE the initial diagnosis, surfacing
alternative explanations before anything is shown to the student. This is
explicitly NOT a rubber stamp — see docs/evaluation.md for the
"critic-agreement-rate" sanity metric used to confirm this node is doing
real adversarial work rather than just agreeing by default.

Recommended model: ideally a DIFFERENT model/provider than the one used for
Nodes 2-3 (e.g. if Reasoning Analyzer + Classifier run on Gemini, run the
Critic on a Claude or Featherless-hosted model). Model diversity reduces
correlated blind spots — this is the strongest justification in the spec
for model routing (see docs/model_routing.md) and should be tested, not
assumed.

Output schema: schemas.models.CriticReview
"""

from schemas.models import CriticReview  # noqa: F401
from taxonomy.misconception_taxonomy import taxonomy_prompt_block

VERSION = "v1"

SYSTEM_PROMPT_V1 = """You are the Adversarial Critic for Bluetute, a math \
tutoring diagnostic system. You will be shown a proposed diagnosis of a \
student's misconception. YOUR JOB IS NOT TO AGREE. You are a skeptic whose \
only role is to stress-test the diagnosis before it reaches a student.

You must:
1. Attempt to construct the strongest available rebuttal of the proposed \
diagnosis, using the same evidence the diagnosing model had access to.
2. Propose at least one, ideally two, alternative misconception hypotheses \
from the taxonomy below (or "execution_error" / "unknown" if warranted) \
that could also explain the observed reasoning.
3. For each alternative, state evidence that supports it AND evidence that \
contradicts it — do not cherry-pick only supporting evidence.
4. Decide whether the original diagnosis survives your scrutiny. Answer \
`diagnosis_survives: true` ONLY if, after genuinely trying to break it, you \
still find it the best-supported explanation. Do not default to true.
5. Propose a `confidence_adjustment` (typically <= 0, range -1.0 to +1.0) \
reflecting how much your review should lower (or, rarely, raise) confidence \
in the original diagnosis.

Do not be contrarian for its own sake — if the evidence genuinely and \
uniquely supports the original diagnosis after real scrutiny, say so. The \
goal is calibration, not reflexive disagreement.

TAXONOMY (for alternative hypotheses):
{taxonomy_block}

Return ONLY the structured output matching the provided schema."""

USER_PROMPT_TEMPLATE_V1 = """Domain: {domain}

Problem: {problem_statement}

Student's reasoning steps (indexed):
{numbered_steps}

Proposed diagnosis:
- misconception_id: {misconception_id}
- label: {label}
- evidence: {evidence}
- confidence: {confidence}
- alternative_candidate_ids already considered by the classifier: {alt_ids}
"""


def build_prompt(domain: str, problem_statement: str, numbered_steps: str,
                  misconception_id: str, label: str, evidence: str,
                  confidence: float, alt_ids: list[str]) -> dict:
    return {
        "system": SYSTEM_PROMPT_V1.format(taxonomy_block=taxonomy_prompt_block()),
        "user": USER_PROMPT_TEMPLATE_V1.format(
            domain=domain,
            problem_statement=problem_statement,
            numbered_steps=numbered_steps,
            misconception_id=misconception_id,
            label=label,
            evidence=evidence,
            confidence=confidence,
            alt_ids=", ".join(alt_ids) if alt_ids else "(none listed)",
        ),
        "response_schema": "schemas.models.CriticReview",
        "version": VERSION,
    }


VERSION_NOTES = {
    "v1": "Initial version. Explicitly instructs the model not to default to "
          "agreement AND not to be reflexively contrarian, since early "
          "internal testing of similar critic prompts tends to collapse to "
          "one extreme or the other. Track diagnosis_survives=True rate "
          "across the benchmark in eval; a rate near 100% or near 0% both "
          "indicate the prompt needs revision (v2 candidate: add few-shot "
          "examples of a diagnosis that legitimately survives vs. one that "
          "legitimately doesn't).",
}
