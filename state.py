"""
state.py — the bot's memory, kept as two files in state/ that the workflow
commits back to the repo:
  posted.json        who has been posted, when, with which trick (feeds "tricks")
  latest_story.json  the last card + its source text (feeds "deeper")
"""

import datetime
import json
import os

import config


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def load_posted(path=config.POSTED_PATH):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)   # a corrupt file should stop the run loudly, not reset history


def too_soon(posted):
    """True if the last story went out under ~a week ago. Half a day of slack
    because GitHub's cron often fires an hour or two late."""
    if not posted:
        return False
    last = datetime.datetime.fromisoformat(posted[-1]["date"])
    return now() - last < datetime.timedelta(days=config.SEND_INTERVAL_DAYS - 0.5)


def record(posted, person, card, source_text, source_urls):
    """Append this story to posted.json and overwrite latest_story.json."""
    stamp = now().isoformat()
    posted.append({"key": person["key"], "name": person["name"],
                   "trick": person["trick"], "date": stamp})
    os.makedirs(config.STATE_DIR, exist_ok=True)
    with open(config.POSTED_PATH, "w") as f:
        json.dump(posted, f, indent=2, ensure_ascii=False)
    with open(config.LATEST_PATH, "w") as f:
        json.dump({"key": person["key"], "name": person["name"], "trick": person["trick"],
                   "date": stamp, "card": card.model_dump(), "sources": source_urls,
                   "source_text": source_text[:config.STORED_SOURCE_CHARS]},
                  f, indent=2, ensure_ascii=False)
    print(f"[state] recorded story #{len(posted)}: {person['name']}")
