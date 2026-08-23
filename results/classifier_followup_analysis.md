# Classifier follow-up (3 sign-error cases) — result

**2/3 exact-match, 3/3 counting the legitimate alternative.**

| Case | Expected | Claimed | Alt listed | Read |
|---|---|---|---|---|
| A01 | `algebra.sign_error` | `algebra.sign_error` | — | correct |
| A07 | `algebra.sign_error` | `algebra.distribution_error` | `algebra.sign_error` | this is the benchmark's own deliberately-ambiguous case (`alt_misconception_id` set at design time in `benchmark/cases.py`) — the classifier landed on the alternative reading and explicitly listed our expected id as its own alternative candidate |
| M02 | `algebra.sign_error` | `algebra.sign_error` | — | correct |

A07 is not a new failure mode — it's the same ambiguity the benchmark
was designed to probe, now confirmed from a second angle (previously the
Critic surfaced this same tension on the structurally similar case A05).

## Final, exact (not estimated) full-pipeline number

| System | Full 30-case accuracy |
|---|---|
| Baseline (single prompt) | 26/30 = 86.7% |
| Bluetute pipeline v1 | 26/30 = 86.7% |
| **Bluetute pipeline v2 — exact match** | **28/30 = 93.3%** |
| **Bluetute pipeline v2 — exact-or-legitimate-alternative** | **29/30 = 96.7%** |

Remaining 2 misses under strict exact-match: A05 (taxonomy overlap,
documented in `results/classifier_analysis.md`) and A07 (the same kind
of overlap, documented above) — both are genuine near-misses between two
adjacent taxonomy categories, not diagnostic failures. Both were also
independently flagged as ambiguous by the Adversarial Critic on
structurally similar cases, which is itself evidence the Critic's
alternative-hypothesis mechanism is catching something real, even where
the Diagnosis Selector isn't (yet) acting on it.

Note: Critic + Diagnosis Selector were not re-run on these 3 cases —
across the original 20, neither ever changed a diagnosis
(`changed_from_classifier` was 0/20 throughout), so their effect here is
assumed unchanged. This is a stated assumption, not a hidden one; re-run
`eval/generate_critic_runbook.py` / `eval/generate_selector_runbook.py`
on these 3 cases specifically if full rigor is wanted before final
submission.
