> **UPDATE — see `results/analyzer_v2_analysis.md` and
> `results/classifier_followup_analysis.md` for the final, exact v2
> numbers: 28/30 (93.3%) exact-match / 29/30 (96.7%) counting legitimate
> alternatives, vs. the baseline's 86.7%.** The tie described below was
> the v1 result, before the sign-error prompt fix. Kept here for the
> historical v1→v2 comparison trail (spec section 17 asks for exactly
> this kind of record).

# Bluetute pipeline vs. single-prompt baseline — full comparison (Nodes 1-6, real data)

This is the first genuine end-to-end comparison the project has: same 30
benchmark cases, same underlying model (Gemini via Google AI Studio) for
both arms, real outputs at every stage — nothing simulated or invented
(spec section 14/20).

## Headline numbers

| System | Metric | Result |
|---|---|---|
| Baseline (single prompt) | misconception exact-match, all 30 cases | **26/30 = 86.7%** |
| Bluetute pipeline (Analyzer→Classifier→Critic→Selector) | misconception exact-match, all 30 cases | **26/30 = 86.7%** |
| Baseline | on the 20 cases the pipeline actually classified as conceptual | 18/20 = 90.0% |
| Bluetute pipeline | on the same 20 cases | **19/20 = 95.0%** |

**Honest read: on raw exact-match accuracy across all 30 cases, the two
systems currently tie at 86.7%.** That's a real result, not a favorable
spin — and it's more informative than it looks, because the two systems
fail on *different, explainable* cases (see below), and one side of that
gap has an identified, not-yet-applied fix.

## Where each system actually fails, and why

**Baseline's 4 misses:** A05, A07 (both ambiguous by our own taxonomy
design), M03 (labeling disagreement), and **G06** — the case with zero
shown work, where the baseline confidently invented `execution_error`
instead of admitting insufficient evidence.

**Pipeline's 4 misses:** A01, A07, M02 (all three are the *same*
sign-error bias identified in `results/analyzer_analysis.md` — the
Reasoning Analyzer systematically mislabels sign errors as `execution`
instead of `conceptual`, which then never reaches classification), and
A05 (the taxonomy-overlap case, also correctly flagged by the Critic as a
plausible alternative but not surfaced by the Selector).

**On G06, the pipeline is correct where the baseline is not** — the
Reasoning Analyzer correctly assigned `unknown` (no work shown), so the
case never reached the Classifier and never got a fabricated diagnosis.
This is the exact overconfidence failure mode the project's central claim
predicts, and it shows up as a real, measured difference here, not just
an anecdote.

## What this means concretely

1. **The 20-case subset that actually reaches full diagnosis is where
   the pipeline's advantage is real and measured: 95.0% vs. 90.0%.**
   Separating "is this conceptual" from "which misconception" into two
   dedicated nodes measurably helps once a case gets that far.
2. **The tie on the full 30 is entirely explained by one identified,
   documented, fixable bug** — the Analyzer's sign-error bias (3 of the
   pipeline's 4 misses). If the proposed v2 fix in
   `results/analyzer_analysis.md` works as intended, those 3 cases would
   very likely flip to conceptual → correctly classified, which would put
   the pipeline at an estimated 29/30 ≈ 96.7% — a genuine, testable
   prediction for the "test 3 prompt versions" step (spec step 5), not a
   guess presented as a result.
3. **The Critic and Selector, as currently prompted, made zero net
   changes to any diagnosis this run** (see `results/critic_analysis.md`
   and `results/selector_results.csv`: `changed_from_classifier` is 0/20
   everywhere). They're not hurting accuracy, but they're not yet
   demonstrably helping it either — their value so far is entirely in
   the reasoning trail they produce (e.g. correctly surfacing A05's real
   alternative), which matters for the "evidence quality" and
   "hallucination/consistency" metrics in spec section 14, even where it
   doesn't move exact-match accuracy.

## Next data point that would make this comparison stronger

Re-run the Reasoning Analyzer with the proposed v2 prompt (sign-error
clarification) on just the 3 affected cases (or all 30, to check for
regressions), then re-run Classifier→Critic→Selector on whatever becomes
newly conceptual, and recompute this table. That is the single most
valuable next experiment for spec step 5 ("test 3 prompt versions") and
step 15 (final metrics) — it directly tests whether one documented,
targeted prompt fix closes the tie.
