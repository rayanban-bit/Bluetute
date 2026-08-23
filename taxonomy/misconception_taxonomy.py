"""
Bluetute — Misconception Taxonomy

A controlled vocabulary of student misconceptions, grouped by math domain.
The Misconception Classifier node (see prompts/03_misconception_classifier.py)
MUST select from this list rather than inventing free-text labels. This is
what makes diagnoses comparable across benchmark cases and lets us score
classifier accuracy against a known-answer key (see benchmark/cases.csv).

Design notes:
- Each entry has a stable `id` (used in benchmark labels and eval scripts),
  a human-readable `label`, a one-line `definition` a grader/LLM can use to
  disambiguate near-neighbor categories, and 1-2 `signals` describing what
  the error typically looks like in a student's written reasoning.
- "execution_error" and "unknown" are deliberately included as escape
  hatches. Node 2 (Reasoning Analyzer) is responsible for first separating
  conceptual errors from simple arithmetic slips — NOT every wrong answer
  maps to a domain misconception. Forcing a taxonomy pick for a slip would
  corrupt the benchmark and the student model.
- Keep this file the single source of truth. Prompts should reference it by
  import (or by rendering `taxonomy_prompt_block()`) rather than re-typing
  the list, so a taxonomy edit doesn't require hunting through every prompt.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Misconception:
    id: str
    domain: str
    label: str
    definition: str
    signals: list[str] = field(default_factory=list)


TAXONOMY: list[Misconception] = [
    # ---------------------------------------------------------------- Algebra
    Misconception(
        id="algebra.sign_error",
        domain="Algebra",
        label="Sign error",
        definition="Student drops, flips, or mishandles a negative sign when "
        "moving a term or applying an operation.",
        signals=["term crosses '=' without sign flip", "-x treated as x"],
    ),
    Misconception(
        id="algebra.distribution_error",
        domain="Algebra",
        label="Distribution error",
        definition="Student fails to distribute a coefficient/negative sign "
        "across all terms inside parentheses, or distributes incorrectly.",
        signals=["only first term inside parens is multiplied", "a(b+c) -> ab+c"],
    ),
    Misconception(
        id="algebra.inverse_operation_error",
        domain="Algebra",
        label="Inverse operation error",
        definition="Student applies the wrong inverse operation to isolate a "
        "variable (e.g. adds instead of subtracts, multiplies instead of "
        "divides), or applies it to only one side of the equation.",
        signals=["operation applied to one side only", "wrong operation chosen to undo a step"],
    ),
    Misconception(
        id="algebra.combining_unlike_terms",
        domain="Algebra",
        label="Combining unlike terms",
        definition="Student adds or subtracts terms that are not like terms "
        "(different variables or exponents) as if they were.",
        signals=["3x + 2 -> 5x", "x + x^2 -> x^3 or 2x^2"],
    ),
    Misconception(
        id="algebra.variable_isolation_error",
        domain="Algebra",
        label="Variable isolation / order-of-operations error",
        definition="Student isolates the variable using steps in an invalid "
        "order (e.g. divides before removing an additive term) leading to a "
        "structurally wrong equation, independent of arithmetic slips.",
        signals=["divides whole equation before removing constant", "skips a required step"],
    ),
    # -------------------------------------------------------------- Functions
    Misconception(
        id="functions.domain_confusion",
        domain="Functions",
        label="Domain confusion",
        definition="Student confuses valid input values with output values, "
        "or misidentifies restrictions on the domain (e.g. ignores "
        "denominators/roots that exclude values).",
        signals=["reports range values as domain", "misses excluded x where denominator = 0"],
    ),
    Misconception(
        id="functions.range_confusion",
        domain="Functions",
        label="Range confusion",
        definition="Student confuses the set of possible outputs with the "
        "set of inputs, or misreads range from a graph/table.",
        signals=["reports domain values as range", "reads x-values off a graph for range"],
    ),
    Misconception(
        id="functions.slope_confusion",
        domain="Functions",
        label="Slope confusion",
        definition="Student miscomputes or misinterprets slope, e.g. inverts "
        "rise/run, uses (x2-x1)/(y2-y1), or confuses slope sign with "
        "direction of the line.",
        signals=["rise/run inverted", "sign of slope doesn't match line direction"],
    ),
    Misconception(
        id="functions.intercept_confusion",
        domain="Functions",
        label="Intercept confusion",
        definition="Student confuses x-intercept with y-intercept, or "
        "miscomputes one by substituting the wrong variable value.",
        signals=["sets x=0 to find x-intercept", "reports (0,b) as x-intercept"],
    ),
    Misconception(
        id="functions.notation_error",
        domain="Functions",
        label="Function notation error",
        definition="Student misreads f(x) notation, e.g. treats f(x) as "
        "f times x, or evaluates f(a+b) as f(a)+f(b) without justification.",
        signals=["f(x) treated as multiplication", "f(a+b) -> f(a)+f(b)"],
    ),
    # --------------------------------------------------------------- Geometry
    Misconception(
        id="geometry.wrong_theorem",
        domain="Geometry",
        label="Wrong theorem applied",
        definition="Student applies a geometric theorem or formula that "
        "does not fit the figure or conditions given.",
        signals=["Pythagorean theorem on a non-right triangle", "wrong area/volume formula"],
    ),
    Misconception(
        id="geometry.angle_relationship_error",
        domain="Geometry",
        label="Angle relationship error",
        definition="Student misidentifies the relationship between angles "
        "(e.g. treats co-interior angles as equal instead of "
        "supplementary, confuses alternate and corresponding angles).",
        signals=["co-interior angles set equal", "corresponding vs alternate mixed up"],
    ),
    Misconception(
        id="geometry.similarity_confusion",
        domain="Geometry",
        label="Similarity / congruence confusion",
        definition="Student assumes two figures are congruent when only "
        "similar (or vice versa), or sets up an incorrect similarity ratio.",
        signals=["uses 1:1 ratio for similar (not congruent) figures", "mismatched correspondence"],
    ),
    Misconception(
        id="geometry.diagram_interpretation_error",
        domain="Geometry",
        label="Diagram interpretation error",
        definition="Student misreads the diagram itself — wrong side "
        "lengths, assumes a figure is drawn to scale, or assumes "
        "unstated properties (e.g. assumes a quadrilateral is a "
        "parallelogram without justification).",
        signals=["assumes property not given/marked in diagram", "misreads labeled length"],
    ),
    # ------------------------------------------------------------- Probability
    Misconception(
        id="probability.independence_confusion",
        domain="Probability",
        label="Independence confusion",
        definition="Student treats dependent events as independent (or vice "
        "versa), e.g. ignores that sampling without replacement changes "
        "probabilities.",
        signals=["reuses original probability after removal", "P(A and B)=P(A)*P(B) when not independent"],
    ),
    Misconception(
        id="probability.conditional_probability_error",
        domain="Probability",
        label="Conditional probability error",
        definition="Student confuses P(A|B) with P(B|A), or computes a "
        "conditional probability using the wrong sample space/denominator.",
        signals=["denominator uses total sample space instead of the given condition", "P(A|B) and P(B|A) swapped"],
    ),
    Misconception(
        id="probability.sample_space_error",
        domain="Probability",
        label="Sample space error",
        definition="Student miscounts or misdefines the total sample space "
        "(e.g. omits equally likely outcomes, double-counts, or uses an "
        "incorrect total).",
        signals=["total outcomes miscounted", "ignores ordering/combinations distinction"],
    ),
    Misconception(
        id="probability.addition_vs_multiplication_rule",
        domain="Probability",
        label="Addition vs. multiplication rule confusion",
        definition="Student adds probabilities where they should multiply "
        "(or vice versa), typically confusing 'or' (union) with 'and' "
        "(intersection) scenarios.",
        signals=["P(A or B) computed as P(A)*P(B)", "P(A and B) computed as P(A)+P(B)"],
    ),
    # ----------------------------------------------------------- Escape hatches
    Misconception(
        id="execution_error",
        domain="General",
        label="Execution / arithmetic error (no conceptual misconception)",
        definition="Student's reasoning and chosen method were conceptually "
        "sound; the error is a simple arithmetic or computational slip "
        "(e.g. miscalculated 14-6). Use this when Node 2 (Reasoning "
        "Analyzer) determines the method was valid but execution failed.",
        signals=["correct method, wrong arithmetic result", "single computational slip, no repeated pattern"],
    ),
    Misconception(
        id="unknown",
        domain="General",
        label="Unclear / insufficient evidence",
        definition="Available reasoning is too sparse, ambiguous, or "
        "contradictory to confidently select a taxonomy category. Prefer "
        "this over forcing a low-confidence guess into a specific label.",
        signals=["no shown work", "reasoning text too short/garbled to interpret"],
    ),
]

TAXONOMY_BY_ID: dict[str, Misconception] = {m.id: m for m in TAXONOMY}

DOMAINS: list[str] = sorted({m.domain for m in TAXONOMY})


def taxonomy_prompt_block() -> str:
    """Render the taxonomy as a compact, LLM-readable block for prompt
    injection into the Misconception Classifier (and, for cross-checking,
    the Adversarial Critic). Keeping this in one function means every
    prompt version pulls the exact same list."""
    lines = []
    current_domain = None
    for m in TAXONOMY:
        if m.domain != current_domain:
            current_domain = m.domain
            lines.append(f"\n{current_domain}:")
        lines.append(f'  - id: "{m.id}"  label: "{m.label}"\n'
                      f'    definition: {m.definition}')
    return "\n".join(lines).strip()


if __name__ == "__main__":
    print(f"{len(TAXONOMY)} misconceptions across {len(DOMAINS)} domains: {DOMAINS}")
    print(taxonomy_prompt_block())
