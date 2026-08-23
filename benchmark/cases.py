"""
Bluetute — Benchmark Cases

30 hand-authored student cases across Algebra, Functions, Geometry,
Probability, and Mixed, each with a known expected diagnosis. This is the
answer key used by eval/score.py to measure diagnosis accuracy for both
the single-prompt baseline and the full Bluetute workflow (spec section
12/13/14).

Design choices:
- Every taxonomy id from taxonomy/misconception_taxonomy.py is covered by
  at least one case.
- 5 cases are deliberately execution_error (correct method, arithmetic
  slip) — this directly tests the core claim in the spec that "a wrong
  answer does not automatically mean a conceptual misconception." A
  system that mislabels these as conceptual should be penalized in eval.
- 2 cases are "unknown" (no work shown) — tests that the system resists
  guessing when evidence is insufficient, rather than forcing a taxonomy
  label.
- Several "Mixed" cases are deliberately ambiguous between two taxonomy
  ids (see `alt_misconception_id`) specifically to exercise the
  Adversarial Critic — these are the cases most likely to show a
  measurable difference between the baseline and the full workflow.
- `student_reasoning` is a list of steps (possibly empty), matching
  ParsedInput.student_reasoning_steps so cases can be fed directly into
  Node 1 without reformatting.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    domain: str                      # Algebra | Functions | Geometry | Probability | Mixed
    problem: str
    correct_answer: str
    student_answer: str
    student_reasoning: list[str]
    expected_error_type: str         # conceptual | execution | incomplete | unknown
    expected_misconception_id: str
    alt_misconception_id: str = ""   # plausible alternative, for critic-testing cases
    difficulty: str = "medium"       # easy | medium | hard
    notes: str = ""


CASES: list[BenchmarkCase] = [
    # ------------------------------------------------------------- Algebra
    BenchmarkCase(
        id="A01", domain="Algebra",
        problem="Solve for x: -3x = 12",
        correct_answer="x = -4", student_answer="x = 4",
        student_reasoning=["-3x = 12", "x = 12 / 3 = 4"],
        expected_error_type="conceptual",
        expected_misconception_id="algebra.sign_error",
        difficulty="easy",
    ),
    BenchmarkCase(
        id="A02", domain="Algebra",
        problem="Solve for x: 3(x + 4) = 21",
        correct_answer="x = 3", student_answer="x = 17/3",
        student_reasoning=["3(x + 4) = 21", "3x + 4 = 21", "3x = 17", "x = 17/3"],
        expected_error_type="conceptual",
        expected_misconception_id="algebra.distribution_error",
        difficulty="easy",
    ),
    BenchmarkCase(
        id="A03", domain="Algebra",
        problem="Solve for x: 2x + 6 = 14",
        correct_answer="x = 4", student_answer="x = 10",
        student_reasoning=["2x + 6 = 14", "2x = 14 + 6 = 20", "x = 10"],
        expected_error_type="conceptual",
        expected_misconception_id="algebra.inverse_operation_error",
        difficulty="easy",
        notes="The worked example from the project spec (section 3).",
    ),
    BenchmarkCase(
        id="A04", domain="Algebra",
        problem="Simplify: 4x + 3x^2 - x",
        correct_answer="3x^2 + 3x", student_answer="6x^2",
        student_reasoning=["4x + 3x^2 - x = 3x^2 + 3x", "3x^2 and 3x are both x terms, so combine: 6x^2"],
        expected_error_type="conceptual",
        expected_misconception_id="algebra.combining_unlike_terms",
        difficulty="medium",
    ),
    BenchmarkCase(
        id="A05", domain="Algebra",
        problem="Solve for x: x/4 - 3 = 5",
        correct_answer="x = 32", student_answer="x = 23",
        student_reasoning=["x/4 - 3 = 5", "multiply both sides by 4: x - 3 = 20", "x = 23"],
        expected_error_type="conceptual",
        expected_misconception_id="algebra.variable_isolation_error",
        difficulty="hard",
        notes="Student multiplies by 4 before clearing the additive -3 term, "
              "so the multiplication doesn't apply to the whole left side.",
    ),
    BenchmarkCase(
        id="A06", domain="Algebra",
        problem="Solve for x: 5x - 9 = 26",
        correct_answer="x = 7", student_answer="x = 8",
        student_reasoning=["5x - 9 = 26", "5x = 26 + 9 = 35", "x = 35 / 5 = 8"],
        expected_error_type="execution",
        expected_misconception_id="execution_error",
        difficulty="easy",
        notes="Method is entirely correct; 35/5 miscalculated as 8 instead of 7.",
    ),
    BenchmarkCase(
        id="A07", domain="Algebra",
        problem="Solve for x: -2(x - 5) = 16",
        correct_answer="x = -3", student_answer="x = -13",
        student_reasoning=["-2(x - 5) = 16", "-2x - 10 = 16", "-2x = 26", "x = -13"],
        expected_error_type="conceptual",
        expected_misconception_id="algebra.sign_error",
        alt_misconception_id="algebra.distribution_error",
        difficulty="hard",
        notes="Deliberately ambiguous: the failure is specifically in the sign of "
              "-2 * -5 during distribution, so it plausibly fits either category. "
              "Good test case for the Adversarial Critic.",
    ),
    # ----------------------------------------------------------- Functions
    BenchmarkCase(
        id="F01", domain="Functions",
        problem="What is the domain of f(x) = 1 / (x - 3)?",
        correct_answer="All real numbers except x = 3",
        student_answer="All real numbers",
        student_reasoning=["f(x) = 1/(x-3)", "x can be any real number, so the domain is all real numbers"],
        expected_error_type="conceptual",
        expected_misconception_id="functions.domain_confusion",
        difficulty="medium",
    ),
    BenchmarkCase(
        id="F02", domain="Functions",
        problem="Given f(x) = x^2 for x in {-2, -1, 0, 1, 2}, what is the range?",
        correct_answer="{0, 1, 4}",
        student_answer="{-2, -1, 0, 1, 2}",
        student_reasoning=["The range is the set of x-values: -2, -1, 0, 1, 2"],
        expected_error_type="conceptual",
        expected_misconception_id="functions.range_confusion",
        difficulty="easy",
    ),
    BenchmarkCase(
        id="F03", domain="Functions",
        problem="Find the slope of the line through (2, 3) and (5, 9).",
        correct_answer="slope = 2", student_answer="slope = 1/2",
        student_reasoning=["slope = (5 - 2) / (9 - 3) = 3 / 6 = 1/2"],
        expected_error_type="conceptual",
        expected_misconception_id="functions.slope_confusion",
        difficulty="easy",
    ),
    BenchmarkCase(
        id="F04", domain="Functions",
        problem="Find the x-intercept of y = 2x + 6.",
        correct_answer="x = -3", student_answer="x = 6",
        student_reasoning=["set x = 0: y = 2(0) + 6 = 6", "so the x-intercept is 6"],
        expected_error_type="conceptual",
        expected_misconception_id="functions.intercept_confusion",
        difficulty="medium",
    ),
    BenchmarkCase(
        id="F05", domain="Functions",
        problem="If f(x) = x^2, what is f(x + 2)?",
        correct_answer="x^2 + 4x + 4",
        student_answer="x^2 + 4",
        student_reasoning=["f(x + 2) = f(x) + f(2) = x^2 + 4"],
        expected_error_type="conceptual",
        expected_misconception_id="functions.notation_error",
        difficulty="hard",
    ),
    BenchmarkCase(
        id="F06", domain="Functions",
        problem="If f(x) = 3x - 4, find f(5).",
        correct_answer="f(5) = 11", student_answer="f(5) = 12",
        student_reasoning=["f(5) = 3(5) - 4 = 15 - 4 = 12"],
        expected_error_type="execution",
        expected_misconception_id="execution_error",
        difficulty="easy",
        notes="15 - 4 miscalculated as 12 instead of 11; method fully correct.",
    ),
    # ------------------------------------------------------------ Geometry
    BenchmarkCase(
        id="G01", domain="Geometry",
        problem="A triangle has two sides of length 5 and 12 with a 60-degree "
                "angle between them (not a right triangle). Find the third side.",
        correct_answer="≈10.54 (Law of Cosines)", student_answer="13",
        student_reasoning=["Using the Pythagorean theorem: c^2 = 5^2 + 12^2 = 169", "c = 13"],
        expected_error_type="conceptual",
        expected_misconception_id="geometry.wrong_theorem",
        difficulty="medium",
    ),
    BenchmarkCase(
        id="G02", domain="Geometry",
        problem="Two parallel lines are cut by a transversal. A pair of "
                "co-interior (same-side interior) angles has one angle equal "
                "to 70 degrees. Find the other angle.",
        correct_answer="110 degrees", student_answer="70 degrees",
        student_reasoning=["Co-interior angles are equal", "so the other angle is also 70 degrees"],
        expected_error_type="conceptual",
        expected_misconception_id="geometry.angle_relationship_error",
        difficulty="medium",
    ),
    BenchmarkCase(
        id="G03", domain="Geometry",
        problem="Triangle ABC ~ Triangle DEF with scale factor 2 (DEF is the "
                "larger triangle). AB=4, BC=6, CA=8. Find DE, EF, FD.",
        correct_answer="DE=8, EF=12, FD=16",
        student_answer="DE=4, EF=6, FD=8",
        student_reasoning=["Since the triangles are similar, DEF has the same side lengths as ABC"],
        expected_error_type="conceptual",
        expected_misconception_id="geometry.similarity_confusion",
        difficulty="medium",
    ),
    BenchmarkCase(
        id="G04", domain="Geometry",
        problem="Quadrilateral ABCD has all four sides equal to 5 (no angle "
                "marks given). Find its area.",
        correct_answer="Cannot be determined from side lengths alone",
        student_answer="25",
        student_reasoning=["All four sides are equal so it's a square", "area = 5 x 5 = 25"],
        expected_error_type="conceptual",
        expected_misconception_id="geometry.diagram_interpretation_error",
        difficulty="hard",
        notes="Tests whether the system catches an unjustified assumption "
              "(equal sides implies square) rather than just checking arithmetic.",
    ),
    BenchmarkCase(
        id="G05", domain="Geometry",
        problem="Find the area of a right triangle with legs 6 and 9.",
        correct_answer="27", student_answer="26",
        student_reasoning=["Area = (1/2)(6)(9) = 54 / 2 = 26"],
        expected_error_type="execution",
        expected_misconception_id="execution_error",
        difficulty="easy",
        notes="54/2 miscalculated as 26 instead of 27; method fully correct.",
    ),
    BenchmarkCase(
        id="G06", domain="Geometry",
        problem="A triangle has angles of 50 degrees and 60 degrees. Find the missing angle.",
        correct_answer="70 degrees", student_answer="80 degrees",
        student_reasoning=[],
        expected_error_type="unknown",
        expected_misconception_id="unknown",
        difficulty="easy",
        notes="No work shown at all — tests whether the system resists guessing.",
    ),
    # --------------------------------------------------------- Probability
    BenchmarkCase(
        id="P01", domain="Probability",
        problem="A bag has 5 red and 5 blue marbles. Two are drawn WITHOUT "
                "replacement. What is P(both red)?",
        correct_answer="2/9", student_answer="1/4",
        student_reasoning=["P(both red) = (5/10) x (5/10) = 1/4"],
        expected_error_type="conceptual",
        expected_misconception_id="probability.independence_confusion",
        difficulty="medium",
    ),
    BenchmarkCase(
        id="P02", domain="Probability",
        problem="In a class, 60% of students play soccer, and 30% play both "
                "soccer and basketball. What is P(basketball | soccer)?",
        correct_answer="0.5", student_answer="0.30",
        student_reasoning=["P(basketball | soccer) = P(soccer and basketball) = 0.30"],
        expected_error_type="conceptual",
        expected_misconception_id="probability.conditional_probability_error",
        difficulty="hard",
    ),
    BenchmarkCase(
        id="P03", domain="Probability",
        problem="Two fair coins are flipped. What is P(exactly one head)?",
        correct_answer="1/2", student_answer="1/3",
        student_reasoning=["Possible outcomes: 0 heads, 1 head, 2 heads — 3 outcomes",
                            "P(exactly one head) = 1/3"],
        expected_error_type="conceptual",
        expected_misconception_id="probability.sample_space_error",
        difficulty="medium",
    ),
    BenchmarkCase(
        id="P04", domain="Probability",
        problem="A fair six-sided die is rolled once. What is P(rolling a 2 OR a 5)?",
        correct_answer="1/3", student_answer="1/36",
        student_reasoning=["P(2 or 5) = P(2) x P(5) = (1/6)(1/6) = 1/36"],
        expected_error_type="conceptual",
        expected_misconception_id="probability.addition_vs_multiplication_rule",
        difficulty="easy",
    ),
    BenchmarkCase(
        id="P05", domain="Probability",
        problem="A jar has 3 red, 4 green, and 5 blue marbles. What is P(green)?",
        correct_answer="1/3", student_answer="1/2",
        student_reasoning=["Total = 3 + 4 + 5 = 12", "P(green) = 4/12 = 1/2"],
        expected_error_type="execution",
        expected_misconception_id="execution_error",
        difficulty="easy",
        notes="Method fully correct; 4/12 simplified incorrectly to 1/2 instead of 1/3.",
    ),
    BenchmarkCase(
        id="P06", domain="Probability",
        problem="A spinner has 4 equal sections: red, blue, green, yellow. "
                "What is P(not red)?",
        correct_answer="3/4", student_answer="1/4",
        student_reasoning=[],
        expected_error_type="unknown",
        expected_misconception_id="unknown",
        difficulty="easy",
        notes="No work shown at all — tests whether the system resists guessing.",
    ),
    # -------------------------------------------------------------- Mixed
    BenchmarkCase(
        id="M01", domain="Mixed",
        problem="Solve for x: 4x + 8 = 32",
        correct_answer="x = 6", student_answer="4x = 24 (stopped, no final value given)",
        student_reasoning=["4x + 8 = 32", "4x = 24"],
        expected_error_type="incomplete",
        expected_misconception_id="unknown",
        difficulty="easy",
        notes="Student stopped before dividing; tests the INCOMPLETE error_type path.",
    ),
    BenchmarkCase(
        id="M02", domain="Mixed",
        problem="Solve for x: -x + 4 = 10",
        correct_answer="x = -6", student_answer="x = 6",
        student_reasoning=["-x + 4 = 10", "-x = 6", "x = 6"],
        expected_error_type="conceptual",
        expected_misconception_id="algebra.sign_error",
        alt_misconception_id="algebra.inverse_operation_error",
        difficulty="medium",
        notes="Ambiguous between dropping the negative sign on -x=6->x=6 (sign_error) "
              "and failing to apply the correct inverse operation (multiply by -1). "
              "Good critic-testing case.",
    ),
    BenchmarkCase(
        id="M03", domain="Mixed",
        problem="Two angles are complementary. One angle is 35 degrees. Find the other.",
        correct_answer="55 degrees", student_answer="145 degrees",
        student_reasoning=["Complementary angles sum to 180 degrees", "180 - 35 = 145"],
        expected_error_type="conceptual",
        expected_misconception_id="geometry.angle_relationship_error",
        difficulty="easy",
        notes="Confuses complementary (90 degrees) with supplementary (180 degrees).",
    ),
    BenchmarkCase(
        id="M04", domain="Mixed",
        problem="A committee of 2 people is chosen from 3 men and 3 women "
                "(without replacement). What is P(both women)?",
        correct_answer="1/5", student_answer="1/4",
        student_reasoning=["P(both women) = (3/6) x (3/6) = 1/4"],
        expected_error_type="conceptual",
        expected_misconception_id="probability.independence_confusion",
        alt_misconception_id="probability.sample_space_error",
        difficulty="hard",
        notes="Committee selection is inherently without replacement (dependent); "
              "student treats draws as independent. Could also be framed as a "
              "sample-space miscount — good critic-testing case.",
    ),
    BenchmarkCase(
        id="M05", domain="Mixed",
        problem="A line has slope 3 and passes through (2, 5). What is its y-intercept?",
        correct_answer="b = -1", student_answer="b = 11",
        student_reasoning=["y = 3x + b", "5 = 3(2) + b = 6 + b", "b = 6 + 5 = 11"],
        expected_error_type="conceptual",
        expected_misconception_id="algebra.inverse_operation_error",
        difficulty="medium",
        notes="Cross-domain (Functions setup, Algebra execution): added instead of "
              "subtracting 6 when isolating b.",
    ),
]

CASES_BY_ID: dict[str, BenchmarkCase] = {c.id: c for c in CASES}


def domain_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in CASES:
        counts[c.domain] = counts.get(c.domain, 0) + 1
    return counts


def error_type_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in CASES:
        counts[c.expected_error_type] = counts.get(c.expected_error_type, 0) + 1
    return counts


if __name__ == "__main__":
    print(f"{len(CASES)} benchmark cases")
    print("By domain:", domain_counts())
    print("By expected error_type:", error_type_counts())
    ids_covered = {c.expected_misconception_id for c in CASES} | {
        c.alt_misconception_id for c in CASES if c.alt_misconception_id
    }
    print(f"Distinct misconception ids referenced: {len(ids_covered)}")
