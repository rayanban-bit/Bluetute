# Bluetute

**An AI tutoring workflow that diagnoses *why* a student got a math problem
wrong — conceptual misconception, execution slip, or insufficient evidence —
before deciding how to help, instead of jumping straight from a wrong answer
to a correction.**

Built for **Reverie Hacks 2026**, ML Prompt Engineering track.

| | |
|---|---|
| 📄 Full documentation | [`docs/Bluetute_Documentation.docx`](docs/Bluetute_Documentation.docx) |
| 🖼 ML workflow diagram | [`diagram/workflow.png`](diagram/workflow.png) |
| 📊 Headline result | Single-prompt baseline **26/30 (86.7%)** → Bluetute pipeline **28/30 (93.3%)** exact-match, **29/30 (96.7%)** counting legitimate alternatives — real benchmark numbers, not projected (see `results/`) |

## Project story

### Inspiration

The idea for Bluetute came directly from the hackathon community. While
exploring the hackathon Discord, we noticed many participants discussing
their preparation for the SAT. That made us think about the challenges
students face when preparing for exams: practicing hundreds of questions is
useful, but simply knowing whether an answer is right or wrong doesn't
necessarily explain why a student keeps making the same type of mistake, or
how they can improve and understand their errors.

This led us to ask: could we build an AI tutor that doesn't just say if the
answer is wrong or correct, but explains the student's mistake and adapts
its teaching to it? From there, we developed the idea of Bluetute: an AI
workflow that analyzes a student's reasoning, identifies the underlying
misconception, verifies that diagnosis, and generates a targeted
intervention.

The SAT became our initial use case because it provides a clear environment
for testing the system: students solve structured problems, make recurring
types of mistakes, and need to improve not only their answers but their
underlying reasoning.

### How we built it

Instead of creating Bluetute as a straightforward chatbot, we designed it as
a multi-stage AI teaching workflow. It evaluates a student's logic, finds
any misunderstandings, confirms the diagnosis, and develops a focused
intervention. To increase the workflow's dependability, we used distinct AI
roles, structured/typed outputs, and versioned, purpose-built prompts for
each node — and benchmarked every one of them against a single-prompt
baseline instead of assuming the extra structure would help.

### Challenges we ran into

Our biggest challenge was distinguishing between a simple execution slip and
a deeper conceptual misconception — a sign-error bias in the Reasoning
Analyzer (documented in `results/analyzer_analysis.md`) was the clearest
example, and fixing it took a full benchmark → failure analysis → re-prompt
→ re-benchmark loop, not a guess. We also had to prevent the AI from making
confident assumptions when a student's reasoning was unclear, which is why
the Reasoning Analyzer has an explicit UNKNOWN state. Finally, we had to
balance the benefits of multiple AI steps against the added complexity,
latency, and cost — which is exactly what the ablation study in the full
documentation was built to measure honestly rather than assume.

### Accomplishments that we're proud of

We take pride in turning a straightforward tutoring concept into a
comprehensive diagnostic process, where each stage has a distinct function
rather than relying on a single AI call to handle everything. The
adversarial verification step — which actively questions the original
diagnosis before Bluetute decides how to help the student — is something
we're especially proud of, and it's the project's core differentiator.

### What we learned

We learned that writing a good prompt is only one part of effective prompt
engineering. The final system is shaped just as much by how a problem is
broken down into nodes, how those nodes' outputs are structured and
validated, how models are made to check each other, and how disagreements
between them get resolved.

### What's next for Bluetute

SAT preparation is only our starting point. We want Bluetute to support
different exams and academic assessments, across subjects and difficulty
levels. Our goal is to build a universal AI study companion that identifies
recurring weaknesses, adapts practice to each student, and helps them
improve their understanding rather than simply giving them answers.

## Repo layout

```
bluetute/
├── taxonomy/
│   └── misconception_taxonomy.py   # controlled vocabulary, single source of truth
├── schemas/
│   └── models.py                   # Pydantic output schema per node
├── prompts/
│   ├── 00_input_parser.py          # Node 1
│   ├── 01_reasoning_analyzer.py    # Node 2
│   ├── 02_misconception_classifier.py  # Node 3
│   ├── 03_adversarial_critic.py    # Node 5
│   ├── 04_diagnosis_selector.py    # Node 6
│   ├── 05_intervention_planner.py  # Node 7
│   ├── 06_socratic_tutor.py        # Node 8
│   └── 07_response_evaluator.py    # Node 9
└── baseline/
    └── single_prompt_baseline.py   # comparison point (ablation stage 1)
```

