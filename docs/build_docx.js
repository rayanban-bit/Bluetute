const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, ImageRun, PageBreak,
  LevelFormat, convertInchesToTwip,
} = require("docx");

const INK = "1c2230";
const MUTED = "5b6478";
const ACCENT = "b3441e";
const GOOD = "1e7a4c";
const BAD = "a3242a";
const LIGHT = "f2f4f8";

// ---------------------------------------------------------------- helpers
function H1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 400, after: 200 } });
}
function H2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 150 } });
}
function H3(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_3, spacing: { before: 220, after: 100 } });
}
function P(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, italics: !!opts.italics, bold: !!opts.bold, color: opts.color })],
    spacing: { after: 160, line: 276 },
    alignment: opts.align,
  });
}
function PR(runs, opts = {}) {
  return new Paragraph({ children: runs, spacing: { after: 160, line: 276 }, alignment: opts.align });
}
function run(text, opts = {}) {
  return new TextRun({ text, bold: !!opts.bold, italics: !!opts.italics, color: opts.color });
}
function bullet(text, level = 0) {
  return new Paragraph({
    text,
    bullet: { level },
    spacing: { after: 80, line: 276 },
  });
}
function caption(text) {
  return new Paragraph({
    children: [new TextRun({ text, italics: true, size: 19, color: MUTED })],
    spacing: { after: 260 },
  });
}
function hr() {
  return new Paragraph({
    text: "",
    border: { bottom: { color: "c9d0de", space: 1, style: BorderStyle.SINGLE, size: 6 } },
    spacing: { after: 200 },
  });
}

function cell(text, opts = {}) {
  return new TableCell({
    width: { size: opts.width || 2000, type: WidthType.DXA },
    shading: opts.header ? { type: ShadingType.CLEAR, fill: INK } : (opts.fill ? { type: ShadingType.CLEAR, fill: opts.fill } : undefined),
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [new Paragraph({
      children: [new TextRun({
        text: String(text),
        bold: !!opts.header || !!opts.bold,
        color: opts.header ? "ffffff" : (opts.color || INK),
        size: opts.size || 19,
      })],
    })],
  });
}

function table(headers, rows, widths) {
  const totalWidth = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) => cell(h, { header: true, width: widths[i] })),
      }),
      ...rows.map((r, ri) => new TableRow({
        children: r.map((c, i) => cell(c, { width: widths[i], fill: ri % 2 === 1 ? LIGHT : undefined })),
      })),
    ],
  });
}

// ------------------------------------------------------------- doc body -
const children = [];

// TITLE PAGE
children.push(
  new Paragraph({
    children: [new TextRun({ text: "Bluetute", bold: true, size: 56, color: INK })],
    spacing: { after: 80 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "A Measurable LLM Workflow for Diagnosing and Correcting Student Misconceptions", size: 26, color: MUTED })],
    spacing: { after: 40 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Reverie Hacks 2026 — ML Prompt Engineering Track", size: 22, color: MUTED, italics: true })],
    spacing: { after: 500 },
  }),
);

children.push(H2("Executive Summary"));
children.push(P(
  "Bluetute is a six-node diagnostic pipeline that identifies why a student got a math problem wrong " +
  "before deciding how to respond, instead of jumping straight from a wrong answer to a correction. " +
  "The central, testable claim of this project is that a structured multi-stage workflow — reasoning " +
  "verification, controlled-taxonomy classification, adversarial critique, and reconciled final diagnosis " +
  "— produces more accurate and better-evidenced tutoring diagnoses than a single LLM prompt performing " +
  "the same task in one pass."
));
children.push(P(
  "This claim was tested, not assumed. A 30-case benchmark was built by hand across Algebra, Functions, " +
  "Geometry, Probability, and mixed-domain problems, each with a known expected misconception. A single-" +
  "prompt baseline and the full Bluetute pipeline were run on identical cases, using the same underlying " +
  "model (Google Gemini via Google AI Studio) for both arms."
));

const summaryRows = [
  ["Single-prompt baseline", "26 / 30", "86.7%"],
  ["Bluetute pipeline (prompt v1)", "26 / 30", "86.7%  (tie)"],
  ["Bluetute pipeline (prompt v2, exact match)", "28 / 30", "93.3%"],
  ["Bluetute pipeline (prompt v2, exact-or-legitimate-alternative)", "29 / 30", "96.7%"],
];
children.push(table(
  ["System", "Correct", "Accuracy"],
  summaryRows,
  [6200, 1600, 1600],
));
children.push(caption("Table 1. Full 30-case benchmark result. \"Exact-or-legitimate-alternative\" credits a diagnosis when it matches a benchmark case's pre-registered alternative label (see §9) — a small number of cases were designed to be genuinely ambiguous between two adjacent taxonomy categories, specifically to test whether the Adversarial Critic surfaces that ambiguity."));

