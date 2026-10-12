"""
card_format.py — turns a checked card into the Telegram post (HTML).
All the look of the post lives here: section emojis, order, line breaks.
"""

import html

import tricks

HEADER = "🧪 <b>BIOTECH</b>"
SECTIONS = {   # emoji per section — change the look here
    "problem": "🌵", "ingredients": "🧺", "why": "⚙️", "next": "📈", "turn": "💭",
}


def esc(s):
    return html.escape(str(s or ""), quote=False)


def iso_flag(iso):
    iso = (iso or "").strip().upper()
    if len(iso) != 2 or not iso.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso)


def source_label(url):
    """'Google Science Fair' for a Wikipedia page, the site name for an article."""
    if "wikipedia.org/wiki/" in url:
        return url.rsplit("/", 1)[-1].replace("_", " ")
    return url.split("/")[2].replace("www.", "").replace("edition.", "")


def format_post(person, card, number, first_time_trick, source_urls):
    t = tricks.TRICKS[person["trick"]]
    who = f"<b>{esc(person['name'])}</b> {iso_flag(person['country'])}"
    if card.when:
        who += f" · {esc(card.when)}"
    trick_block = f"{t['emoji']} <b>The trick: {esc(t['name'])}</b>\n"
    if first_time_trick:
        trick_block += f"<i>{esc(t['explain'])}</i>\n"
    trick_block += esc(card.trick_here)
    sources = " · ".join(f'<a href="{esc(u)}">{esc(source_label(u))}</a>' for u in source_urls)
    s = SECTIONS
    return "\n\n".join([
        f"{HEADER} · #{number}\n{who}\n<i>{esc(card.hook)}</i>",
        f"{s['problem']} <b>The problem</b>\n{esc(card.problem)}",
        f"{s['ingredients']} <b>What it's made of</b>\n"
        + "\n".join(f"• {esc(i)}" for i in card.ingredients),
        f"{s['why']} <b>Why it works</b>\n{esc(card.why_it_works)}",
        f"{s['next']} <b>What happened next</b>\n{esc(card.what_next)}",
        trick_block,
        f"{s['turn']} <b>Your turn</b>\n{esc(card.your_turn)}",
        f"🔗 {sources}\n<i>DM the bot: </i><code>deeper</code><i> · </i><code>tricks</code>",
    ])
