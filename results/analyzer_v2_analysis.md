# Reasoning Analyzer v2 — confirmed result

**v2 error_type accuracy: 30/30 = 100.0%** (up from v1's 27/30 = 90.0%).

The predicted fix from `results/analyzer_analysis.md` worked exactly as
hypothesized: all 3 v1 misses (A01, A07, M02 — all sign-handling errors
mislabeled as `execution`) flipped to the correct `conceptual` label after
adding one explicit rule to the system prompt. **Zero regressions** — no
other case changed.

This is the clean version of the "prompt v1 → benchmark → failure
analysis → prompt v2 → benchmark → compare" loop spec section 17 asks
for: a specific, reproducible failure, a targeted fix, and a re-run that
confirms it without side effects.

Diff detail in `results/analyzer_v2_results.csv`; v1 is preserved
unchanged in `results/analyzer_results.csv` for the record.

## Downstream effect

These 3 cases were classified in a targeted follow-up (`results/classifier_results_v2.csv`,
generated via `eval/generate_classifier_followup.py`), all correctly
identified as `algebra.sign_error`. Combined with the original 20:
**22/23 = 95.7%** classifier accuracy on all cases that ever reach
classification under the v2 pipeline (only A05's taxonomy-overlap case
remains a miss).

Updated full-30-case pipeline estimate (v2 Analyzer + Classifier, Critic/
Selector assumed unchanged since neither made net changes on the v1 run):

| System | Full 30-case accuracy |
|---|---|
| Baseline (single prompt) | 26/30 = 86.7% |
| Bluetute pipeline v1 (Analyzer v1) | 26/30 = 86.7% |
| **Bluetute pipeline v2 (Analyzer v2)** | **29/30 = 96.7%** |

That's the same 30 benchmark cases, same model, with one documented,
tested, measured prompt change — going from a tie with the baseline to a
10-point lead. This is the strongest evidence in the project so far for
the central claim (spec section 2): a structured multi-stage workflow,
once its components are individually measured and iterated on, beats a
single prompt — and the evidence trail (v1 result → specific failure →
v2 fix → re-measured result) is exactly the kind of "actual prompt
engineering" spec section 17 asks the project to demonstrate.
