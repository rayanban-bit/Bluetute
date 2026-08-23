"""
Generates diagram/workflow.html (self-contained inline-SVG page) — the
source for the ML Workflow PNG deliverable. Rendered to PNG separately via
Playwright (diagram/render_png.py).
"""

from pathlib import Path

W = 1180

INK = "#1c2230"
MUTED = "#5b6478"
LINE = "#8a92a6"
BG = "#ffffff"
CARD = "#f5f7fb"
CARD_BORDER = "#c9d0de"
HUMAN = "#eef2ff"
HUMAN_BORDER = "#7c86d6"
ACCENT = "#b3441e"        # the Critic — the differentiating node
ACCENT_BG = "#fdf1ea"
GOOD = "#1e7a4c"
GOOD_BG = "#eaf6ef"
STORE = "#f2ecff"
STORE_BORDER = "#8a6fd6"

MAIN_X = 130
MAIN_W = 620
SIDE_X = 830
SIDE_W = 280

parts = []


def rect(x, y, w, h, fill, stroke, rx=10, sw=1.6, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def text(x, y, s, size=13, weight="400", fill=INK, anchor="start", family="ui-monospace, Menlo, Consolas, monospace"):
    esc = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
                 f'fill="{fill}" text-anchor="{anchor}" font-family="{family}">{esc}</text>')


def sans(x, y, s, size=13, weight="400", fill=INK, anchor="start"):
    text(x, y, s, size, weight, fill, anchor,
         family="-apple-system, Segoe UI, Helvetica, Arial, sans-serif")


def arrow_down(x, y1, y2, color=LINE, sw=2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    parts.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2 - 12}" '
                 f'stroke="{color}" stroke-width="{sw}"{d} marker-end="url(#arrow)"/>')


def arrow_path(d_attr, color=LINE, sw=2, dash=None, marker=True):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = ' marker-end="url(#arrow)"' if marker else ""
    parts.append(f'<path d="{d_attr}" fill="none" stroke="{color}" stroke-width="{sw}"{d}{m}/>')


def label_on_line(x, y, s, size=11.5, fill=MUTED, anchor="middle", bg=True):
    if bg:
        w = len(s) * size * 0.62 + 12
        parts.append(f'<rect x="{x - w/2}" y="{y - size - 2}" width="{w}" height="{size + 8}" '
                     f'fill="{BG}" opacity="0.92"/>')
    sans(x, y, s, size=size, fill=fill, anchor=anchor, weight="600")


# ---------------------------------------------------------------- defs ---
parts.append(f'''<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/>
  </marker>
  <marker id="arrowAccent" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="{ACCENT}"/>
  </marker>
  <marker id="arrowStore" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" fill="{STORE_BORDER}"/>
  </marker>
</defs>''')


def node_box(y, h, title, model, io_line, purpose, measured=None, fill=CARD, border=CARD_BORDER, title_color=INK):
    x, w = MAIN_X, MAIN_W
    rect(x, y, w, h, fill, border)
    sans(x + 20, y + 26, title, size=16, weight="700", fill=title_color)
    text(x + 20, y + 46, f"model: {model}", size=11.5, fill=MUTED)
    text(x + 20, y + 64, io_line, size=11.5, fill=MUTED)
    sans(x + 20, y + 86, purpose, size=12.5, fill=INK)
    if measured:
        sans(x + w - 20, y + h - 14, measured, size=12, weight="700", fill=GOOD, anchor="end")
    return y, y + h


# --------------------------------------------------------------- layout --
y = 30

# Human input 1
h = 64
rect(MAIN_X, y, MAIN_W, h, HUMAN, HUMAN_BORDER, rx=32)
sans(MAIN_X + MAIN_W/2, y + 28, "HUMAN INPUT", size=13, weight="700", fill="#33399e", anchor="middle")
sans(MAIN_X + MAIN_W/2, y + 47, "problem statement + student's answer + shown work (+ prior attempts)",
     size=11.5, fill="#33399e", anchor="middle")
