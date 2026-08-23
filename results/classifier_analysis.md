# Misconception Classifier results — analysis (prompt v1, chained on real Analyzer output)

**Exact-match accuracy: 19/20 = 95.0%**, **0/20 invented (non-taxonomy) ids**
— the model respected the controlled taxonomy constraint on every case,
which is the thing spec section 3 explicitly asks to verify ("The model
should select from controlled categories rather than inventing arbitrary
labels").

Only 20 of the 30 benchmark cases reached this node, because it's chained
on what the Analyzer *actually* claimed was conceptual (not the benchmark's
ground truth) — see `results/analyzer_analysis.md` for which 3 cases were
dropped (the sign-error cases the Analyzer mislabeled as execution).

## The 1 miss — a genuinely informative one

| Case | Expected | Claimed | Model's own `alternative_candidate_ids` |
|---|---|---|---|
| A05 | `algebra.variable_isolation_error` | `algebra.distribution_error` | `["algebra.variable_isolation_error"]` |

This is not a blind miss: the classifier's evidence field describes the
failure accurately ("failed to distribute the 4 to the -3 term"), and it
explicitly listed our expected answer as its runner-up candidate. This
confirms something noted at benchmark design time (`benchmark/cases.py`,
case A05's `notes` field): these two taxonomy categories genuinely overlap
for "multiply/divide before clearing an additive term" errors. That's a
taxonomy precision issue worth a line in the final documentation's
"limitations" section (spec section 20), not a prompt failure.

## Running total: chained pipeline vs. baseline

| Stage | Metric | Result |
|---|---|---|
| Baseline (single prompt) | misconception exact-match | 26/30 = 86.7% |
| Analyzer (Node 2) | error_type exact-match | 27/30 = 90.0% |
| Classifier (Node 3, chained on Analyzer's real conceptual calls) | misconception exact-match | 19/20 = 95.0% |

Next: the Adversarial Critic (Node 5) is the node the whole project is
named for — it should be judged less on raw accuracy and more on whether
`diagnosis_survives=False` shows up often enough to be doing real
adversarial work (see `prompts/03_adversarial_critic.py` VERSION_NOTES),
and specifically on whether it catches the A05 taxonomy-overlap case above.
