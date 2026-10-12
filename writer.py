"""
writer.py — asks the AI to write one story card from the source text, then
checks every part is there. A card with a missing part is refused, never sent
half-empty (MicroDigest once posted bare headlines because of a silent fallback).
"""

from pydantic import BaseModel, Field, ValidationError, field_validator

import config
import llm
import tricks

STYLE_RULES = """Style:
- Plain English for a curious adult who never studied science. ELI5 register.
- Sentences under 20 words. One idea each.
- The first time a science word appears, define it in brackets: "pectin (the natural gel that makes jam set)".
- Never use the "it's not X, it's Y" construction. No hype words (revolutionary, game-changer)."""

CARD_SYSTEM = f"""You write one weekly story for BioTech, a channel that teaches how real inventions work so the reader can learn to invent.

Hard rules:
- Facts about the PERSON and the INVENTION (names, ages, dates, places, results) come ONLY from the source text. If the source does not say something, leave it out.
- The "why it works" part may use well-established textbook science (chemistry, physics, biology) to explain the mechanism, even if the source does not spell it out. Never invent numbers.

{STYLE_RULES}

Return ONLY a JSON object with these keys:
"when": age and/or year from the source, e.g. "16 · 2016" ("" if the source gives neither),
"hook": one sentence that makes you want to read on,
"problem": 1-2 sentences, what they saw that needed fixing,
"ingredients": list of 1-6 short strings, what the invention is physically made of,
"why_it_works": 3-5 sentences, the mechanism step by step,
"what_next": 1-2 sentences, what happened after (prizes, spread, impact),
"trick_here": 1-2 sentences, how this invention uses the given trick,
"your_turn": one question that invites the reader to apply the same trick to something new."""


class Card(BaseModel):
    when: str = ""
    hook: str = Field(min_length=10)
    problem: str = Field(min_length=10)
    ingredients: list[str] = Field(min_length=1, max_length=6)
    why_it_works: str = Field(min_length=40)
    what_next: str = Field(min_length=10)
    trick_here: str = Field(min_length=10)
    your_turn: str = Field(min_length=10)

    @field_validator("ingredients")
    @classmethod
    def no_blank_ingredients(cls, v):
        v = [s.strip() for s in v if s and s.strip()]
        if not v:
            raise ValueError("ingredients are all blank")
        return v


def card_prompt(person, source_text):
    t = tricks.TRICKS[person["trick"]]
    return (f"Person: {person['name']}\n"
            f"Trick to explain: {t['name']} — {t['explain']}\n\n"
            f"SOURCE TEXT:\n{source_text}")


def validate(raw):
    """Turn the AI's JSON into a Card, or None (with the reason logged)."""
    try:
        return Card.model_validate(raw)
    except ValidationError as e:
        print(f"[writer] card refused — {e.error_count()} problem(s):")
        for err in e.errors():
            print(f"   · {'.'.join(map(str, err['loc'])) or 'card'}: {err['msg']}")
        return None


def write_card(person, source_text):
    """Two tries at a complete card; None if both come back incomplete."""
    for attempt in (1, 2):
        reply = llm.chat(CARD_SYSTEM, card_prompt(person, source_text),
                         config.CARD_MAX_TOKENS, label=f" card#{attempt}")
        card = validate(llm.extract_json(reply))
        if card:
            return card
    return None