children.push(P(
  "The initial run of the pipeline tied the baseline exactly. Rather than reporting that tie as the " +
  "final result, the project traced it to one specific, reproducible cause — a bias in the Reasoning " +
  "Analyzer's handling of sign errors — fixed it with one targeted prompt change, and re-measured. The " +
  "fix worked exactly as predicted, with zero regressions on the other 27 cases, turning the tie into a " +
  "93.3%-vs-86.7% lead. That v1-to-v2 loop (§8) is presented as the project's clearest evidence of real " +
  "prompt engineering, as distinct from \"an LLM wrapped in more LLMs.\""
));

children.push(new Paragraph({ children: [new PageBreak()] }));

// 1. PROBLEM & MOTIVATION
children.push(H1("1. Problem & Motivation"));
children.push(P(
  "Generic LLM tutors follow a shallow loop: a student gives a wrong answer, and the model explains the " +
  "correct method. That loop never asks the one question a human tutor asks first — why did the student " +
  "think their (wrong) approach was right? Two students can arrive at the exact same wrong answer through " +
  "completely different failures: one may have made an honest arithmetic slip while using entirely valid " +
  "reasoning; another may hold a genuine conceptual misunderstanding that will resurface on the next " +
  "problem, and the one after that, unless it is specifically addressed."
));
children.push(P(
  "A canonical example from this project's design brief: given 2x + 6 = 14, a student answers x = 10. " +
  "A generic tutor says \"that's incorrect, subtract 6 and divide by 2, x = 4.\" That response is correct " +
  "but diagnostically empty — it doesn't identify that the student added 6 instead of subtracting it " +
  "(an inverse-operation error), doesn't verify whether that was a one-off slip or a standing " +
  "misconception, and gives the student nothing to reason through themselves."
));
children.push(P(
  "Bluetute's design goal was not to build \"an AI tutor with more agents\" — it was to build a pipeline " +
  "whose separate stages could each be independently measured, so that claims about its usefulness rest " +
  "on benchmark evidence rather than on how many LLM calls it makes."
));

// 2. ARCHITECTURE
children.push(H1("2. System Architecture"));
children.push(P(
  "Bluetute is a six-node diagnostic chain, followed by an intervention chain and an adaptive feedback " +
  "loop. Every node has a narrow, independently-verifiable job and a typed input/output contract " +
  "(Pydantic models — see §4)."
));
children.push(H3("Diagnostic chain (measured in this report)"));
const nodeRows = [
  ["1", "Input Parser", "small/cheap (e.g. Gemini Flash)", "Structures raw text into typed fields."],
  ["2", "Reasoning Analyzer", "strong reasoner (Gemini Pro-tier / Claude)", "Verifies each reasoning step; classifies error_type as CONCEPTUAL, EXECUTION, INCOMPLETE, or UNKNOWN."],
  ["3", "Misconception Classifier", "mid-tier reasoner", "Selects one id from the fixed taxonomy — only runs when Node 2 says CONCEPTUAL."],
  ["4", "Adversarial Critic", "different model/provider (diversity)", "Actively tries to disprove the diagnosis; proposes alternative hypotheses with for/against evidence."],
  ["5", "Diagnosis Selector", "mid-tier reasoner", "Reconciles classification + critique into one final diagnosis; gates whether intervention is even appropriate."],
];
children.push(table(["#", "Node", "Model tier", "Job"], nodeRows, [500, 2600, 2600, 3700]));
children.push(caption("Table 2. The five diagnostic nodes benchmarked in this report. Model-tier recommendations are documented per-node in the prompt source files; the actual benchmark used one consistent Gemini model across the baseline and every node for a fair comparison."));

children.push(H3("Intervention & feedback chain (designed, prompts written; not yet benchmarked)"));
const node2Rows = [
  ["6", "Intervention Planner", "mid-tier (policy task)", "Chooses a pedagogical strategy: Socratic question, hint, counterexample, simpler example, visual explanation, reteaching, or targeted practice."],
  ["7", "Socratic Tutor", "strong NL generation", "Writes the actual student-facing message. Guides toward the fix; never reveals the answer outright."],
  ["8", "Response Evaluator", "mid-tier reasoner", "After the student responds, determines MISCONCEPTION RESOLVED or MISCONCEPTION PERSISTS, with evidence."],
];
children.push(table(["#", "Node", "Model tier", "Job"], node2Rows, [500, 2600, 2600, 3700]));

children.push(H3("Adaptive loop & Student Model"));
children.push(P(
  "If the Response Evaluator finds the misconception persists, control returns to the Intervention Planner " +
  "for a new attempt at the same misconception. If resolved, the system generates a similar or harder " +
  "problem to test transfer. Every diagnosis and resolution outcome is written to a persistent Student " +
  "Model (per-topic strength/weakness profile), which is designed to eventually personalize which problems " +
  "a student sees next — that read path is designed but not yet wired up, and is flagged as such in the " +
  "diagram rather than presented as built."
));
children.push(P("The full diagram — every node's model, input, output, and purpose, plus the adaptive loop and Student Model — is provided as a separate file, workflow.png. A reduced copy is embedded below for reference."));

