"""
Shared infrastructure for running a workflow node against all 30 benchmark
cases in a SINGLE AI Studio request instead of 30 separate copy-pastes.

Why batch: this cloud sandbox cannot call LLM APIs directly (network is
allowlisted, see README), so every node has to be run manually in Google
AI Studio. Doing that 30 times per node across ~7 remaining nodes would be
~200+ manual copy-paste actions. Batching turns each node into exactly
ONE paste-in (the batch prompt) and ONE paste-out (the JSON array reply).

Contract: the model is asked to return a JSON array, in the same order as
the cases given, where each element is the node's normal schema fields
PLUS a "case_id" field. Order is not trusted for matching — case_id is —
but order is requested anyway since some models track it more reliably
than others, which helps quietly catch dropped cases.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build_batch_user_message(intro: str, case_blocks: list[tuple[str, str]]) -> str:
    """
    case_blocks: list of (case_id, per-case prompt text without any
    "respond with JSON" instructions — those belong in the system prompt).
    """
    parts = [intro, ""]
    for case_id, text in case_blocks:
        parts.append(f"===== CASE {case_id} =====")
        parts.append(text.strip())
        parts.append("")
    return "\n".join(parts)


def batch_json_instruction(per_case_schema_hint: str) -> str:
    return f"""

You will receive MULTIPLE independent cases, each delimited by a line like \
"===== CASE <id> =====". Treat every case as completely independent — do \
not let one case's content influence another's analysis, and do not \
compare cases to each other.

Respond with ONLY a single valid JSON array, no markdown code fences, no \
extra text before or after it. The array must have exactly one element per \
case, in the same order the cases were given, and each element must \
include a "case_id" field matching the case's id, plus these fields:
{per_case_schema_hint}"""


def extract_json_array(raw: str):
    """Find the outermost [...] in raw text (tolerating stray prose/fences
    around it) and return the parsed list. Falls back to lenient parsing
    (allows raw control chars like literal newlines inside strings, which
    happens often when copying rendered math out of AI Studio)."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()

    start = raw.find("[")
    if start == -1:
        raise ValueError("No JSON array found ('[' not present) in the pasted response.")

    depth = 0
    in_string = False
    escape = False
    end = None
    for i in range(start, len(raw)):
        ch = raw[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        raise ValueError("Unbalanced brackets — the pasted JSON array looks truncated.")

    text = raw[start:end]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(text, strict=False)


def clean_text(s):
    return re.sub(r"\s+", " ", s).strip() if isinstance(s, str) else s
