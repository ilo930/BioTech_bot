"""
reply_core.py — what the bot answers when you DM it. Given a message text,
returns a list of reply strings (HTML). No Telegram code here, so it can be
tested offline.

  deeper   the science of the latest story, step by step
  tricks   the toolbox: every trick explained, with the stories that used it
  menu     the list of commands
"""

import json
import os

import requests

import config
import llm
import tricks
from card_format import esc
from writer import STYLE_RULES

MENU = (
    "🧪 <b>BioTech — menu</b>\n\n"
    "⚙️ <b>deeper</b> — the science of this week's story, step by step\n"
    "🧰 <b>tricks</b> — the invention moves, and which stories used each one\n"
    "❓ <b>menu</b> — show this again"
)

DEEPER_SYSTEM = f"""You are a patient science teacher. Explain how this invention works, deeper than the weekly card did.

Facts about the person and the invention come only from the source text. The science may use well-established textbook knowledge.

{STYLE_RULES}

Format for Telegram, plain text, no markdown:
1. "How it works, step by step" — 4-6 numbered steps.
2. "The science words" — 3-5 lines, word: plain meaning.
3. "Try it / look it up" — 2-3 safe things to try at home or search next."""


def read_state(name):
    """A file from state/. On GitHub Actions it is read live from the repo, so the
    long-running listener sees a story posted after it started."""
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    if repo and token:
        r = requests.get(f"https://api.github.com/repos/{repo}/contents/state/{name}",
                         headers={"Authorization": f"Bearer {token}",
                                  "Accept": "application/vnd.github.raw+json"}, timeout=15)
        r.raise_for_status()
        return r.json()
    path = os.path.join(config.STATE_DIR, name)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def deeper():
    story = read_state("latest_story.json")
    if not story:
        return ["No story has been posted yet — the first one arrives this week."]
    card = story["card"]
    prompt = (f"Person: {story['name']}\nIngredients: {', '.join(card['ingredients'])}\n"
              f"What the card said: {card['why_it_works']}\n\n"
              f"SOURCE TEXT:\n{story['source_text']}")
    reply = llm.chat(DEEPER_SYSTEM, prompt, config.DEEPER_MAX_TOKENS, label=" deeper")
    if not reply.strip():
        return ["The AI didn't answer just now — try <b>deeper</b> again in a minute."]
    return [f"⚙️ <b>Deeper: {esc(story['name'])}</b>\n\n{esc(reply.strip())}"]


def toolbox():
    posted = read_state("posted.json") or []
    lines = ["🧰 <b>The toolbox</b>\n<i>Eight moves inventors keep using. "
             "Each story adds an example.</i>"]
    for key, t in tricks.TRICKS.items():
        names = [p["name"] for p in posted if p["trick"] == key]
        seen = esc(", ".join(names)) if names else "<i>no story yet</i>"
        lines.append(f"{t['emoji']} <b>{esc(t['name'])}</b>\n{esc(t['explain'])}\n→ {seen}")
    return ["\n\n".join(lines)]


def handle_text(text):
    word = (text or "").strip().lower().lstrip("/").split("@")[0].split(" ")[0]
    if word in ("deeper", "deep", "more", "science"):
        return deeper()
    if word in ("tricks", "trick", "toolbox"):
        return toolbox()
    return [MENU]
