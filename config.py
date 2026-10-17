"""
config.py — every setting in one place: secrets (read from the environment,
never written here), cadence, model and file paths.
"""

import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")   # the channel, @xbiotechx
BOT_USERNAME = "MicroBioTech_bot"   # readers message it for "deeper" and "tricks"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

DRY_RUN = os.environ.get("DRY_RUN", "") == "1"       # print the card, send nothing
FORCE_SEND = os.environ.get("FORCE_SEND", "") == "1"  # manual runs skip the weekly gate

# The cron fires daily; a story only goes out once a week. A missed cron day then
# delays the story by a day instead of skipping a whole week.
SEND_INTERVAL_DAYS = 7

GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
CARD_MAX_TOKENS = 2500
DEEPER_MAX_TOKENS = 2000
CHECK_MAX_TOKENS = 1500

SOURCE_CHARS = 8000        # how much source text the writer may read (all sources together)
STORED_SOURCE_CHARS = SOURCE_CHARS  # "deeper" reads the same full text
TELEGRAM_LIMIT = 4096

# Wikipedia asks every bot to name itself and give a way to reach its owner.
USER_AGENT = "BioTechBot/0.1 (weekly invention stories; https://github.com/ilo930/BioTech_bot)"

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(HERE, "state")
POSTED_PATH = os.path.join(STATE_DIR, "posted.json")
LATEST_PATH = os.path.join(STATE_DIR, "latest_story.json")