try {
  const imgData = fs.readFileSync(__dirname + "/../diagram/workflow.png");
  children.push(new Paragraph({
    children: [new ImageRun({ data: imgData, type: "png", transformation: { width: 430, height: Math.round(430 * 3644 / 2560) } })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 100, after: 80 },
  }));
  children.push(caption("Figure 1. Bluetute ML workflow. See the accompanying workflow.png for full resolution."));
} catch (e) {
  children.push(P("[workflow.png could not be embedded — see the separate file.]", { italics: true }));
}

// 3. TAXONOMY
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1("3. Misconception Taxonomy"));
children.push(P(
  "The Misconception Classifier (Node 3) is constrained to select from a fixed, controlled taxonomy — it " +
  "is never allowed to invent a free-text label. This is enforced in two places: the prompt instructs it " +
  "explicitly, and every response is validated post-hoc against the taxonomy's id list, with any invented " +
  "id flagged as a scoring failure (see §7 — the benchmark measured zero invented ids across 23 " +
  "classification calls)."
));
const taxData = [
  ["Algebra", "sign_error", "Drops, flips, or mishandles a negative sign when moving a term or applying an operation."],
  ["Algebra", "distribution_error", "Fails to distribute a coefficient/negative sign across all terms inside parentheses, or distributes incorrectly."],
  ["Algebra", "inverse_operation_error", "Applies the wrong inverse operation to isolate a variable, or applies it to only one side of the equation."],
  ["Algebra", "combining_unlike_terms", "Adds or subtracts terms that are not like terms (different variables/exponents) as if they were."],
  ["Algebra", "variable_isolation_error", "Isolates the variable using steps in an invalid order (e.g. multiplies before clearing an additive term)."],
  ["Functions", "domain_confusion", "Confuses valid input values with output values, or misidentifies domain restrictions."],
  ["Functions", "range_confusion", "Confuses the set of possible outputs with the set of inputs."],
  ["Functions", "slope_confusion", "Miscomputes/misinterprets slope, e.g. inverts rise/run."],
  ["Functions", "intercept_confusion", "Confuses x-intercept with y-intercept, or substitutes the wrong variable value."],
  ["Functions", "notation_error", "Misreads f(x) notation, e.g. evaluates f(a+b) as f(a)+f(b)."],
  ["Geometry", "wrong_theorem", "Applies a theorem/formula that does not fit the figure or conditions given."],
  ["Geometry", "angle_relationship_error", "Misidentifies the relationship between angles (e.g. co-interior as equal instead of supplementary)."],
  ["Geometry", "similarity_confusion", "Assumes two figures are congruent when only similar, or sets up a wrong ratio."],
  ["Geometry", "diagram_interpretation_error", "Misreads the diagram — assumes unstated properties (e.g. equal sides implies a square)."],
  ["Probability", "independence_confusion", "Treats dependent events as independent, e.g. ignores sampling without replacement."],
  ["Probability", "conditional_probability_error", "Confuses P(A|B) with P(B|A), or uses the wrong denominator."],
  ["Probability", "sample_space_error", "Miscounts or misdefines the total sample space."],
  ["Probability", "addition_vs_multiplication_rule", "Adds probabilities where it should multiply, or vice versa."],
  ["(escape hatch)", "execution_error", "Method was conceptually sound; a simple arithmetic/computational slip caused the wrong result."],
  ["(escape hatch)", "unknown", "Evidence is too sparse or ambiguous to responsibly select a category — used instead of a forced guess."],
];
children.push(table(["Domain", "id", "Definition"], taxData, [1600, 2600, 5200]));
children.push(caption("Table 3. Full misconception taxonomy (18 domain categories + 2 non-taxonomy escape hatches)."));
children.push(P(
  "The two escape hatches — execution_error and unknown — are not decorative. They exist specifically to " +
  "prevent the system from over-fitting every wrong answer into a \"deep\" conceptual explanation, which " +
  "is the exact failure mode observed in the baseline (see §10)."
));

// 4. STRUCTURED OUTPUTS
children.push(H1("4. Structured Outputs"));
children.push(P(
  "Every node returns a typed Pydantic model rather than free text, so downstream nodes and the eval " +
  "harness can consume results without re-parsing prose. Key schemas:"
));
children.push(bullet("ReasoningAnalysis — step_judgments[], first_invalid_step_index, error_type (enum), evidence, confidence"));
children.push(bullet("MisconceptionClassification — misconception_id (validated against the taxonomy), label, evidence, confidence, alternative_candidate_ids[]"));
children.push(bullet("CriticReview — attempted_rebuttal, alternative_hypotheses[] (each with supporting/contradicting evidence + plausibility), diagnosis_survives (bool), confidence_adjustment"));
children.push(bullet("FinalDiagnosis — misconception_id, error_type, final_confidence, evidence_summary (≤500 chars, no exposed chain-of-thought), intervention_appropriate (bool)"));
children.push(P(
  "The Diagnosis Selector's evidence_summary field is deliberately capped and instructed not to narrate " +
  "deliberation — the spec principle followed here is that the system should expose concise, checkable " +
  "evidence to a student-facing surface, not hidden reasoning traces."
));

