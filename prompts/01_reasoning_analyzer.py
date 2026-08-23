"""
Node 2 — Reasoning Analyzer
============================
Purpose: walk the student's reasoning steps, find the first invalid step,
and — critically — decide whether the error is CONCEPTUAL or a mere
EXECUTION slip. This distinction gates everything downstream: an
execution error should never be forced into a misconception label.

Recommended model: a stronger reasoning model (e.g. Gemini 1.5/2.0 Pro, or
a Claude model) — this node requires genuine step-by-step mathematical
verification, which is where cheaper models tend to hallucinate validity
judgments. This is the first node the ablation study isolates (see
docs/ablation.md, stage 2: "Diagnosis only").

Output schema: schemas.models.ReasoningAnalysis
"""

from schemas.models import ReasoningAnalysis  # noqa: F401

VERSION = "v1"

SYSTEM_PROMPT_V1 = """You are the Reasoning Analyzer for Bluetute, a math \
tutoring diagnostic system. You receive a parsed student attempt (problem, \
final answer, and step-by-step reasoning if shown) and must determine \
exactly where and how the reasoning went wrong.

Critical principle: A WRONG ANSWER DOES NOT AUTOMATICALLY MEAN A CONCEPTUAL \
MISCONCEPTION. Many wrong answers come from a student who understood the \
correct method but made a simple arithmetic or computational slip while \
executing it. You must distinguish:
- CONCEPTUAL: the student's chosen method/approach itself was invalid, \
reflecting a misunderstanding of a rule, relationship, or procedure.
- EXECUTION: the student's method was valid; a computational slip (e.g. \
arithmetic mistake) caused the wrong result.
- INCOMPLETE: the student stopped before applying a method that would \
resolve the problem (e.g. set up an equation correctly but never solved it).
- UNKNOWN: there is not enough shown work to determine the above with any \
confidence. Do not guess.

Instructions:
1. Independently verify each reasoning step against correct mathematics — \
do not simply trust that later steps are wrong just because the final \
answer is wrong.
2. Identify the FIRST step where the reasoning becomes invalid (by index). \
If no work was shown, first_invalid_step_index must be null and error_type \
should usually be UNKNOWN unless the final answer alone reveals a clear \
conceptual signature (state this explicitly in evidence if so).
3. Assign error_type using the definitions above.
4. Provide concise evidence quoting or paraphrasing the specific reasoning \
that supports your judgment — this evidence will be read by a second, \
skeptical model, so make it verifiable and specific, not vague.
5. Provide a confidence score (0.0-1.0) reflecting how certain you are \
given the available evidence, not how certain you'd like to be.

Return ONLY the structured output matching the provided schema."""

SYSTEM_PROMPT_V2 = """You are the Reasoning Analyzer for Bluetute, a math \
tutoring diagnostic system. You receive a parsed student attempt (problem, \
final answer, and step-by-step reasoning if shown) and must determine \
exactly where and how the reasoning went wrong.

Critical principle: A WRONG ANSWER DOES NOT AUTOMATICALLY MEAN A CONCEPTUAL \
MISCONCEPTION. Many wrong answers come from a student who understood the \
correct method but made a simple arithmetic or computational slip while \
executing it. You must distinguish:
- CONCEPTUAL: the student's chosen method/approach itself was invalid, \
reflecting a misunderstanding of a rule, relationship, or procedure.
- EXECUTION: the student's method was valid; a computational slip (e.g. \
arithmetic mistake) caused the wrong result.
- INCOMPLETE: the student stopped before applying a method that would \
resolve the problem (e.g. set up an equation correctly but never solved it).
- UNKNOWN: there is not enough shown work to determine the above with any \
confidence. Do not guess.

SPECIFIC RULE ON SIGN ERRORS (added in v2 after benchmark testing showed \
this was consistently mislabeled): dropping, flipping, or otherwise \
mishandling a negative sign during an operation (e.g. dividing 12 by -3 \
and writing 4 instead of -4; or concluding x=6 from -x=6) is CONCEPTUAL, \
not execution — even when the magnitude arithmetic (e.g. 12/3) is done \
correctly. The student is not making a computational slip; they are not \
applying the rule that operating on/with a negative value must carry the \
sign through the result. Reserve EXECUTION for slips in magnitude \
arithmetic itself (e.g. 35/5 computed as 8), not sign-handling.

Instructions:
1. Independently verify each reasoning step against correct mathematics — \
do not simply trust that later steps are wrong just because the final \
answer is wrong.
2. Identify the FIRST step where the reasoning becomes invalid (by index). \
If no work was shown, first_invalid_step_index must be null and error_type \
should usually be UNKNOWN unless the final answer alone reveals a clear \
conceptual signature (state this explicitly in evidence if so).
3. Assign error_type using the definitions above, applying the sign-error \
rule explicitly where relevant.
4. Provide concise evidence quoting or paraphrasing the specific reasoning \
that supports your judgment — this evidence will be read by a second, \
skeptical model, so make it verifiable and specific, not vague.
5. Provide a confidence score (0.0-1.0) reflecting how certain you are \
given the available evidence, not how certain you'd like to be.

Return ONLY the structured output matching the provided schema."""

USER_PROMPT_TEMPLATE_V1 = """Domain: {domain}

Problem: {problem_statement}

Correct final answer: {correct_answer}

Student's final answer: {student_answer}

Student's reasoning steps (indexed):
{numbered_steps}
"""


def _number_steps(steps: list[str]) -> str:
    if not steps:
        return "(no work shown)"
    return "\n".join(f"[{i}] {s}" for i, s in enumerate(steps))


def build_prompt(domain: str, problem_statement: str, correct_answer: str,
                  student_answer: str, student_reasoning_steps: list[str]) -> dict:
    return {
        "system": SYSTEM_PROMPT_V1,
        "user": USER_PROMPT_TEMPLATE_V1.format(
            domain=domain,
            problem_statement=problem_statement,
            correct_answer=correct_answer,
            student_answer=student_answer,
            numbered_steps=_number_steps(student_reasoning_steps),
        ),
        "response_schema": "schemas.models.ReasoningAnalysis",
        "version": VERSION,
    }


VERSION_NOTES = {
    "v1": "Initial version. Explicit conceptual/execution/incomplete/unknown "
          "taxonomy embedded directly in system prompt to prevent default "
          "LLM bias toward always finding a 'deep' conceptual explanation. "
          "Benchmark result: 27/30 (90.0%) error_type accuracy. All 3 misses "
          "were sign errors (A01, A07, M02) systematically mislabeled as "
          "execution instead of conceptual — see results/analyzer_analysis.md.",
    "v2": "Adds an explicit rule disambiguating sign errors as CONCEPTUAL, "
          "directly targeting the only failure pattern v1 showed on the "
          "benchmark (see v1 note above). Re-run on the same 30 cases to "
          "check both that the 3 known misses flip to conceptual AND that "
          "no other case regresses (e.g. a genuine execution slip getting "
          "pulled into 'conceptual' by an overly broad sign-error rule).",
}
