# Reasoning Analyzer results — analysis (prompt v1, 30/30 parsed)

**error_type accuracy: 27/30 = 90.0%** — all 30 responses were valid JSON
and schema-valid on the first try (no retries needed).

## The 3 misses — a systematic pattern, not random noise

| Case | Expected | Claimed | Student's error |
|------|----------|---------|------------------|
| A01 | conceptual | execution | `-3x = 12` → divided by `3` instead of `-3`, dropping the sign |
| A07 | conceptual | execution | `-2 * -5` computed as `-10` instead of `+10` during distribution |
| M02 | conceptual | execution | `-x = 6` → wrote `x = 6`, dropping the negative |

**All three misses are sign errors**, and in all three the model's own
`note` field describes them explicitly as "a sign error" but then labels
`error_type: execution` rather than `conceptual`. This is a real,
reproducible bias in prompt v1: the model appears to treat "got the sign
wrong" as inherently an arithmetic slip, when the taxonomy (and the
benchmark's intent) treats a *dropped/mishandled negative sign during an
algebraic operation* as conceptual — the student doesn't understand that
dividing/multiplying by a negative requires carrying the sign through,
which is a rule, not a computation.

This is exactly the kind of finding spec section 17 (prompt engineering
methodology) asks for: a concrete, evidence-backed reason to write a v2
prompt, not a vibes-based tweak.

## Proposed v2 change

Add an explicit disambiguation rule to `SYSTEM_PROMPT_V1`'s CONCEPTUAL
definition:

> A sign error (dropping, flipping, or mishandling a negative sign during
> an operation like multiplication or division) is CONCEPTUAL, not
> execution — it reflects not applying the rule that operating on a
> negative value must carry the sign through, even when the magnitude
> arithmetic (e.g. 12/3) is done correctly.

This directly targets the observed failure mode. v2 should be re-run on
just these 3 cases (or the full 30, to check for regressions elsewhere)
before rolling it into the taxonomy-facing prompts.

## Comparison to baseline

| Metric | Baseline (single prompt) | Analyzer (Node 2 alone) |
|---|---|---|
| Relevant accuracy | 86.7% misconception exact-match | 90.0% error_type exact-match |
| Note | Different tasks — not directly comparable 1:1, but both measure "did the system correctly characterize the nature of the error" | Isolating this judgment into its own node lets us see *and fix* a specific bias (sign-error mislabeling) that's invisible when it's buried inside one big response |

The real payoff comes once the full chain (Analyzer → Classifier →
Critic → Diagnosis Selector) is measured end-to-end against the same 30
cases and compared to the baseline's 86.7% — that comparison is what
section 14/15 of the spec actually asks for.