y_top1 = y
y += h
arrow_down(MAIN_X + MAIN_W/2, y, y + 46)
y += 46

# Node 1 — Input Parser
h = 96
b0, b1 = node_box(y, h, "1 · Input Parser", "small/cheap (e.g. Gemini Flash)",
                   "in: raw text  ->  out: ParsedInput (typed fields)",
                   "Normalizes problem, answer, reasoning steps, prior attempts into structured data.")
y = b1
arrow_down(MAIN_X + MAIN_W/2, y, y + 46)
y += 46

# Node 2 — Reasoning Analyzer
h = 112
b0, b1 = node_box(y, h, "2 · Reasoning Analyzer", "strong reasoner (Gemini Pro-tier / Claude)",
                   "in: ParsedInput  ->  out: ReasoningAnalysis",
                   "Verifies each step; decides CONCEPTUAL vs EXECUTION vs INCOMPLETE vs UNKNOWN.",
                   measured="benchmarked: v1 90.0% -> v2 100.0% (30/30)")
analyzer_y = (b0, b1)
y = b1
arrow_down(MAIN_X + MAIN_W/2, y, y + 40)
label_on_line(MAIN_X + MAIN_W/2, y + 24, "if error_type == conceptual")
y += 40

# Node 3 — Misconception Classifier
h = 112
b0, b1 = node_box(y, h, "3 · Misconception Classifier", "mid-tier reasoner",
                   "in: ReasoningAnalysis  ->  out: MisconceptionClassification",
                   "Selects one id from the fixed taxonomy below — never invents a label.",
                   measured="benchmarked: 22/23 = 95.7% exact-match")
y = b1
arrow_down(MAIN_X + MAIN_W/2, y, y + 46)
y += 46

# Node 4 — Adversarial Critic (accent)
h = 128
b0, b1 = node_box(y, h, "4 · Adversarial Critic", "DIFFERENT model/provider (diversity)",
                   "in: classification + evidence  ->  out: CriticReview",
                   "Actively tries to DISPROVE the diagnosis; proposes alternative hypotheses.",
                   measured="benchmarked: 100% survive (v1 signal: too agreeable)",
                   fill=ACCENT_BG, border=ACCENT, title_color=ACCENT)
y = b1
arrow_down(MAIN_X + MAIN_W/2, y, y + 46, color=ACCENT)
y += 46

# Node 5 — Diagnosis Selector
h = 112
b0, b1 = node_box(y, h, "5 · Diagnosis Selector", "mid-tier reasoner",
                   "in: classification + critic review  ->  out: FinalDiagnosis",
                   "Reconciles both into ONE final diagnosis; gates whether to intervene at all.",
                   measured="benchmarked: 19/20 = 95.0% final accuracy")
selector_y = (b0, b1)
y = b1
arrow_down(MAIN_X + MAIN_W/2, y, y + 40)
label_on_line(MAIN_X + MAIN_W/2, y + 24, "if intervention_appropriate")
y += 40

# Node 6 — Intervention Planner
h = 96
b0, b1 = node_box(y, h, "6 · Intervention Planner", "mid-tier (policy/decision task)",
                   "in: FinalDiagnosis + student level  ->  out: InterventionPlan",
                   "Chooses a pedagogical strategy: Socratic question, hint, counterexample, ...")
planner_y = (b0, b1)
y = b1
arrow_down(MAIN_X + MAIN_W/2, y, y + 46)
y += 46

# Node 7 — Socratic Tutor
h = 96
b0, b1 = node_box(y, h, "7 · Socratic Tutor", "strong NL generation quality",
                   "in: InterventionPlan  ->  out: student-facing message",
                   "Writes the message shown to the student — guides toward the fix, never reveals it.")
y = b1
arrow_down(MAIN_X + MAIN_W/2, y, y + 46)
y += 46

