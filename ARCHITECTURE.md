# Architecture

## What this project is
BioTech: a Telegram channel (@xbiotechx) that posts one real inventor's story a week —
what the invention is made of, why it works, and the reusable "trick" behind it —
so the reader builds a toolbox for inventing. A DM bot answers `deeper` and `tricks`.

## Style
Pipeline: each weekly step is one file that hands its result to the next.
(Same shape as MicroDigests_bot, its sibling; nothing is shared between the two repos.)

## Who feeds whom
```
people.py ─► sources.py ─► writer.py ◄─► fact_check.py
 (who next)   (Wikipedia /   (AI writes)    (2nd AI: claims vs source)
              news text)         │
                                 ▼
                          card_format.py ─► telegram.py ─► @xbiotechx
                    story_bot.py wires them; state.py remembers who was posted
DM ─► poller.py ─► reply_core.py ─► deeper (AI + stored source) / tricks (tricks.py + posted.json)
```

## Map
| File | What it does |
|---|---|
| people.py | The curated list: real people, their sources, their trick, must-mention words |
| tricks.py | The 8 invention moves and their plain explanations |
| sources.py | Fetches Wikipedia pages and news articles; refuses sources that don't describe the invention |
| writer.py | The AI prompt; checks every part of the card is there; retries with the checker's notes |
| fact_check.py | Second AI pass: lists every claim the source doesn't back up; any → card refused |
| card_format.py | Turns a card into the Telegram post — all the post's look lives here |
| llm.py | Talks to Groq (free AI), retries when rate-limited |
| telegram.py | Sends one message (prints it instead in dry-run) |
| state.py | `state/posted.json` (who, when, which trick) and `state/latest_story.json` |
| story_bot.py | The weekly run |
| reply_core.py / poller.py | The DM bot: what to answer / listening to Telegram |
| config.py | Every setting; secrets come from the environment only |
| .github/workflows/ | `story-bot.yml` daily cron + weekly gate · `reply-bot.yml` always-on listener |

## How to run it
- Check it works: `.venv/bin/python smoke_test.py` (offline) · add `--live` to test every real source
- Preview a card: GitHub → Actions → "BioTech weekly story" → Run workflow (dry run is ticked by default)
- Locally: `GROQ_API_KEY=… DRY_RUN=1 .venv/bin/python story_bot.py`

## Decisions
- Fact-check pass added (2026-10-17). The first real card gave the orange's pectin to the avocado,
  listed "water" as an ingredient and invented farm trials. Prompt rules alone weren't enough.
- Posts go to the public channel @xbiotechx (FH tried his private chat first, then chose a channel 2026-10-17).
  The bot is @MicroBioTech_bot; `deeper`/`tricks` work in a private chat with it.
- Sources carry `must_mention` words. (Wikipedia rewrote Kiara Nirghin's page in 2026 and dropped the
  orange peel; a "Gitanjali Rao" title pointed to a different person. Without the gate the AI would invent.)
- News URLs allowed as sources next to Wikipedia, for inventors Wikipedia covers badly.
- Curated list over AI-found people. (AI discovery considered; rejected — risk of made-up inventors.)
- Trick is chosen by hand per person; the AI only explains how it applies.
- Repo must be public: the always-on listener needs ~43,000 Actions minutes a month; private gets 2,000.

## Known rough edges
- 11 people ≈ 11 weeks. The list needs topping up; the run goes red when nobody is left.
- News-article reading keeps every `<p>` over 40 characters, so a few captions slip in.