Node numbering follows the spec's node list; file numbering follows
pipeline execution order (the spec's Node 4, "Diagnosis Selector," sits
after the critic in execution, so it is file `04_` even though its title
number is 6 — see the docstring in each file for its exact spec node
number and rationale).

## How each prompt file is structured

Every file under `prompts/` and `baseline/` follows the same shape, so
adding v2/v3 revisions later is mechanical:

- **Docstring** — the node's purpose, why it's a separate node at all,
  and a *recommended model* with reasoning (not a hard commitment — see
  Model Selection below).
- **`SYSTEM_PROMPT_V1`** — the versioned system prompt.
- **`USER_PROMPT_TEMPLATE_V1`** — the versioned user-turn template.
- **`build_prompt(...)`** — assembles system + user text plus the
  `response_schema` path, ready to hand to whichever LLM client wrapper
  gets built next (Gemini structured output, Claude tool-use, etc.).
- **`VERSION_NOTES`** — a dict keyed by version string. This is the
  prompt-engineering paper trail required by the hackathon rubric: each
  entry says what the version does and, importantly, what to watch for in
  benchmark testing that would justify writing a v2. When a v2 is written,
  add a new `SYSTEM_PROMPT_V2` / `USER_PROMPT_TEMPLATE_V2`, extend
  `VERSION_NOTES["v2"]` with *why* it changed and what benchmark failure
  motivated it, and switch `VERSION` — never silently overwrite v1, since
  the ablation study needs to be able to re-run any historical version.

## Why the taxonomy is a separate module

`taxonomy/misconception_taxonomy.py` is imported by the classifier,
critic, and baseline prompts (`taxonomy_prompt_block()`) rather than
copy-pasted into each. This guarantees all three nodes — and the baseline,
which needs the *same* taxonomy to make the comparison fair — are always
looking at an identical, current list. Editing the taxonomy is a one-file
change.

## Why schemas are centralized

`schemas/models.py` holds one Pydantic model per node output. This isn't
just for documentation: these models are meant to be handed directly to a
provider's structured-output feature (Gemini `response_schema`, an
OpenAI/Claude JSON-schema tool, or Featherless JSON mode) so every node
returns typed, parseable data instead of prose that has to be re-parsed
with regex. That's what makes automated benchmark scoring possible at all
— the eval harness diffs `MisconceptionClassification.misconception_id`
against a benchmark answer key, it doesn't read paragraphs.

Two design choices worth flagging:
- `ReasoningAnalysis.error_type` includes `EXECUTION` and `INCOMPLETE`
  states, not just conceptual-vs-not, because the spec is explicit that a
  wrong answer must not be auto-assumed conceptual — see Node 2's
  docstring.
- `ResponseEvaluation.status` adds a third `PARTIAL_PROGRESS` outcome
  beyond the spec's stated binary (`RESOLVED`/`PERSISTS`), documented as a
  deliberate deviation in that file's `VERSION_NOTES` — worth revisiting
  once real data shows whether the model uses that category sensibly.

## Model selection (not yet finalized)

Per the spec (section 16), model routing should only be adopted if
experiments justify it — this scaffolding is written model-agnostically
(prompts are plain text + a schema reference) so it can be pointed at
Gemini, Claude, or a Featherless-hosted open model without rewriting
anything. Each prompt file's docstring has a *recommended* model with a
one-line rationale (e.g. Reasoning Analyzer needs real step verification →
stronger model; Input Parser is pure structuring → cheap/fast model). These
are hypotheses to test in the ablation study (section 15 of the spec, plan
in `docs/ablation.md` once written), not conclusions.

## Status vs. the 22-step plan

