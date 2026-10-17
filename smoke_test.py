"""
smoke_test.py — checks the bot still works, in plain words.

  python3 smoke_test.py          offline checks (no internet, no keys)
  python3 smoke_test.py --live   also fetches a real Wikipedia page, and writes a
                                 real card if GROQ_API_KEY is set (prints it, posts nothing)
"""

import datetime
import json
import os
import sys
import tempfile
import time

os.environ["DRY_RUN"] = "1"   # never post from a test

import config
import people
import reply_core
import state
import tricks
import sources
import writer
from card_format import format_post

GOOD = {"when": "16 · 2016", "hook": "A teenager turned breakfast scraps into rain insurance.",
        "problem": "Drought kills crops and the water-holding powders are expensive.",
        "ingredients": ["orange peel", "avocado skin"],
        "why_it_works": "Orange peel holds pectin (the gel that makes jam set). Heated with oil "
                        "from avocado skin it forms a sponge that soaks up water.",
        "what_next": "She won the Google Science Fair grand prize.",
        "trick_here": "Peels people throw away already hold the water-grabbing gel.",
        "your_turn": "What else do we throw away that holds water?"}

results = []


def check(name, fn):
    try:
        fn()
        results.append((True, name, ""))
    except Exception as e:
        results.append((False, name, f"{type(e).__name__}: {e}"))


def people_list_is_sound():
    keys = [p["key"] for p in people.PEOPLE]
    assert len(keys) == len(set(keys)), "two people share a key"
    for p in people.PEOPLE:
        assert p["trick"] in tricks.TRICKS, f"{p['name']} has unknown trick {p['trick']}"
        assert p["sources"], f"{p['name']} has no source page"
        assert p["must_mention"], f"{p['name']} has no must_mention words"
    assert people.upcoming(set())[0] is people.PEOPLE[0]
    assert people.upcoming(set(keys)) == []


def page_trimming_keeps_the_invention():
    text = ("Intro about her.\n\n== Early life ==\nborn somewhere\n\n"
            "== Invention ==\norange peel polymer\n\n== Personal life ==\nhobbies")
    out = sources.focus(text, 5000)
    assert "orange peel polymer" in out and "Intro" in out
    assert "hobbies" not in out and "born somewhere" not in out
    fair = "Intro.\n\n== 2016 ==\nWon by Kiara Nirghin.\nWon by someone else."
    assert sources.focus(fair, 5000, ("Nirghin",)) == "Intro.\n\nWon by Kiara Nirghin."


def short_sources_hand_space_to_long_ones():
    assert sources.share_budget([5000, 200], 6000) == [5000, 200]
    assert sources.share_budget([9000, 200], 6000) == [5800, 200]
    assert sum(sources.share_budget([9000, 9000, 9000], 6000)) == 6000


def news_article_is_read_cleanly():
    page = ("<html><style>.x{color:red}</style><script>var a=1;</script><nav><p>Menu</p></nav>"
            "<p>Using orange peel and avocado skins, the student created a polymer.</p>"
            "<p>Short</p></html>")
    assert sources.article_text(page) == ("Using orange peel and avocado skins, "
                                          "the student created a polymer.")


def thin_sources_are_caught():
    person = {**people.PEOPLE[0], "sources": ["Fake page"]}
    real = sources.fetch_wikipedia
    sources.fetch_wikipedia = lambda t: (t, "She now works in AI.", "https://x")
    try:
        sources.gather(person)
    except sources.SourceTooThin:
        return
    finally:
        sources.fetch_wikipedia = real
    raise AssertionError("a page without 'orange' was accepted for Kiara")


def complete_card_is_accepted():
    assert writer.validate(GOOD) is not None


def incomplete_card_is_refused():
    for missing in ("why_it_works", "your_turn", "ingredients"):
        broken = {k: v for k, v in GOOD.items() if k != missing}
        assert writer.validate(broken) is None, f"card without {missing} got through"
    assert writer.validate({**GOOD, "ingredients": ["", " "]}) is None
    assert writer.validate({}) is None


