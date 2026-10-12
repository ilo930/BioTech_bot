"""
poller.py — the listener. A GitHub Actions job runs this for ~5.5 hours at a
time: it long-polls Telegram for DMs, answers them via reply_core, then exits
and the next queued run takes over (same setup as MicroDigest's reply bot).
"""

import os
import time

import requests

import config
import reply_core
import telegram

API = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}"
RUN_SECONDS = int(os.environ.get("RUN_SECONDS", "270"))
LONG_POLL = 25

COMMANDS = [   # the tappable "/" menu in Telegram
    {"command": "deeper", "description": "The science of this week's story"},
    {"command": "tricks", "description": "The invention toolbox"},
    {"command": "menu", "description": "Show all options"},
]


def setup_bot():
    me = requests.get(f"{API}/getMe", timeout=10).json()
    print(f"[poller] bot is @{(me.get('result') or {}).get('username')}")
    r = requests.post(f"{API}/setMyCommands", json={"commands": COMMANDS}, timeout=10).json()
    print(f"[poller] setMyCommands ok={r.get('ok')}")


def answer(update):
    msg = update.get("message") or update.get("edited_message") or {}
    chat, text = (msg.get("chat") or {}).get("id"), msg.get("text", "")
    if not (chat and text):
        return
    print(f"[poller] message: {text!r}")
    try:
        replies = reply_core.handle_text(text)
    except Exception as e:
        print(f"[poller] handler error: {e!r}")
        replies = ["Something went wrong on my side — send <b>menu</b> to try again."]
    for reply in replies:
        telegram.send(chat, reply)


def main():
    if not config.TELEGRAM_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN not set")
    requests.get(f"{API}/deleteWebhook", timeout=10)   # polling and webhooks can't coexist
    setup_bot()
    offset, deadline = None, time.time() + RUN_SECONDS
    print(f"[poller] listening for ~{RUN_SECONDS}s")
    while time.time() < deadline:
        try:
            params = {"timeout": LONG_POLL, **({"offset": offset} if offset else {})}
            data = requests.get(f"{API}/getUpdates", params=params, timeout=LONG_POLL + 10).json()
        except Exception as e:
            print(f"[poller] getUpdates failed: {e}")
            time.sleep(3)
            continue
        if not data.get("ok"):
            print(f"[poller] getUpdates not ok: {data.get('description')}")
            time.sleep(3)
            continue
        for update in data.get("result", []):
            offset = update["update_id"] + 1
            answer(update)
    print("[poller] done")


if __name__ == "__main__":
    main()
