# Baseline results — analysis (Gemini, Google AI Studio, 30/30 cases)

**Diagnosis accuracy (exact match): 26/30 = 86.7%** (28/30 = 93.3% counting the
`alt_misconception_id` cases as correct — see `benchmark/cases.py` for why
those 3 cases are deliberately ambiguous).

Scored data: `baseline_results.csv`.

## The 4 misses

| Case | Expected | Claimed | Read |
|------|----------|---------|------|
| G06 | `unknown` (no work shown) | `execution_error` | **Overconfidence** — the model invented a specific diagnosis with zero evidence to support it, instead of asking for the student's work. This is the single most useful data point in this run: it's a direct, measured instance of the failure mode the whole project is built to fix. |
| A05 | `algebra.variable_isolation_error` | `algebra.distribution_error` | Near-miss between two taxonomy categories that are conceptually adjacent by design (multiplying across an unremoved additive term vs. failing to distribute). Arguably a legitimate alternative read. |
| A07 | `algebra.sign_error` | `algebra.distribution_error` | Case was deliberately authored as ambiguous (see `alt_misconception_id` in cases.py) — the baseline picked the alt id, which we count as acceptable. |
| M03 | `geometry.angle_relationship_error` | `geometry.wrong_theorem` | Labeling disagreement, not a reasoning failure — complementary/supplementary confusion is arguably "using the wrong angle-sum rule," which a person could plausibly call either. |

## What this means for Bluetute vs. baseline

The baseline is already fairly strong at labeling *when reasoning is
visible*. The gap the full workflow needs to demonstrate is specifically
on evidence-insufficient cases like G06: a good diagnostic system should
recognize "I don't have enough information" rather than defaulting to
its most common label. Both `unknown` cases in the benchmark (G06, P06)
are worth tracking separately in the final comparison table — P06 was
correctly called `unknown`, G06 was not, so it's not that the model can
never say "unknown," just that it's inconsistent about when to.

This is exactly the kind of signal the Adversarial Critic (spec section
5) is designed to catch: a critic prompted to actively look for
insufficient evidence should flag G06-style cases that a single
generation pass sails past.

## Next comparison point

Once the Reasoning Analyzer + Misconception Classifier + Critic chain is
run on the same 30 cases, compare:
- exact-match accuracy (should meet or beat 86.7%, ideally closer to
  93%+ once ambiguous cases are handled via the critic's alternative
  hypotheses)
- rate of confident-wrong-on-`unknown` cases (should be 0/2, vs.
  baseline's 1/2)
