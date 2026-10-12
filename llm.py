"""
llm.py — talks to Groq (the free AI service MicroDigest also uses) and pulls
JSON out of its replies. Waits and retries when the free tier says "slow down".
"""

import json
import re
import time

import requests

import config


def chat(system_prompt, user_prompt, max_tokens, temperature=0.4, label=""):
    """One AI call. Returns the reply text, or "" after logging why it failed."""
    data = {
        "model": config.GROQ_MODEL,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if config.GROQ_MODEL.startswith("openai/gpt-oss"):
        data["reasoning_effort"] = "low"   # keeps the hidden thinking inside the free budget
    headers = {"Authorization": f"Bearer {config.GROQ_API_KEY}"}

    for attempt in range(5):
        try:
            j = requests.post(config.GROQ_URL, json=data, headers=headers, timeout=120).json()
        except Exception as e:
            print(f"[groq{label}] attempt {attempt + 1} failed: {e}")
            time.sleep(3 * (attempt + 1))
            continue
        if "error" in j:
            err = j["error"]
            if err.get("code") == "rate_limit_exceeded" or err.get("type") == "tokens":
                m = re.search(r"try again in ([0-9.]+)s", err.get("message", ""))
                wait = min(float(m.group(1)) + 1.5 if m else 20.0, 65.0)
                print(f"[groq{label}] rate limited; waiting {wait:.0f}s")
                time.sleep(wait)
                continue
            print(f"[groq{label}] API error: {err}")
            return ""
        choice = j["choices"][0]
        if choice.get("finish_reason") == "length":
            print(f"[groq{label}] reply hit the {max_tokens}-token ceiling and was CUT OFF")
        return choice["message"]["content"] or ""
    print(f"[groq{label}] gave up after 5 attempts")
    return ""


def extract_json(text):
    """The JSON object inside a reply, or {} if there is none."""
    if not text:
        return {}
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return {}
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        print(f"[json] reply was not valid JSON ({e}); head: {text[:120]!r}")
        return {}
