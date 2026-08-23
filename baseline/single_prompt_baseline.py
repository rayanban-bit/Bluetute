"""
Baseline — Single-Prompt Tutor
=================================
Purpose: the comparison point for Bluetute's whole multi-stage workflow.
One LLM call, given the same input as the full pipeline (problem + student
answer + reasoning if shown), must produce a tutoring response AND
(optionally) name a misconception id — using the SAME taxonomy — so
diagnosis accuracy can be scored on equal footing (see docs/evaluation.md).

Deliberately kept as close as possible to "what a naive integration would
do": one prompt, one call, no critic, no separate reasoning-analysis step.
This is stage 1 of the ablation study (docs/ablation.md).

Recommended model: run the baseline on the SAME model used as the primary
model in the full workflow, so the comparison isolates the workflow
structure itself rather than a model-quality difference. If multiple
models are tested, run the baseline against each for a fair per-model
comparison.

Output schema: schemas.models.BaselineResponse
"""

from schemas.models import BaselineResponse  # noqa: F401
from taxonomy.misconception_taxonomy import taxonomy_prompt_block

VERSION = "v1"

SYSTEM_PROMPT_V1 = """You are a math tutor. A student has attempted a \
problem and gotten it wrong (or you must first check if they got it right). \
Given the problem and the student's answer and work, respond to the \
student the way a good tutor would: helpfully, without immediately just \
handing over the final answer, and try to help them find their own mistake.

If you can identify what likely misconception caused the error, name it \
using one of the following ids (or "execution_error" if it looks like a \
simple slip, or "unknown" if you can't tell):
{taxonomy_block}

Return ONLY the structured output matching the provided schema: a \
`tutoring_response` (the message to the student) and an optional \
`claimed_misconception_id`."""

USER_PROMPT_TEMPLATE_V1 = """Problem: {problem_statement}

Student's answer: {student_answer}

Student's shown work (may be empty): {student_reasoning_raw}
"""


def build_prompt(problem_statement: str, student_answer: str,
                  student_reasoning_raw: str = "") -> dict:
    return {
        "system": SYSTEM_PROMPT_V1.format(taxonomy_block=taxonomy_prompt_block()),
        "user": USER_PROMPT_TEMPLATE_V1.format(
            problem_statement=problem_statement,
            student_answer=student_answer,
            student_reasoning_raw=student_reasoning_raw or "(none provided)",
        ),
        "response_schema": "schemas.models.BaselineResponse",
        "version": VERSION,
    }


VERSION_NOTES = {
    "v1": "Initial version. Intentionally given the SAME taxonomy access as "
          "Bluetute's classifier so that any accuracy gap measured in "
          "evaluation reflects the multi-stage WORKFLOW (decomposition + "
          "adversarial verification), not an unfair information advantage. "
          "Do not add reasoning-analysis-style scaffolding to this prompt in "
          "later versions — that would defeat its purpose as a single-prompt "
          "baseline; keep changes here limited to fixing genuine ambiguity, "
          "not adding capability.",
}
