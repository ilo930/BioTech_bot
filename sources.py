"""
sources.py — fetches the text a story is written from: Wikipedia pages and
trusted news articles. This text is the ONLY place facts about the person may
come from, and it must actually describe the invention (see must_mention).
"""

import html
import re

import requests

import config

WIKI_API = "https://en.wikipedia.org/w/api.php"

# Long pages (Hedy Lamarr is 33,000 characters, mostly film career) are trimmed to
# the intro, the sections about the invention, and any paragraph naming the person.
KEEP_SECTION = re.compile(
    r"invent|patent|career|research|work|science|design|innovation|award|"
    r"development|technology|description|operation|history|use|impact|legacy",
    re.I)


class SourceTooThin(Exception):
    """The source pages don't describe the invention — writing from them would
    force the AI to make it up."""


def fetch_wikipedia(title):
    """(real title, plain text, url). Raises if the page is missing or empty."""
    r = requests.get(WIKI_API, timeout=30, headers={"User-Agent": config.USER_AGENT}, params={
        "action": "query", "prop": "extracts", "explaintext": 1, "redirects": 1,
        "format": "json", "titles": title})
    r.raise_for_status()
    page = next(iter(r.json()["query"]["pages"].values()))
    text = page.get("extract", "")
    if "missing" in page or not text.strip():
        raise LookupError(f"Wikipedia page not found or empty: {title!r}")
    return page["title"], text, "https://en.wikipedia.org/wiki/" + page["title"].replace(" ", "_")


def article_text(raw_html):
    """The readable paragraphs of a news page, without scripts, styles and menus."""
    s = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw_html, flags=re.S | re.I)
    paragraphs = (re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", p))).strip()
                  for p in re.findall(r"<p[^>]*>(.*?)</p>", s, flags=re.S | re.I))
    return "\n".join(p for p in paragraphs if len(p) > 40)


def fetch_article(url):
    """(site name, plain text, url). Raises on a dead or empty page."""
    r = requests.get(url, timeout=30, headers={"User-Agent": config.USER_AGENT})
    r.raise_for_status()
    text = article_text(r.text)
    if not text:
        raise LookupError(f"no readable paragraphs at {url}")
    return url.split("/")[2].replace("www.", ""), text, url


def focus(text, limit, names=()):
    """Intro + invention sections + paragraphs mentioning `names`, cut to `limit`."""
    parts = re.split(r"\n(={2,} .+? ={2,})\n", text)
    kept = [parts[0].strip()]
    for heading, body in zip(parts[1::2], parts[2::2]):
        if KEEP_SECTION.search(heading) and body.strip():
            kept.append(f"{heading.strip('= ')}:\n{body.strip()}")
        else:
            kept += [p for p in body.split("\n") if any(n in p for n in names)]
    return "\n\n".join(k for k in kept if k)[:limit]


def share_budget(lengths, limit):
    """How many characters each source may keep. A short source keeps all of
    itself and hands what it didn't use to the longer ones — an even split
    once cut Kiara's CNN article in half and lost her own explanation."""
    caps, left, todo = [0] * len(lengths), limit, sorted(range(len(lengths)), key=lengths.__getitem__)
    for n, i in enumerate(todo):
        caps[i] = min(lengths[i], left // (len(todo) - n))
        left -= caps[i]
    return caps


def gather(person):
    """Fetch every source for a person. Returns (text, urls).
    Raises SourceTooThin if the words the story depends on are not in them."""
    surname = person["name"].split()[-1]
    labels, texts, urls = [], [], []
    for src in person["sources"]:
        fetch = fetch_article if src.startswith("http") else fetch_wikipedia
        label, text, url = fetch(src)
        labels.append(label)
        texts.append(focus(text, config.SOURCE_CHARS, (surname,)))
        urls.append(url)
    caps = share_budget([len(t) for t in texts], config.SOURCE_CHARS)
    combined = "\n\n".join(f"[Source: {l}]\n{t[:c]}" for l, t, c in zip(labels, texts, caps))
    missing = [w for w in person["must_mention"] if w.lower() not in combined.lower()]
    if missing:
        raise SourceTooThin(f"{person['name']}: sources never mention {missing}")
    return combined, urls
