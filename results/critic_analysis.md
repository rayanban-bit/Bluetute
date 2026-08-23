# Adversarial Critic results — analysis (prompt v1, chained on real Classifier output)

**diagnosis_survives rate: 20/20 = 100%.**

This is exactly the failure mode `prompts/03_adversarial_critic.py`'s own
`VERSION_NOTES` predicted and asked the eval harness to watch for: *"a
rate near 100% or near 0% both indicate the prompt needs revision."* On
this run, the critic never once concluded a diagnosis didn't survive.
That's the headline result for this node, and it should be reported
honestly rather than glossed over (spec section 14: "Do not invent
results").

## A more specific finding than "100% agreement"

Looking at the actual `alternative_hypotheses` the critic proposed, in
**10 of the 20 cases** (F04, F05, G02, G03, P01, P02, P03, P04, M03, M04)
the critic's "alternative" hypothesis has **the same `misconception_id`**
as the diagnosis it was supposed to be attacking, with `plausibility` near
0.9 and `contradicting_evidence: "None."`. That's not an alternative
hypothesis — it's the model restating the original answer and calling it
a check. On these cases the critic isn't doing adversarial work at all;
it's pattern-matching agreement.

Contrast this with the 2 cases where the critic behaved as designed:

- **A05** (the one case the Classifier got wrong): the critic correctly
  named `algebra.variable_isolation_error` — a genuinely different id —
  as the alternative, with real supporting/contradicting evidence on both
  sides. This is exactly the intended behavior. It just didn't go the
  extra step of setting `diagnosis_survives: false`, so the Diagnosis
  Selector (Node 6) will need to weigh the alternative hypothesis itself
  rather than trust the survives flag alone.
- **M05**: the only case with a non-zero `confidence_adjustment` (-0.1)
  and a genuinely distinct alternative (`execution_error`), with a
  reasoned rebuttal for both sides. Diagnosis still survived, but this is
  real scrutiny, not a rubber stamp.

## Net effect on accuracy this run

| | Cases | Result |
|---|---|---|
| Classifier got wrong, critic caught via correct alternative | 1/1 | ✅ A05 |
| Classifier got right, critic wrongly overturned | 0/19 | ✅ no false alarms |

So on raw accuracy, adding the Critic didn't change the scoreboard
(19/20 either way) — its value on this run was entirely in the *quality
and traceability* of the reasoning attached to A05, not in flipping any
verdict. That's a legitimate, useful, non-overstated result for the
ablation study (spec section 15): on this benchmark, "Diagnosis + Critic"
≈ "Diagnosis only" on accuracy, but the critic's rubber-stamp tendency on
easy cases is itself the actionable finding.

## Proposed v2 change

Add an explicit constraint to `SYSTEM_PROMPT_V1`:

> An `alternative_hypotheses` entry MUST propose a `misconception_id`
> DIFFERENT from the one being reviewed. If you cannot find a genuinely
> different plausible explanation, leave `alternative_hypotheses` empty
> rather than restating the original diagnosis — and say so explicitly in
> `attempted_rebuttal`.

This should be tested specifically on the 10 "restated" cases above to
see if it either (a) surfaces real alternatives the model was capable of
finding but didn't bother to, or (b) confirms those 10 diagnoses really
are uncontested, which is also a valid and useful outcome to measure.
