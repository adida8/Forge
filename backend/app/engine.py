"""The Forge engine.

Wraps the Anthropic API to do four jobs against a request + its refine-chat
transcript:
  1. Ask the smallest set of gap-closing questions (refine).
  2. Score priority (impact x reach / effort -> 0-100).
  3. Score readiness (gates the dev handoff).
  4. Write the dev prompt once readiness clears the threshold.

It always returns one structured object so the API layer stays dumb. If no
ANTHROPIC_API_KEY is set, a deterministic heuristic fallback runs instead, so
the app is fully functional for local testing without a key.
"""

import json
import re

from .config import settings

READINESS_RUBRIC = """\
Readiness rubric (weights):
- Problem clearly stated — 20
- Scope bounded (in AND out) — 20
- Acceptance criteria testable — 25
- Edge/error cases named — 20
- Dependencies/risks surfaced — 15
Score 0-100. Penalise ambiguity, missing acceptance criteria, undefined edges."""

DEV_PROMPT_TEMPLATE = """\
The dev prompt MUST use exactly these markdown sections:
## Problem
## Scope
## Acceptance criteria
## Likely files / areas
## Risks & dependencies
## Out of scope"""

SYSTEM = f"""You are The Forge — a spec compiler that refines rough feature \
requests until they are buildable, then writes a developer handoff prompt.

Your behaviour:
- Interrogate ONLY the gaps. Ask the smallest set of questions that would raise \
the readiness score. One focused question per turn (you may bundle 2-3 tightly \
related sub-questions). Never re-ask something already answered.
- Stop asking once readiness clears the threshold of {{threshold}}. At that \
point, set "reply" to a short confirmation that the spec is ready, and fill \
"dev_prompt".
- Be terse and concrete. No filler.

{READINESS_RUBRIC}

Priority score = impact x reach / effort, mapped to 0-100. Estimate from what \
the requester says; if unknown, assume a mid value and note the assumption in \
your reply.

{DEV_PROMPT_TEMPLATE}

Respond with ONLY a JSON object, no prose around it:
{{{{
  "reply": "your next question OR ready-confirmation",
  "readiness_score": <int 0-100>,
  "priority_score": <int 0-100>,
  "dev_prompt": "<markdown spec, ONLY when readiness >= threshold, else null>"
}}}}"""


def _build_messages(request, transcript):
    """transcript: list of (role, content) where role is 'user' or 'engine'."""
    lines = [
        f"REQUEST TITLE: {request.title}",
        f"RAW IDEA: {request.raw_idea}",
        "",
        "REFINE TRANSCRIPT (oldest first):",
    ]
    if not transcript:
        lines.append("(none yet — this is the first turn)")
    for role, content in transcript:
        who = "REQUESTER" if role == "user" else "FORGE"
        lines.append(f"{who}: {content}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    """Claude usually returns clean JSON; be defensive about stray prose."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?|\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def run_engine(request, transcript) -> dict:
    """Returns {reply, readiness_score, priority_score, dev_prompt}."""
    threshold = settings.readiness_threshold

    if not settings.anthropic_api_key:
        return _fallback(request, transcript, threshold)

    # Imported lazily so the app boots without the package configured.
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    system = SYSTEM.replace("{threshold}", str(threshold))
    resp = client.messages.create(
        model=settings.forge_model,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": _build_messages(request, transcript)}],
    )
    data = _extract_json(resp.content[0].text)

    readiness = int(data.get("readiness_score", 0))
    priority = int(data.get("priority_score", 50))
    dev_prompt = data.get("dev_prompt") or None
    if readiness < threshold:
        dev_prompt = None  # never expose a prompt below the bar
    return {
        "reply": data.get("reply", ""),
        "readiness_score": max(0, min(100, readiness)),
        "priority_score": max(0, min(100, priority)),
        "dev_prompt": dev_prompt,
    }


# --- Heuristic fallback (no API key) ---------------------------------------
# Lets the app run end-to-end offline. Each requester answer nudges readiness
# up; a canned dev prompt is produced once the bar is cleared.
_GAP_QUESTIONS = [
    "What problem does this solve, and for whom? Be specific about the user.",
    "Which surface does this live on, and what exactly is in vs out of scope?",
    "What are the acceptance criteria — how do we know it's done and correct?",
    "What are the error/edge cases, and what does it depend on or touch?",
]


def _fallback(request, transcript, threshold) -> dict:
    answers = [c for r, c in transcript if r == "user"]
    n = len(answers)
    readiness = min(100, 25 + n * 20)
    priority = 60

    if readiness >= threshold:
        reply = "Looks buildable — readiness cleared the bar. Dev prompt written below."
        dev_prompt = _fallback_prompt(request, answers)
    else:
        idx = min(n, len(_GAP_QUESTIONS) - 1)
        reply = _GAP_QUESTIONS[idx]
        dev_prompt = None

    return {
        "reply": reply,
        "readiness_score": readiness,
        "priority_score": priority,
        "dev_prompt": dev_prompt,
    }


def _fallback_prompt(request, answers) -> str:
    notes = "\n".join(f"- {a}" for a in answers) or "- (no detail captured)"
    return f"""## Problem
{request.raw_idea}

## Scope
Derived from the refine chat:
{notes}

## Acceptance criteria
- TODO: confirm testable criteria from the answers above.

## Likely files / areas
- TODO: identify from the codebase.

## Risks & dependencies
- TODO: surfaced during refine.

## Out of scope
- Anything not stated above.

_(Generated by the offline fallback — set ANTHROPIC_API_KEY for the real engine.)_"""