| # | Step | Status |
|---|------|--------|
| 1 | Misconception taxonomy | ✅ `taxonomy/misconception_taxonomy.py` |
| 2 | 30 benchmark cases | ✅ `benchmark/cases.py` → `benchmark/cases.csv` |
| 3 | Single-prompt baseline | ✅ done — 26/30 (86.7%) exact-match diagnosis accuracy, see `results/baseline_results.csv` |
| 4 | Reasoning Analyzer | ✅ done — 27/30 (90.0%) error_type accuracy, see `results/analyzer_analysis.md` |
| 5 | Test 3 prompt versions | ✅ v1 (90.0%) → v2 (100.0%) confirmed, 0 regressions. **Final full pipeline v2: 28/30 = 93.3% exact-match (29/30 = 96.7% w/ legitimate alt) vs. baseline's 86.7%** — see `results/classifier_followup_analysis.md`. v3 not currently needed. |
| 6 | Misconception Classifier | ✅ done — 19/20 (95.0%) exact-match, 0 invented ids, see `results/classifier_analysis.md` |
| 7 | Adversarial Critic | ✅ done — 20/20 diagnosis_survives (100%, flagged as a v2 signal — see `results/critic_analysis.md`) |
| 8 | Diagnosis Selector | ✅ done — 19/20 (95.0%) final accuracy, 0 changes vs. Classifier this run. **Full pipeline (Nodes 1-6) vs. baseline comparison: see `results/pipeline_vs_baseline.md`** |
| 9 | Intervention Planner | ✅ prompt v1 written; ⏳ not yet run |
| 10 | Socratic Tutor | ✅ prompt v1 written; ⏳ not yet run |
| 11 | Response Evaluator | ✅ prompt v1 written; ⏳ not yet run |
| 12 | Adaptive loop | ❌ not started |
| 13 | Compare models | ❌ not started |
| 14 | Ablation tests | ❌ not started |
| 15 | Compute metrics | ❌ not started (harness scaffolding exists: `eval/ingest_baseline.py`) |
| 16 | Backend | ❌ not started (by design — spec says workflow first) |
| 17 | Frontend | ❌ not started (by design) |
| 18 | Final benchmark | ✅ diagnostic chain (Nodes 1-5) fully benchmarked, v1→v2 loop closed — see row 5 above. Intervention chain (Nodes 6-8) deferred, see row 9-11. |
| 19 | Workflow PNG | ✅ `diagram/workflow.png` — full node-by-node diagram with model/io/purpose/measured-stat per box, adaptive loop, Student Model store |
| 20 | Documentation | ✅ `docs/Bluetute_Documentation.docx` — 17-section report (architecture, taxonomy, v1→v2 methodology, full results, 3 worked samples, ablation, honest limitations, project story) |
| 21 | Video | ❌ not started — user-recorded, outside this repo's scope |
| 22 | Submission | ⏳ ready to package once video is recorded — code + docx + PNG are submission-ready now |

## Evaluation methodology

Every node was run against the benchmark through Google AI Studio (Gemini),
using each `prompts/0X_*.py` file's `build_prompt()` to generate the exact
system + user prompt sent to the model. Each node's structured JSON output
was fed forward as the next node's input — Analyzer → Classifier → Critic →
Diagnosis Selector — so the pipeline numbers reflect genuine end-to-end
chaining, not isolated per-node tests. `eval/generate_*_runbook.py` builds
each node's evaluation prompts from the live benchmark/previous-node data;
`eval/ingest_*.py` validates each response against its `schemas/models.py`
type, joins it with the benchmark answer key, and writes the scored
`results/*_results.csv` — that's the source of every number in
`docs/Bluetute_Documentation.docx`.

## What's left (honest, from the table above)

The diagnostic chain (Nodes 1–5: Input Parser → Reasoning Analyzer →
Misconception Classifier → Adversarial Critic → Diagnosis Selector) is
fully built, prompt-versioned, and benchmarked against the single-prompt
baseline with real data — that is this project's central, falsifiable
claim, and it's proven out in `docs/Bluetute_Documentation.docx`.

Not yet benchmarked, by deliberate scope choice for this submission:

1. **Nodes 6–8** (Intervention Planner, Socratic Tutor, Response
   Evaluator) — prompts are fully written (`prompts/05_*`, `06_*`, `07_*`)
   but not yet run against the benchmark. The same manual-AI-Studio +
   `eval/*` scoring pattern used for Nodes 1–5 applies directly.
2. **Backend/frontend** — intentionally deferred; the spec's own priority
   order is to measure the workflow before building a UI around it.
3. **Cross-model routing experiment** — running the Critic on a different
   model/provider than the Analyzer/Classifier, to test the "diversity"
   hypothesis in `prompts/03_adversarial_critic.py`'s docstring.