def fact_check_blocks_unsupported_cards():
    import llm
    real, prompts = llm.chat, []

    def fake_ai(verdicts):
        def chat(system, prompt, *a, **k):
            prompts.append(prompt)
            if "fact-checker" in system:
                return json.dumps({"unsupported": verdicts.pop(0)})
            return json.dumps(GOOD)
        return chat
    try:
        llm.chat = fake_ai([["avocado given the pectin"]] * 3)
        assert writer.write_card(people.PEOPLE[0], "src") is None, "a rejected card got through"
        prompts.clear()
        llm.chat = fake_ai([["field trials invented"], []])
        assert writer.write_card(people.PEOPLE[0], "src") is not None
        assert "field trials invented" in prompts[2], "the retry was not told what was wrong"
    finally:
        llm.chat = real


def post_renders_and_fits_telegram():
    card, kiara = writer.validate(GOOD), people.PEOPLE[0]
    url = ["https://edition.cnn.com/2016/08/09/africa/x/index.html",
           "https://en.wikipedia.org/wiki/Google_Science_Fair"]
    first = format_post(kiara, card, 1, True, url)
    later = format_post(kiara, card, 5, False, url)
    explain = tricks.TRICKS[kiara["trick"]]["explain"]
    assert explain in first, "trick not explained on first appearance"
    assert explain not in later, "trick explained again after the first time"
    assert "🇿🇦" in first and "#1" in first
    assert ">cnn.com<" in first and ">Google Science Fair<" in first
    assert len(first) < config.TELEGRAM_LIMIT


def weekly_gate_works():
    def ago(days):
        return [{"date": (state.now() - datetime.timedelta(days=days)).isoformat()}]
    assert not state.too_soon([])
    assert state.too_soon(ago(2))
    assert not state.too_soon(ago(7))


def bot_replies_work():
    with tempfile.TemporaryDirectory() as tmp:
        config.STATE_DIR = tmp
        with open(os.path.join(tmp, "posted.json"), "w") as f:
            json.dump([{"key": "kiara_nirghin", "name": "Kiara Nirghin",
                        "trick": "waste_to_resource", "date": "2026-10-12"}], f)
        box = reply_core.handle_text("tricks")[0]
        assert "Kiara Nirghin" in box and box.count("<b>") == len(tricks.TRICKS) + 1
        assert "No story" in reply_core.handle_text("/deeper")[0]  # no latest_story yet
        assert "menu" in reply_core.handle_text("hello")[0]


def live_every_source_holds_up():
    broken = []
    for p in people.PEOPLE:
        try:
            text, _ = sources.gather(p)
            print(f"   ✓ {p['name']}: {len(text)} characters")
        except Exception as e:
            broken.append(f"{p['name']} ({e})")
        time.sleep(2)   # Wikipedia rate-limits bursts
    assert not broken, "; ".join(broken)


def live_card():
    kiara = people.PEOPLE[0]
    text, urls = sources.gather(kiara)
    card = writer.write_card(kiara, text)
    assert card, "the AI did not return a complete card"
    print(format_post(kiara, card, 1, True, urls))


check("The people list is sound (unique, real tricks, a source each)", people_list_is_sound)
check("Long Wikipedia pages are trimmed to the invention parts", page_trimming_keeps_the_invention)
check("Short sources hand their unused space to long ones", short_sources_hand_space_to_long_ones)
check("News articles are read without menus and scripts", news_article_is_read_cleanly)
check("A source that no longer describes the invention is caught", thin_sources_are_caught)
check("A complete card is accepted", complete_card_is_accepted)
check("A card with a missing part is refused", incomplete_card_is_refused)
check("The fact-checker blocks a card with unsupported claims", fact_check_blocks_unsupported_cards)
check("The post renders, fits Telegram, explains a trick only once", post_renders_and_fits_telegram)
check("The once-a-week gate works", weekly_gate_works)
check("The bot answers 'tricks', 'deeper' and anything else", bot_replies_work)
if "--live" in sys.argv:
    check("LIVE: every person's sources still describe their invention", live_every_source_holds_up)
    if config.GROQ_API_KEY:
        check("LIVE: write Kiara's real card with the AI", live_card)
    else:
        print("(GROQ_API_KEY not set — the real-card check was not run)")

for ok, name, why in results:
    print(f"{'✅' if ok else '❌'} {name}" + (f"\n     → {why}" if why else ""))
failed = sum(not ok for ok, _, _ in results)
print(f"\n{len(results) - failed}/{len(results)} passed")
sys.exit(1 if failed else 0)