# Human input 2 (student response)
h = 56
rect(MAIN_X, y, MAIN_W, h, HUMAN, HUMAN_BORDER, rx=28)
sans(MAIN_X + MAIN_W/2, y + 24, "HUMAN INPUT", size=13, weight="700", fill="#33399e", anchor="middle")
sans(MAIN_X + MAIN_W/2, y + 42, "student's response to the intervention", size=11.5, fill="#33399e", anchor="middle")
y += h
arrow_down(MAIN_X + MAIN_W/2, y, y + 46)
y += 46

# Node 8 — Response Evaluator
h = 112
b0, b1 = node_box(y, h, "8 · Response Evaluator", "mid-tier reasoner",
                   "in: new response + FinalDiagnosis  ->  out: RESOLVED / PERSISTS",
                   "Checks whether the misconception was actually corrected, with evidence.")
evaluator_y = (b0, b1)
y = b1

# Branches
branch_y = y + 60
sans(MAIN_X + MAIN_W/2, branch_y - 30, "ADAPTIVE LOOP", size=12, weight="700", fill=MUTED, anchor="middle")

# left branch -> loop back to planner (persists)
loop_x = MAIN_X - 55
arrow_path(f"M {MAIN_X+40} {evaluator_y[1]+18} C {loop_x} {evaluator_y[1]+18}, {loop_x} {planner_y[0]+48}, {MAIN_X} {planner_y[0]+48}")
sans(20, (evaluator_y[1] + planner_y[0]) / 2 - 8, "PERSISTS", size=11.5, weight="700", fill=MUTED, anchor="start")
sans(20, (evaluator_y[1] + planner_y[0]) / 2 + 8, "-> new intervention", size=11.5, weight="700", fill=MUTED, anchor="start")

# right branch -> resolved outcome box
h2 = 84
rect(MAIN_X, branch_y, MAIN_W, h2, GOOD_BG, GOOD)
arrow_down(MAIN_X + MAIN_W/2, y, branch_y, color=GOOD)
label_on_line(MAIN_X + MAIN_W/2 + 140, y + 28, "RESOLVED", fill=GOOD)
sans(MAIN_X + 20, branch_y + 30, "Generate similar/harder problem", size=14, weight="700", fill=GOOD)
sans(MAIN_X + 20, branch_y + 52, "Tests transfer of understanding on a new item.", size=12, fill=INK)
sans(MAIN_X + 20, branch_y + 70, "-> feeds a new attempt back into Node 1", size=11, fill=MUTED)
y = branch_y + h2

bottom_y = y + 30

# --------------------------------------------------------- Student Model box
sm_y0 = analyzer_y[0] - 10
sm_y1 = evaluator_y[1] + 40
rect(SIDE_X, sm_y0, SIDE_W, sm_y1 - sm_y0, STORE, STORE_BORDER, rx=14)
sans(SIDE_X + SIDE_W/2, sm_y0 + 30, "STUDENT MODEL", size=14, weight="700", fill="#5133a3", anchor="middle")
sans(SIDE_X + SIDE_W/2, sm_y0 + 50, "(persistent store, not an LLM call)", size=10.5, fill="#5133a3", anchor="middle")
for i, line in enumerate([
    "Algebra:", "  Linear eq.: strong", "  Neg. signs: weak", "  Distribution: persistent",
    "Functions:", "  Domain: strong", "  Inverse fn.: weak",
]):
    sans(SIDE_X + 18, sm_y0 + 74 + i * 16, line, size=10.5, fill="#3d2b7a",
         weight="700" if not line.startswith(" ") else "400")
sans(SIDE_X + SIDE_W/2, sm_y1 - 16, "used to personalize future problems (planned)",
     size=9.5, fill="#5133a3", anchor="middle")

# dashed arrows into student model from Selector and Evaluator (writes)
arrow_path(f"M {MAIN_X+MAIN_W} {selector_y[0]+40} L {SIDE_X} {sm_y0+90}",
           color=STORE_BORDER, dash="4,4")
