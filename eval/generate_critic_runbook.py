"""
Generates prompts/RUNBOOK_adversarial_critic.md — ONE batched prompt for
Node 5 (Adversarial Critic), chained from the real Misconception Classifier
results (results/classifier_results.csv).

The critic reviews every case the Classifier actually produced a diagnosis
for — its job is to try to break that diagnosis, not to re-derive it from
scratch. Recommended: run this in a NEW AI Studio chat (spec section 16
suggests model diversity across nodes reduces correlated blind spots —
consider trying a different model here than you used for the Analyzer/
Classifier, if you want to test that claim rather than assume it).

Requires results/classifier_results.csv to exist first.

Run: python3 eval/generate_critic_runbook.py
"""

import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmark.cases import CASES_BY_ID  # noqa: E402
from eval.batch_common import batch_json_instruction, build_batch_user_message  # noqa: E402

CLASSIFIER_CSV = ROOT / "results" / "classifier_results.csv"


def _load_node(module_filename: str):
    path = ROOT / "prompts" / module_filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _number_steps(steps: list[str]) -> str:
    if not steps:
        return "(no work shown)"
    return "\n".join(f"[{i}] {s}" for i, s in enumerate(steps))


SCHEMA_HINT = """{
  "case_id": "<echo the case id, e.g. 'A02'>",
  "attempted_rebuttal": "<your strongest case against the proposed diagnosis>",
  "alternative_hypotheses": [
    {"misconception_id": "<taxonomy id>", "supporting_evidence": "...", "contradicting_evidence": "...", "plausibility": <float 0-1>}
  ],
  "diagnosis_survives": <true or false>,
  "survival_rationale": "<why it does/doesn't survive>",
  "confidence_adjustment": <float -1.0 to +1.0, usually <= 0>
}"""


def main():
    if not CLASSIFIER_CSV.exists():
        print(f"{CLASSIFIER_CSV} not found. Run the Classifier runbook + "
              "eval/ingest_classifier.py first.")
        sys.exit(1)

    node = _load_node("03_adversarial_critic.py")

    with open(CLASSIFIER_CSV, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("claimed_misconception_id")]

    if not rows:
        print(f"No classified cases found in {CLASSIFIER_CSV}.")
        sys.exit(1)

    case_blocks = []
    for r in rows:
        case = CASES_BY_ID[r["case_id"]]
        alt_ids = [x for x in r.get("alternative_candidate_ids", "").split("|") if x]
        prompt = node.build_prompt(
            domain=case.domain,
            problem_statement=case.problem,
            numbered_steps=_number_steps(case.student_reasoning),
            misconception_id=r["claimed_misconception_id"],
            label=r.get("label", ""),
            evidence=r.get("evidence", ""),
            confidence=r.get("confidence", ""),
            alt_ids=alt_ids,
        )
        case_blocks.append((case.id, prompt["user"]))

    user_message = build_batch_user_message(
        f"Critique the following proposed diagnoses. There are {len(case_blocks)} "
        f"independent cases. For each, try genuinely to break the proposed "
        f"diagnosis before deciding whether it survives.",
        case_blocks,
    )

    system_text = node.SYSTEM_PROMPT_V1.format(
        taxonomy_block=__import__(
            "taxonomy.misconception_taxonomy", fromlist=["taxonomy_prompt_block"]
        ).taxonomy_prompt_block()
    ) + batch_json_instruction(SCHEMA_HINT)

    lines = []
    lines.append(f"# Bluetute — Adversarial Critic Runbook (BATCHED, prompt {node.VERSION})\n")
    lines.append(
        f"Chained from {len(rows)} real Classifier diagnoses.\n\n"
        "Consider using a DIFFERENT model/chat than the Analyzer+Classifier "
        "for this one (spec section 16: model diversity reduces correlated "
        "blind spots) — not required, but worth trying once.\n\n"
        "1. New chat in AI Studio.\n"
        "2. Paste **System Instructions** once.\n"
        "3. Paste the **Batch User Message** once.\n"
        "4. Save the JSON array reply into `results/critic_raw_responses.txt`.\n"
        "5. Run `python3 eval/ingest_critic.py`.\n"
    )
    lines.append("---\n\n## System Instructions (paste once)\n")
    lines.append("```\n" + system_text + "\n```\n")
    lines.append(f"---\n\n## Batch User Message ({len(case_blocks)} cases)\n")
    lines.append("```\n" + user_message + "\n```\n")
    out = ROOT / "prompts" / "RUNBOOK_adversarial_critic.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({len(case_blocks)} cases, batched)")


if __name__ == "__main__":
    main()