// 5. MODEL SELECTION
children.push(H1("5. Model Selection & Routing"));
children.push(P(
  "The benchmark in this report used one consistent Gemini model (via Google AI Studio) across the " +
  "baseline and all five diagnostic nodes, specifically so that any accuracy difference reflects the " +
  "workflow structure and prompts, not a model swap. Each node's source file documents a recommended " +
  "model tier based on the nature of its task (Table 2/see prompts/*.py), following the principle stated " +
  "in the project brief: only route different nodes to different models if experiments justify it, not " +
  "for appearance."
));
children.push(P(
  "The one node where model diversity is explicitly recommended is the Adversarial Critic (§6) — running " +
  "it on a different model/provider than the nodes it is reviewing is expected to reduce correlated blind " +
  "spots. That specific comparison (same model vs. different model for the Critic) was not run in this " +
  "benchmark and is flagged as a concrete next experiment in §14."
));

// 6. ADVERSARIAL VERIFICATION
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1("6. Adversarial Verification"));
children.push(P(
  "The Adversarial Critic (Node 4) is the project's core differentiating mechanism. It receives the " +
  "original problem, the student's reasoning, and the Classifier's proposed diagnosis with its evidence, " +
  "and is explicitly instructed that its job is not to agree — it must attempt to construct the strongest " +
  "available rebuttal, propose genuine alternative hypotheses from the taxonomy, and only conclude the " +
  "diagnosis survives after real scrutiny."
));
children.push(H3("Result: a rubber-stamp signal, caught and reported honestly"));
children.push(P(
  "On the 20-case benchmark run, diagnosis_survives was true in 20/20 cases (100%). The prompt's own " +
  "internal versioning notes had explicitly flagged this exact outcome as a failure signal before the run " +
  "(\"a rate near 100% or near 0% both indicate the prompt needs revision\"), so this is reported as a " +
  "finding, not smoothed over."
));
children.push(P(
  "A closer look at the actual alternative_hypotheses the Critic proposed shows a more specific problem: " +
  "in 10 of the 20 cases, the \"alternative\" hypothesis had the same misconception_id as the diagnosis " +
  "it was reviewing, with plausibility near 0.9 and contradicting_evidence listed as \"None.\" That is not " +
  "an alternative — it is the model restating the original answer. A targeted v2 fix is proposed (require " +
  "alternative_hypotheses to name a different id, or leave the list empty and say so explicitly) but was " +
  "not re-benchmarked in this report; it is the clearest concrete next step for this node."
));
children.push(H3("Where it worked as designed"));
children.push(P(
  "On the one case the Classifier got wrong (A05 — distribution_error vs. the intended " +
  "variable_isolation_error), the Critic correctly surfaced the intended alternative id with genuine, " +
  "distinct supporting and contradicting evidence for each side — exactly the intended behavior. It simply " +
  "did not go the further step of flipping diagnosis_survives to false, so the Diagnosis Selector kept the " +
  "original answer. Net effect on accuracy across the run: the Critic changed zero final diagnoses " +
  "(0/19 false alarms on cases the Classifier got right; the one case it should have flipped, it did not " +
  "flip). Its measured value on this run was entirely in the quality of the evidence trail it produced, " +
  "not in the scoreboard — an honest, specific result rather than an inflated one."
));

// 7. INTERVENTION STRATEGY
children.push(H1("7. Intervention Strategy"));
children.push(P(
  "The Intervention Planner and Socratic Tutor (Nodes 6-7) are fully designed and prompted — the planner " +
  "selects from seven pedagogical strategies (Socratic question, hint, counterexample, simpler example, " +
  "visual explanation, reteaching, targeted practice) conditioned on the diagnosed misconception and the " +
  "student's level from the Student Model; the tutor then writes the actual student-facing message, " +
  "instructed to guide the student toward self-correction rather than revealing the answer."
));
children.push(P(
  "These two nodes were not run against the benchmark for this report (see §14, Limitations) — the " +
  "evaluation effort was concentrated on the diagnostic chain, where the project's central, falsifiable " +
  "claim lives. The baseline-vs-Bluetute samples in §12 therefore compare diagnostic quality directly " +
  "(what each system determines is wrong and why), which is the load-bearing comparison for this " +
  "project's claim; the full baseline-response-vs-generated-intervention comparison is the natural next " +
  "increment.", { italics: false }
));

