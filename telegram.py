"""
telegram.py — sends one message to Telegram. In dry-run mode it prints instead.
"""

import requests

import config


def send(chat_id, text):
    """True if Telegram accepted the message; logs Telegram's reason otherwise."""
    if config.DRY_RUN:
        print("\n" + "=" * 64 + "\n" + text + "\n" + "=" * 64)
        return True
    if not (config.TELEGRAM_TOKEN and chat_id):
        print("[telegram] TELEGRAM_BOT_TOKEN or chat id not set — nothing sent")
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage",
                          json={"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                                "disable_web_page_preview": True}, timeout=20).json()
    except Exception as e:
        print(f"[telegram] send failed: {e}")
        return False
    if not r.get("ok"):
        print(f"[telegram] refused: {r.get('description')}")
    return bool(r.get("ok"))
