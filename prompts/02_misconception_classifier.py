"""
Node 3 — Misconception Classifier
===================================
Purpose: given a CONCEPTUAL error (from Node 2), select a misconception
label from the controlled taxonomy — never invent a free-text label. Only
called when Node 2's error_type == "conceptual" (execution/incomplete/
unknown attempts should skip straight to a non-taxonomy path — see
workflow_router notes in docs/architecture.md).

Recommended model: mid-tier reasoning model. Classification against a
fixed list is easier than the free verification Node 2 does, so this is a
good candidate for testing whether a cheaper model matches a frontier
model's accuracy (see docs/model_routing.md).

Output schema: schemas.models.MisconceptionClassification
"""

from schemas.models import MisconceptionClassification  # noqa: F401
from taxonomy.misconception_taxonomy import taxonomy_prompt_block

VERSION = "v1"

SYSTEM_PROMPT_V1 = """You are the Misconception Classifier for Bluetute, a \
math tutoring diagnostic system. You receive a student's problem, reasoning, \
and the Reasoning Analyzer's finding of where/how the reasoning first became \
invalid (already confirmed to be a CONCEPTUAL error, not an execution slip). \
Your job is to select the single best-fitting misconception from the fixed \
taxonomy below.

RULES:
- You MUST select `misconception_id` from the taxonomy list below, using \
the id exactly as written (e.g. "algebra.sign_error"). Never invent a new \
id or label, even if none seems like a perfect fit — choose the closest \
match and reflect any imperfection in your confidence score.
- If truly nothing in the taxonomy fits and the evidence is too sparse to \
choose responsibly, use id "unknown" rather than forcing a guess.
- Ground your choice in the SPECIFIC evidence from the reasoning steps, not \
general assumptions about what students "usually" get wrong on this type \
of problem.
- List any other taxonomy ids you seriously considered as \
`alternative_candidate_ids` — this will be handed to a skeptical second \
model, so be honest about genuine ambiguity rather than projecting false \
certainty.

TAXONOMY:
{taxonomy_block}

Return ONLY the structured output matching the provided schema."""

USER_PROMPT_TEMPLATE_V1 = """Domain: {domain}

Problem: {problem_statement}

Student's reasoning steps (indexed):
{numbered_steps}

Reasoning Analyzer finding:
- first_invalid_step_index: {first_invalid_step_index}
- error_type: {error_type}
- evidence: {analyzer_evidence}
- confidence: {analyzer_confidence}
"""


def build_prompt(domain: str, problem_statement: str, numbered_steps: str,
                  first_invalid_step_index, error_type: str,
                  analyzer_evidence: str, analyzer_confidence: float) -> dict:
    return {
        "system": SYSTEM_PROMPT_V1.format(taxonomy_block=taxonomy_prompt_block()),
        "user": USER_PROMPT_TEMPLATE_V1.format(
            domain=domain,
            problem_statement=problem_statement,
            numbered_steps=numbered_steps,
            first_invalid_step_index=first_invalid_step_index,
            error_type=error_type,
            analyzer_evidence=analyzer_evidence,
            analyzer_confidence=analyzer_confidence,
        ),
        "response_schema": "schemas.models.MisconceptionClassification",
        "version": VERSION,
    }


VERSION_NOTES = {
    "v1": "Initial version. Taxonomy injected verbatim from "
          "taxonomy.misconception_taxonomy so edits to the taxonomy module "
          "propagate automatically. Validate misconception_id against "
          "TAXONOMY_BY_ID post-hoc in the eval harness; if the model still "
          "invents ids despite instructions, v2 should switch to constrained "
          "decoding / enum-typed structured output instead of relying on "
          "prompt compliance alone.",
}