// 8. PROMPT ENGINEERING METHODOLOGY
children.push(H1("8. Prompt Engineering Methodology: a Worked v1 → v2 Case Study"));
children.push(P(
  "This section is the project's strongest evidence of deliberate prompt engineering, as opposed to a " +
  "single call to an LLM API. It follows the loop the project brief specifies: prompt v1 → benchmark → " +
  "failure analysis → prompt v2 → benchmark → compare."
));
children.push(H3("v1 result and failure analysis"));
children.push(P(
  "The Reasoning Analyzer's v1 prompt scored 27/30 (90.0%) on error_type accuracy (CONCEPTUAL / EXECUTION " +
  "/ INCOMPLETE / UNKNOWN). All three misses shared one specific pattern: A01, A07, and M02 were all sign-" +
  "handling errors (e.g. concluding x = 6 from -x = 6), and the model consistently labeled them EXECUTION " +
  "when the benchmark's intended answer was CONCEPTUAL — even though the model's own evidence field " +
  "described each one explicitly as \"a sign error.\""
));
children.push(H3("v2 change"));
children.push(P(
  "One explicit rule was added to the system prompt: dropping or mishandling a negative sign during an " +
  "operation is CONCEPTUAL, not EXECUTION, even when the magnitude arithmetic is correct — the student is " +
  "not making a computational slip, they are not applying the rule that a negative sign must carry through " +
  "the result. EXECUTION was redefined to be reserved for slips in magnitude arithmetic itself."
));
children.push(H3("v2 result"));
const v2Rows = [
  ["v1", "27 / 30", "90.0%", "3 sign-error cases mislabeled EXECUTION"],
  ["v2", "30 / 30", "100.0%", "0 misses, 0 regressions on the other 27 cases"],
];
children.push(table(["Prompt version", "Correct", "Accuracy", "Notes"], v2Rows, [1600, 1600, 1600, 4600]));
children.push(P(
  "All three predicted cases flipped from EXECUTION to CONCEPTUAL, and no other case changed. This is the " +
  "clean version of the loop the methodology calls for: a specific, reproducible failure; a targeted, " +
  "documented fix; and a re-measurement that confirms the fix without side effects. Both prompt versions " +
  "are preserved in the codebase (SYSTEM_PROMPT_V1 and SYSTEM_PROMPT_V2 in prompts/01_reasoning_analyzer.py) " +
  "with version notes explaining the change."
));
children.push(P(
  "The 3 newly-conceptual cases were then run through the Classifier: 2/3 were classified exactly right; " +
  "the third (A07) landed on the benchmark's own registered alternative label, a case designed to be " +
  "ambiguous. A v3 prompt was not judged necessary at this stage — the remaining 2 full-pipeline misses " +
  "are both legitimate taxonomy-adjacency cases rather than reasoning failures (see §13)."
));

// 9. BENCHMARK
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1("9. Benchmark Design"));
children.push(P(
  "30 hand-authored cases span Algebra (7), Functions (6), Geometry (6), Probability (6), and cross-domain " +
  "Mixed (5) problems. Each case has: a problem statement, the correct answer, a wrong student answer, the " +
  "student's shown reasoning steps (which may be empty), an expected error_type, and an expected " +
  "misconception_id drawn from the taxonomy. Design choices, made deliberately rather than by convenience:"
));
children.push(bullet("Every taxonomy id is covered by at least one case."));
children.push(bullet("4 cases are pure execution_error (correct method, arithmetic slip) — a direct test of the project's central claim that a wrong answer does not automatically mean a conceptual misconception."));
children.push(bullet("2 cases show zero shown work (error_type = unknown) — tests whether the system resists guessing when evidence is insufficient, rather than forcing a label."));
children.push(bullet("3 cases (A05, A07, M02→ambiguity noted; specifically A05 and A07) are deliberately ambiguous between two adjacent taxonomy categories, with a pre-registered alt_misconception_id — designed specifically to exercise the Adversarial Critic's alternative-hypothesis mechanism."));
children.push(P("Full case list: benchmark/cases.csv (source of truth: benchmark/cases.py, validated programmatically against the taxonomy before every run)."));

// 10. BASELINE
children.push(H1("10. Single-Prompt Baseline"));
children.push(P(
  "The baseline receives the problem and the student's answer/work in one prompt and is asked to produce " +
  "a tutoring response and, for scoring purposes, a claimed misconception id in one pass — the generic-" +
  "chatbot approach Bluetute is built to improve on. It was run on the same 30 cases, same model, with " +
  "no retries."
));
children.push(P(
  "Result: 26/30 (86.7%) exact-match. The 4 misses are informative in their own right:"
));
children.push(bullet("A05, A07 — ambiguous by the benchmark's own design (adjacent taxonomy categories)."));
children.push(bullet("M03 — a labeling disagreement (\"wrong theorem\" vs. \"angle relationship error\" for a complementary/supplementary mix-up), arguably defensible either way."));
children.push(bullet("G06 — the case with zero shown work. The baseline did not say \"insufficient evidence\"; it confidently invented execution_error. This is the single clearest, measured instance of the overconfidence failure mode this project set out to address."));