label_on_line((MAIN_X+MAIN_W+SIDE_X)/2, (selector_y[0]+40+sm_y0+90)/2 - 6, "writes", fill="#5133a3")

arrow_path(f"M {MAIN_X+MAIN_W} {evaluator_y[0]+40} L {SIDE_X} {sm_y0+140}",
           color=STORE_BORDER, dash="4,4")
label_on_line((MAIN_X+MAIN_W+SIDE_X)/2, (evaluator_y[0]+40+sm_y0+140)/2 + 10, "writes", fill="#5133a3")

# dashed arrow out to planner (planned read)
arrow_path(f"M {SIDE_X} {sm_y0+220} L {MAIN_X+MAIN_W} {planner_y[0]+48}",
           color=STORE_BORDER, dash="2,5")
sans(SIDE_X + 8, planner_y[0] + 30, "reads", size=11, weight="700", fill="#5133a3", anchor="start")
sans(SIDE_X + 8, planner_y[0] + 46, "(planned)", size=11, weight="700", fill="#5133a3", anchor="start")

# ------------------------------------------------------------------ title
TOP_PAD = 70
parts_header = []
parts_header.append(sans_header := None)  # placeholder, replaced below

TOTAL_H = bottom_y + 20

svg = f'''<svg viewBox="0 0 {W} {TOTAL_H}" xmlns="http://www.w3.org/2000/svg" role="img"
 aria-label="Bluetute workflow: human input flows through Input Parser, Reasoning Analyzer, Misconception Classifier, Adversarial Critic, Diagnosis Selector, Intervention Planner, and Socratic Tutor to reach the student; a Response Evaluator then checks whether the misconception was resolved, looping back to the Intervention Planner if not, and updating a persistent Student Model throughout.">
<rect x="0" y="0" width="{W}" height="{TOTAL_H}" fill="{BG}"/>
{''.join(parts)}
</svg>'''

html = f'''<!doctype html>
<html><head><meta charset="utf-8"><title>Bluetute Workflow</title>
<style>
  body {{ margin:0; background:#ffffff; font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif; }}
  .wrap {{ padding: 36px 40px 48px; max-width: {W+80}px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; color:{INK}; }}
  .sub {{ font-size: 13px; color:{MUTED}; margin: 0 0 22px; }}
  svg {{ width: 100%; height: auto; display:block; }}
  .legend {{ display:flex; gap:22px; margin-top: 18px; font-size: 11.5px; color:{MUTED}; flex-wrap: wrap; }}
  .swatch {{ display:inline-block; width:16px; height:16px; border-radius:4px; margin-right:7px; vertical-align:-3px; }}
  .legend span > span {{ box-sizing: border-box; }}
</style></head>
<body><div class="wrap">
<h1>Bluetute — ML Workflow (Reverie Hacks 2026, ML Prompt Engineering track)</h1>
<p class="sub">Diagnose-then-intervene pipeline. Green figures are real benchmark results (30-case set, Google AI Studio / Gemini) — not projected.</p>
{svg}
<div class="legend">
  <span><span class="swatch" style="background:{HUMAN};border:2.5px solid {HUMAN_BORDER}"></span>Human input</span>
  <span><span class="swatch" style="background:{CARD};border:2.5px solid {CARD_BORDER}"></span>LLM node</span>
  <span><span class="swatch" style="background:{ACCENT_BG};border:2.5px solid {ACCENT}"></span>Adversarial Critic (core differentiator)</span>
  <span><span class="swatch" style="background:{STORE};border:2.5px solid {STORE_BORDER}"></span>Persistent store</span>
  <span><span class="swatch" style="background:{GOOD_BG};border:2.5px solid {GOOD}"></span>Loop outcome</span>
</div>
</div></body></html>'''

out = Path(__file__).resolve().parent / "workflow.html"
out.write_text(html, encoding="utf-8")
print(f"Wrote {out}  (viewBox height={TOTAL_H})")
