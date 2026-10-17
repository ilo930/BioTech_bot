"""
fact_check.py — a second AI pass that compares a finished card with its source
and lists every claim the source does not back up. The writer is good at
sounding right; this pass exists because the first real card swapped which
ingredient did what and invented field trials that never happened.
"""

import json

import config
import llm

CHECK_SYSTEM = """You are a strict fact-checker. You get a SOURCE TEXT and a CARD written from it.

List every claim in the card that the source does not support. Check especially:
- each ingredient: is it named in the source as part of the invention?
- which ingredient does what: does the card give a role to the wrong ingredient?
- results, prizes, dates, ages, spread: hopes or plans in the source must not appear as things that happened.

General textbook science that explains HOW a named ingredient behaves is allowed (e.g. "pectin is a gel"), as long as it does not contradict the source.

Return ONLY JSON: {"unsupported": ["short description of each problem", ...]}. Empty list if the card is clean."""


def problems(card, source_text):
    """The list of unsupported claims, or None if the checker itself failed
    (a failed check counts as a failed card, never as a pass)."""
    prompt = (f"SOURCE TEXT:\n{source_text}\n\n"
              f"CARD:\n{json.dumps(card.model_dump(), ensure_ascii=False, indent=1)}")
    reply = llm.extract_json(llm.chat(CHECK_SYSTEM, prompt, config.CHECK_MAX_TOKENS,
                                      temperature=0.0, label=" check"))
    found = reply.get("unsupported")
    if not isinstance(found, list):
        print("[check] the fact-checker gave no usable answer")
        return None
    for p in found:
        print(f"[check] unsupported: {p}")
    return [str(p) for p in found]