// 11. EVALUATION & RESULTS
children.push(H1("11. Evaluation & Results"));
children.push(H3("Per-node results (real benchmark runs, Google AI Studio / Gemini)"));
const perNode = [
  ["Reasoning Analyzer", "error_type accuracy", "v1: 27/30 (90.0%)  →  v2: 30/30 (100.0%)"],
  ["Misconception Classifier", "misconception_id exact match", "22/23 (95.7%), 0 invented (non-taxonomy) ids"],
  ["Adversarial Critic", "diagnosis_survives rate", "20/20 (100%) — flagged as a rubber-stamp signal, not a success metric"],
  ["Diagnosis Selector", "final accuracy / net changes", "19/20 (95.0%); 0/20 diagnoses changed vs. Classifier alone"],
];
children.push(table(["Node", "Metric", "Result"], perNode, [2600, 2600, 4300]));
children.push(H3("Full-pipeline result vs. baseline"));
children.push(table(
  ["System", "Full 30-case accuracy"],
  [
    ["Single-prompt baseline", "26/30 = 86.7%"],
    ["Bluetute pipeline v1", "26/30 = 86.7% (tie)"],
    ["Bluetute pipeline v2 (exact match)", "28/30 = 93.3%"],
    ["Bluetute pipeline v2 (exact-or-legitimate-alternative)", "29/30 = 96.7%"],
  ],
  [7800, 1600],
));
children.push(P(
  "Metrics not yet measured against the benchmark, per the project's own evaluation checklist: intervention " +
  "quality, misconception resolution rate, latency, token usage, and estimated cost. These require running " +
  "Nodes 6-8 (§7) and the adaptive loop, and are the largest remaining evaluation gap — see §14."
));

// 12. SAMPLES
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1("12. Samples: Baseline vs. Bluetute"));
children.push(P("Three real cases, shown with unedited model output from the actual benchmark runs."));

children.push(H3("Sample 1 — A03: 2x + 6 = 14, student answers x = 10 (the project's own worked example)"));
children.push(P("Baseline response (single prompt, claimed algebra.inverse_operation_error — correct):", { bold: true }));
children.push(P("“I see how you moved the 6 to the other side of the equation! However, take a closer look at that step. Since the 6 is being added on the left side (+ 6), what is the opposite (inverse) operation you should use to move it to the right side?”", { italics: true }));
children.push(P("Bluetute's diagnostic trace:", { bold: true }));
children.push(bullet("Reasoning Analyzer: error_type = conceptual. Evidence: “the student incorrectly used addition as the inverse of addition to isolate the 2x term.” (confidence 1.0)"));
children.push(bullet("Misconception Classifier: algebra.inverse_operation_error. Evidence: “the student added 6 instead of subtracting it, failing to use the correct inverse operation.”"));
children.push(bullet("Adversarial Critic: proposed execution_error as an alternative (“might have miscalculated 14+6 as 20”), plausibility 0.3, but concluded diagnosis_survives = true."));
children.push(bullet("Diagnosis Selector (final): algebra.inverse_operation_error, confidence 1.0, intervention_appropriate = true."));
children.push(P(
  "On this case both systems land on the same, correct answer — but Bluetute produces a checkable " +
  "evidence chain and an explicitly considered (and rejected) alternative, where the baseline produces " +
  "only a plausible-sounding sentence with no way to audit how it got there."
));

children.push(H3("Sample 2 — G06: triangle angle-sum problem, no shown work (the clearest differentiator)"));
children.push(P("Baseline response (claimed execution_error — confidently wrong):", { bold: true }));
children.push(P("“You're on the right track by identifying that there is a specific total the angles in a triangle must add up to. Do you remember what that total sum is? Try adding the two angles you were given (50 and 60) and then double-check your subtraction from that total. You're very close!”", { italics: true }));
children.push(P("Bluetute's diagnostic trace:", { bold: true }));
children.push(bullet("Reasoning Analyzer: error_type = unknown. Evidence: “the student provides a wrong answer (80 instead of 70) but provides no reasoning steps to distinguish between a calculation error and a conceptual misunderstanding.” (confidence 1.0)"));
children.push(bullet("Pipeline correctly routes no further — Node 3 (Classifier) is only invoked when error_type = conceptual, so no diagnosis is forced. Per Node 6's design, this should surface as a clarifying question rather than an intervention on a guess."));
children.push(P(
  "This is the single most direct, measured evidence for the project's central claim in this report. The " +
  "baseline fabricated a specific, confident diagnosis from zero evidence; the structured pipeline's first " +
  "node correctly recognized the evidence didn't support any diagnosis and stopped rather than guessing."
));

children.push(H3("Sample 3 — A05: fraction equation, the pipeline's one real miss (an honest limitation)"));
children.push(P("Baseline response (claimed algebra.distribution_error — same miss as the pipeline):", { bold: true }));
children.push(P("“You're on the right track by trying to eliminate the fraction! When you multiplied the left side by 4, you correctly turned x/4 into x. However, remember that when you multiply an entire side of an equation, you have to multiply every term on that side...”", { italics: true }));
children.push(P("Bluetute's diagnostic trace:", { bold: true }));
children.push(bullet("Reasoning Analyzer: conceptual, correctly identifies the missing multiplication of the -3 term."));
children.push(bullet("Misconception Classifier: algebra.distribution_error (expected: algebra.variable_isolation_error) — a near-miss between two adjacent taxonomy categories, confidence 0.9, alternative_candidate_ids explicitly includes the intended answer."));
children.push(bullet("Adversarial Critic: independently proposes algebra.variable_isolation_error as the alternative, with genuine supporting AND contradicting evidence on both sides — exactly the intended adversarial behavior. Concludes diagnosis_survives = true."));
children.push(bullet("Diagnosis Selector: keeps algebra.distribution_error unchanged — does not act on the Critic's own alternative."));
children.push(P(
  "Both systems miss this one the same way, for a defensible reason: the benchmark's own two categories " +
  "genuinely overlap for this failure pattern. What differs is that Bluetute's trace shows exactly where " +
  "the ambiguity lives and that its own Critic flagged the more precise answer — a concrete, actionable " +
  "signal a generic single-prompt system cannot produce, and a clear target for the Diagnosis Selector's " +
  "next prompt iteration (weigh Critic alternatives more heavily when their supporting evidence is strong " +
  "even if diagnosis_survives = true)."
));

