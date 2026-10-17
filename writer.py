"""
writer.py — asks the AI to write one story card from the source text, then
checks every part is there and has it fact-checked (fact_check.py). A card
with a missing part or an unsupported claim is refused, never sent.
"""

from pydantic import BaseModel, Field, ValidationError, field_validator

import config
import fact_check
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
- Ingredients: only materials the source names as part of the invention. Sunlight, heat or time are steps, never ingredients.
- Keep each ingredient's role exactly as the source gives it. Never move a property from one ingredient to another.
- "what_next": a hope, plan or "could" in the source stays a hope. Never turn it into something that happened.
- The "why it works" part may use well-established textbook science to explain how the NAMED ingredients behave, as long as it never contradicts the source. Never invent numbers.

{STYLE_RULES}

Return ONLY a JSON object with these keys:
"when": age and/or year from the source, e.g. "16 · 2016" ("" if the source gives neither),
"hook": one sentence that makes you want to read on,
"problem": 1-2 sentences, what they saw that needed fixing,
"ingredients": list of 1-6 short strings, what the invention is physically made of,
"why_it_works": 4-6 sentences. FIRST the concrete details the source gives: what each ingredient contributes, any numbers, the making steps (heating, sun, mixing). THEN the textbook science of why that works. This is the heart of the card — be specific, never vague,
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


def card_prompt(person, source_text, fix=()):
    t = tricks.TRICKS[person["trick"]]
    prompt = (f"Person: {person['name']}\n"
              f"Trick to explain: {t['name']} — {t['explain']}\n\n"
              f"SOURCE TEXT:\n{source_text}")
    if fix:
        prompt += ("\n\nA fact-checker rejected your previous card. Do not repeat these "
                   "problems:\n" + "\n".join(f"- {p}" for p in fix))
    return prompt


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
    """A complete card that passed the fact-check, or None.
    Up to three tries; each retry is told what the checker rejected."""
    fix = []
    for attempt in (1, 2, 3):
        reply = llm.chat(CARD_SYSTEM, card_prompt(person, source_text, fix),
                         config.CARD_MAX_TOKENS, temperature=0.2, label=f" card#{attempt}")
        card = validate(llm.extract_json(reply))
        if not card:
            continue
        found = fact_check.problems(card, source_text)
        if found == []:
            print(f"[writer] card #{attempt} passed the fact-check")
            return card
        fix = found or fix
    return None
