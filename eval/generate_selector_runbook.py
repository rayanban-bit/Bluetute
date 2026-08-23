"""
Generates prompts/RUNBOOK_diagnosis_selector.md — ONE batched prompt for
Node 6 (Diagnosis Selector), chained from real Classifier + Critic output.

Run: python3 eval/generate_selector_runbook.py
"""

import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from eval.batch_common import batch_json_instruction, build_batch_user_message  # noqa: E402

CLASSIFIER_CSV = ROOT / "results" / "classifier_results.csv"
CRITIC_CSV = ROOT / "results" / "critic_results.csv"
ANALYZER_CSV = ROOT / "results" / "analyzer_results.csv"


def _load_node(module_filename: str):
    path = ROOT / "prompts" / module_filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCHEMA_HINT = """{
  "case_id": "<echo the case id, e.g. 'A02'>",
  "misconception_id": "<final chosen id, or 'unknown'>",
  "error_type": "<one of: conceptual, execution, incomplete, unknown>",
  "final_confidence": <float 0.0-1.0>,
  "evidence_summary": "<<=500 chars, conclusion + direct support only, no narrated deliberation>",
  "intervention_appropriate": <true or false>
}"""


def main():
    for p in (CLASSIFIER_CSV, CRITIC_CSV, ANALYZER_CSV):
        if not p.exists():
            print(f"{p} not found. Run the earlier nodes first.")
            sys.exit(1)

    node = _load_node("04_diagnosis_selector.py")

    with open(ANALYZER_CSV, encoding="utf-8") as f:
        analyzer_by_id = {r["case_id"]: r for r in csv.DictReader(f)}
    with open(CLASSIFIER_CSV, encoding="utf-8") as f:
        classifier_by_id = {r["case_id"]: r for r in csv.DictReader(f) if r.get("claimed_misconception_id")}
    with open(CRITIC_CSV, encoding="utf-8") as f:
        critic_by_id = {r["case_id"]: r for r in csv.DictReader(f) if r.get("diagnosis_survives") != ""}

    case_ids = [cid for cid in classifier_by_id if cid in critic_by_id]
    if not case_ids:
        print("No cases have both Classifier and Critic results. Run those steps first.")
        sys.exit(1)

    case_blocks = []
    for cid in case_ids:
        cls = classifier_by_id[cid]
        crit = critic_by_id[cid]
        analyzer_error_type = analyzer_by_id.get(cid, {}).get("claimed_error_type", "conceptual")

        alt_ids_str = crit.get("alternative_ids_proposed", "")
        alternatives = []
        if alt_ids_str:
            for aid in alt_ids_str.split("|"):
                if aid:
                    alternatives.append({
                        "misconception_id": aid,
                        "plausibility": "see critic transcript",
                        "supporting_evidence": "(see critic's attempted_rebuttal below)",
                        "contradicting_evidence": "(see critic's attempted_rebuttal below)",
                    })

        prompt = node.build_prompt(
            initial_id=cls["claimed_misconception_id"],
            initial_confidence=cls["confidence"],
            initial_evidence=cls["evidence"],
            error_type=analyzer_error_type,
            rebuttal=crit.get("attempted_rebuttal", ""),
            alternatives=alternatives,
            survives=crit.get("diagnosis_survives", "true"),
            survival_rationale="(see attempted_rebuttal)",
            confidence_adjustment=crit.get("confidence_adjustment", "0.0"),
        )
        case_blocks.append((cid, prompt["user"]))

    user_message = build_batch_user_message(
        f"Reconcile the following {len(case_blocks)} independent diagnosis+critic "
        f"pairs into one final diagnosis each.",
        case_blocks,
    )
    system_text = node.SYSTEM_PROMPT_V1 + batch_json_instruction(SCHEMA_HINT)

    lines = []
    lines.append(f"# Bluetute — Diagnosis Selector Runbook (BATCHED, prompt {node.VERSION})\n")
    lines.append(
        f"Chained from {len(case_blocks)} real Classifier+Critic pairs.\n\n"
        "1. New chat in AI Studio.\n"
        "2. Paste **System Instructions** once.\n"
        "3. Paste the **Batch User Message** once.\n"
        "4. Save the JSON array reply into `results/selector_raw_responses.txt`.\n"
        "5. Run `python3 eval/ingest_selector.py`.\n"
    )
    lines.append("---\n\n## System Instructions (paste once)\n")
    lines.append("```\n" + system_text + "\n```\n")
    lines.append(f"---\n\n## Batch User Message ({len(case_blocks)} cases)\n")
    lines.append("```\n" + user_message + "\n```\n")
    out = ROOT / "prompts" / "RUNBOOK_diagnosis_selector.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({len(case_blocks)} cases, batched)")


if __name__ == "__main__":
    main()