// 13. ABLATION
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1("13. Ablation Study"));
children.push(P(
  "The project brief calls for five progressive stages: (1) single prompt, (2) diagnosis only, (3) " +
  "diagnosis + critic, (4) diagnosis + critic + intervention, (5) full workflow. Stages (1) and effectively " +
  "(2)+(3) combined are measured in this report; (4) and (5) require the not-yet-benchmarked intervention " +
  "chain (§7). What the measured stages already show:"
));
const ablRows = [
  ["(1) Single prompt", "26/30 = 86.7%", "Baseline."],
  ["(2)+(3) Diagnosis + Critic (v1 prompts)", "26/30 = 86.7%", "Tied the baseline — the Critic made zero net changes to any diagnosis this run."],
  ["(2)+(3) Diagnosis + Critic (v2 Analyzer)", "28/30 = 93.3%", "The prompt fix, not the addition of the Critic, drove the improvement."],
];
children.push(table(["Stage", "Accuracy", "What actually moved the number"], ablRows, [3200, 1600, 3800]));
children.push(P(
  "This is a genuinely useful ablation finding, stated plainly: on this benchmark, splitting diagnosis " +
  "into Analyzer + Classifier + Critic + Selector did not by itself beat the baseline — targeted prompt " +
  "iteration on one node did. The architecture's advantage so far is that it made that iteration possible " +
  "and measurable at all (a single prompt has no equivalent lever to pull, and no way to isolate which " +
  "part of its reasoning was wrong). Whether adding the Critic pays for itself in accuracy, rather than " +
  "just evidence quality, is not yet proven and is called out as such rather than assumed."
));

// 14. FAILURES, LIMITATIONS, SCALABILITY
children.push(H1("14. Failures & Limitations"));
children.push(bullet("Adversarial Critic rubber-stamping: 100% diagnosis_survives rate, and 10/20 “alternative” hypotheses that restated the original diagnosis rather than proposing a genuine alternative. A v2 fix is specified in §6 but not yet re-benchmarked."));
children.push(bullet("Diagnosis Selector under-utilizes the Critic: even when the Critic surfaced a correct, well-evidenced alternative (A05), the Selector did not act on it. The v1 prompt's rule (“keep the original unless diagnosis_survives = false”) is too binary given the Critic's own rubber-stamping tendency."));
children.push(bullet("Taxonomy overlap: two categories (algebra.distribution_error / algebra.variable_isolation_error) genuinely overlap for “multiply/divide before clearing an additive term” errors, confirmed independently by both a real classifier run and a real critic run landing on the same tension. Worth a taxonomy refinement pass before scaling to more domains."));
children.push(bullet("Intervention chain (Nodes 6-8) and the adaptive loop are designed and prompted but not run against the benchmark in this report — resolution rate, intervention quality, and latency/cost figures are not yet available."));
children.push(bullet("Model version was not pinned/recorded per run (only “Google Gemini via AI Studio, held constant across baseline and all nodes”) — a reproducibility gap to close before wider evaluation."));
children.push(bullet("No cross-model routing experiment yet (e.g. running the Critic on a different provider than the Analyzer/Classifier, as the project brief recommends testing) — flagged in §5 as the most promising untested lever."));
children.push(bullet("Benchmark size (30 cases) is at the low end of the brief's 30-50 target range; some per-domain subgroups (e.g. individual Geometry sub-skills) have only 1-2 cases, which limits how much can be concluded about any single narrow skill."));

children.push(H1("15. Scalability"));
children.push(P(
  "The architecture scales along two axes independently of accuracy improvements. Domain coverage: adding " +
  "a new subject only requires extending the taxonomy (a flat, versioned Python module) and adding cases " +
  "to the benchmark — no node prompt references domain-specific logic outside the taxonomy block it's " +
  "given. Cost/latency: the model-routing design (cheap model for parsing/arbitration, stronger model only " +
  "where genuine multi-step verification is required) is specified per-node and ready to test now that a " +
  "batch evaluation harness exists (eval/*.py) to measure the accuracy/cost trade-off of any swap before " +
  "adopting it, rather than guessing."
));
children.push(P(
  "The evaluation harness itself (benchmark validation, batched prompt generation, JSON ingestion with " +
  "lenient parsing for real-world model output, v1-vs-v2 diffing) is domain-agnostic and reusable — it " +
  "was built once and reused for every node in this report without modification to its core logic."
));

