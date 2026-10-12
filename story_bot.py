"""
story_bot.py — the weekly run. Wires the steps together:
pick the next person → fetch their sources → write the card → check it → post → remember.
"""

import config
import people
import sources
import state
import telegram
import writer
from card_format import format_post


def pick_person(posted):
    """The first upcoming person whose sources still describe the invention.
    Someone whose sources fail is skipped this week (not marked posted)."""
    for person in people.upcoming({p["key"] for p in posted}):
        try:
            source_text, urls = sources.gather(person)
        except sources.SourceTooThin as e:
            print(f"[run] SKIPPED — {e}. Fix their sources in people.py.")
            continue
        print(f"[run] this week: {person['name']}")
        return person, source_text, urls
    print("[run] nobody left with usable sources — add people to people.py")
    raise SystemExit(1)   # red run, so the empty list gets noticed


def main():
    print(f"[run] BioTech (dry_run={config.DRY_RUN}, model={config.GROQ_MODEL})")
    posted = state.load_posted()

    if state.too_soon(posted) and not (config.DRY_RUN or config.FORCE_SEND):
        print("[run] last story is under a week old — nothing to do today")
        return

    person, source_text, urls = pick_person(posted)
    card = writer.write_card(person, source_text)
    if not card:
        print("[run] no complete card after two tries — holding the story; "
              "nothing marked as posted, the next run retries")
        raise SystemExit(1)

    first_time = person["trick"] not in {p["trick"] for p in posted}
    post = format_post(person, card, len(posted) + 1, first_time, urls)
    if len(post) > config.TELEGRAM_LIMIT:
        print(f"[run] card is {len(post)} characters, over Telegram's "
              f"{config.TELEGRAM_LIMIT} — holding it")
        raise SystemExit(1)

    if not telegram.send(config.TELEGRAM_CHAT_ID, post):
        raise SystemExit(1)
    if not config.DRY_RUN:
        state.record(posted, person, card, source_text, urls)
    print("[run] done")


if __name__ == "__main__":
    main()
