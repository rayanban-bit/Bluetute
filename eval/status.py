"""
Prints exactly what you need to do next in the manual AI-Studio pipeline.
Run this any time you're not sure what's next.

Run: python3 eval/status.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

# Ordered pipeline: (label, runbook_to_paste, raw_file_to_fill, ingest_script, results_csv)
PIPELINE = [
    ("Baseline", "baseline/RUNBOOK.md", "results/baseline_raw_responses.txt",
     "eval/ingest_baseline.py", "results/baseline_results.csv"),
    ("Reasoning Analyzer", "prompts/RUNBOOK_reasoning_analyzer.md", "results/analyzer_raw_responses.txt",
     "eval/ingest_analyzer.py", "results/analyzer_results.csv"),
    ("Misconception Classifier", "prompts/RUNBOOK_misconception_classifier.md",
     "results/classifier_raw_responses.txt", "eval/ingest_classifier.py", "results/classifier_results.csv"),
]


def has_content(rel_path: str) -> bool:
    p = ROOT / rel_path
    return p.exists() and p.read_text(encoding="utf-8").strip() not in ("", )


def main():
    print("Bluetute pipeline status\n" + "=" * 40)
    next_action = None
    for label, runbook, raw_file, ingest, results_csv in PIPELINE:
        done = (ROOT / results_csv).exists() and (ROOT / results_csv).stat().st_size > 0
        pasted = has_content(raw_file)
        if done:
            print(f"[DONE]    {label:28s} -> {results_csv}")
        elif pasted:
            status = f"[READY]   {label:28s} -> paste done, run: python3 {ingest}"
            print(status)
            if next_action is None:
                next_action = f"Run: python3 {ingest}"
        else:
            runbook_exists = (ROOT / runbook).exists()
            if runbook_exists:
                print(f"[WAITING] {label:28s} -> paste {runbook} into AI Studio, "
                      f"save reply into {raw_file}")
                if next_action is None:
                    next_action = f"Open {runbook}, run it in AI Studio, paste the reply into {raw_file}"
            else:
                print(f"[BLOCKED] {label:28s} -> runbook not generated yet")
                if next_action is None:
                    next_action = f"Ask Claude to generate {runbook}"

    print("\n" + "=" * 40)
    if next_action:
        print(f"NEXT ACTION: {next_action}")
    else:
        print("All listed nodes are scored. Ask Claude to chain the next node "
              "(Critic, Diagnosis Selector, ...).")


if __name__ == "__main__":
    main()
