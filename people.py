"""
people.py — the curated list. Real people only: every entry names the
sources the story is written from (Wikipedia page titles, or full URLs of
trusted news articles), and nothing else is used.

must_mention: words the sources MUST contain. Wikipedia pages get rewritten
(Kiara Nirghin's page lost her orange-peel invention in 2026); if the words are
gone, the person is skipped instead of letting the AI invent the story.

Stories go out in this order. To add someone: pick
the trick their invention uses (see tricks.py), append a line,
then run `python3 smoke_test.py --live` to check every source still holds up.

kind: young (teen/student inventor) · grassroots (low-cost local fix)
      forgotten (history overlooked them) · earth (helps the planet)
"""

PEOPLE = [
    {"key": "kiara_nirghin", "name": "Kiara Nirghin", "country": "ZA", "kind": "young",
     "trick": "waste_to_resource", "must_mention": ["orange", "avocado"],
     "sources": ["https://edition.cnn.com/2016/08/09/africa/orange-drought-kiara-nirghin/index.html",
                 "Google Science Fair"]},
    {"key": "mohammed_bah_abba", "name": "Mohammed Bah Abba", "country": "NG", "kind": "grassroots",
     "trick": "free_physics", "must_mention": ["pot", "sand"],
     "sources": ["Mohammed Bah Abba", "Pot-in-pot refrigerator"]},
    {"key": "george_de_mestral", "name": "George de Mestral", "country": "CH", "kind": "forgotten",
     "trick": "copy_nature", "must_mention": ["burr", "Velcro"],
     "sources": ["George de Mestral"]},
    {"key": "william_kamkwamba", "name": "William Kamkwamba", "country": "MW", "kind": "young",
     "trick": "use_whats_local", "must_mention": ["windmill"],
     "sources": ["William Kamkwamba"]},
    {"key": "hedy_lamarr", "name": "Hedy Lamarr", "country": "AT", "kind": "forgotten",
     "trick": "borrow_from_elsewhere", "must_mention": ["frequency"],
     "sources": ["Hedy Lamarr"]},
    {"key": "arunachalam_muruganantham", "name": "Arunachalam Muruganantham", "country": "IN",
     "kind": "grassroots", "trick": "strip_it_down", "must_mention": ["sanitary"],
     "sources": ["Arunachalam Muruganantham"]},
    {"key": "mick_pearce", "name": "Mick Pearce", "country": "ZW", "kind": "earth",
     "trick": "copy_nature", "must_mention": ["Eastgate", "termite"],
     "sources": ["Mick Pearce"]},
    {"key": "alice_ball", "name": "Alice Ball", "country": "US", "kind": "forgotten",
     "trick": "old_knowledge", "must_mention": ["chaulmoogra"],
     "sources": ["Alice Ball"]},
    {"key": "gitanjali_rao", "name": "Gitanjali Rao", "country": "US", "kind": "young",
     "trick": "borrow_from_elsewhere", "must_mention": ["Tethys", "lead"],
     "sources": ["Gitanjali Rao (inventor)"]},
    {"key": "alfredo_moser", "name": "Alfredo Moser", "country": "BR", "kind": "grassroots",
     "trick": "free_physics", "must_mention": ["Moser", "bottle"],
     "sources": ["Liter of Light"]},
    {"key": "lewis_latimer", "name": "Lewis Latimer", "country": "US", "kind": "forgotten",
     "trick": "strip_it_down", "must_mention": ["filament"],
     "sources": ["Lewis Howard Latimer"]},
]


def upcoming(posted_keys):
    """Everyone not yet posted, in list order (empty when the list is used up)."""
    return [p for p in PEOPLE if p["key"] not in posted_keys]