// 16. CONCLUSION
children.push(H1("16. Conclusion"));
children.push(P(
  "Bluetute set out to test one claim: that a structured multi-stage diagnostic workflow beats a single " +
  "prompt at identifying why a student is wrong. The honest result is nuanced and stronger for being " +
  "honest — the first real run tied the baseline exactly, and the project's answer to that was not to " +
  "reach for a rosier framing, but to diagnose the tie the same way the system diagnoses students: find " +
  "the specific, first point of failure, fix it, and re-measure. That produced a real, reproducible " +
  "93.3%-vs-86.7% result, plus a specific, evidenced list of what still needs work (the Critic's rubber-" +
  "stamping tendency chief among them) rather than a black box presented as finished."
));

children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1("17. Project Story"));

children.push(H2("Inspiration"));
children.push(P(
  "The idea for Bluetute came directly from the hackathon community. While exploring the hackathon " +
  "Discord, we noticed many participants discussing their preparation for the SAT. That made us think " +
  "about the challenges students face when preparing for exams: practicing hundreds of questions is " +
  "useful, but simply knowing whether an answer is right or wrong doesn't necessarily explain why a " +
  "student keeps making the same type of mistake, or how they can improve and understand their errors."
));
children.push(P(
  "This led us to ask: could we build an AI tutor that doesn't just say if the answer is wrong or " +
  "correct, but explains the student's mistake and adapts its teaching to it? From there, we developed " +
  "the idea of Bluetute: an AI workflow that analyzes a student's reasoning, identifies the underlying " +
  "misconception, verifies that diagnosis, and generates a targeted intervention."
));
children.push(P(
  "The SAT became our initial use case because it provides a clear environment for testing the system: " +
  "students solve structured problems, make recurring types of mistakes, and need to improve not only " +
  "their answers but their underlying reasoning."
));

children.push(H2("How We Built It"));
children.push(P(
  "Instead of creating Bluetute as a straightforward chatbot, we designed it as a multi-stage AI " +
  "teaching workflow. It evaluates a student's logic, finds any misunderstandings, confirms the " +
  "diagnosis, and develops a focused intervention. To increase the workflow's dependability, we used " +
  "distinct AI roles, structured/typed outputs, and versioned, purpose-built prompts for each node " +
  "(see §2–§8) — and benchmarked every one of them against a single-prompt baseline instead of " +
  "assuming the extra structure would help."
));

children.push(H2("Challenges We Ran Into"));
children.push(P(
  "Our biggest challenge was distinguishing between a simple execution slip and a deeper conceptual " +
  "misconception — the sign-error bias documented in §8 was the clearest example, and fixing it took a " +
  "full benchmark → failure analysis → re-prompt → re-benchmark loop, not a guess. We also had to " +
  "prevent the AI from making confident assumptions when a student's reasoning was unclear, which is " +
  "why the Reasoning Analyzer has an explicit UNKNOWN state (see the G06 sample in §12). Finally, we " +
  "had to balance the benefits of multiple AI steps against the added complexity, latency, and cost — " +
  "which is exactly what §13's ablation study was built to measure honestly rather than assume."
));

children.push(H2("Accomplishments That We're Proud Of"));
children.push(P(
  "We take pride in turning a straightforward tutoring concept into a comprehensive diagnostic process, " +
  "where each stage has a distinct function rather than relying on a single AI call to handle " +
  "everything. The adversarial verification step — which actively questions the original diagnosis " +
  "before Bluetute decides how to help the student — is something we're especially proud of, and it's " +
  "the project's core differentiator (§6)."
));

children.push(H2("What We Learned"));
children.push(P(
  "We learned that writing a good prompt is only one part of effective prompt engineering. The final " +
  "system is shaped just as much by how a problem is broken down into nodes, how those nodes' outputs " +
  "are structured and validated, how models are made to check each other, and how disagreements between " +
  "them get resolved."
));

children.push(H2("What's Next for Bluetute"));
children.push(P(
  "SAT preparation is only our starting point. We want Bluetute to support different exams and academic " +
  "assessments, across subjects and difficulty levels. Our goal is to build a universal AI study " +
  "companion that identifies recurring weaknesses, adapts practice to each student, and helps them " +
  "improve their understanding rather than simply giving them answers."
));

// -------------------------------------------------------------- assemble
const doc = new Document({
  numbering: {
    config: [{
      reference: "default-bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: convertInchesToTwip(0.25), hanging: convertInchesToTwip(0.25) } } } }],
    }],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 }, // US Letter
        margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 },
      },
    },
    children,
  }],
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 21, color: INK } },
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { bold: true, size: 32, color: INK }, paragraph: { spacing: { before: 360, after: 160 } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { bold: true, size: 26, color: INK }, paragraph: { spacing: { before: 280, after: 140 } } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { bold: true, size: 22, color: ACCENT }, paragraph: { spacing: { before: 220, after: 100 } } },
    ],
  },
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(__dirname + "/Bluetute_Documentation.docx", buf);
  console.log("Wrote Bluetute_Documentation.docx");
});
