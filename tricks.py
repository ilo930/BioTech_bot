"""
tricks.py — the invention moves. Every story is tagged with one, so over time
the channel teaches a toolbox you can reuse on your own problems.

The first time a trick appears in the channel, its full explanation is shown;
after that only its name. Send "tricks" to the bot to see the whole toolbox.
"""

TRICKS = {
    "waste_to_resource": {
        "emoji": "♻️", "name": "Waste → resource",
        "explain": "Something people throw away already has the property you need. "
                   "Look in the bin before you look in the shop.",
    },
    "copy_nature": {
        "emoji": "🦎", "name": "Copy nature",
        "explain": "Plants and animals have been testing designs for millions of years. "
                   "Find one that already solved your problem and borrow its shape.",
    },
    "free_physics": {
        "emoji": "☀️", "name": "Use free physics",
        "explain": "Sun, gravity, wind and evaporation work for nothing. "
                   "Let them do the job a motor or a battery would do.",
    },
    "borrow_from_elsewhere": {
        "emoji": "🔀", "name": "Borrow from another field",
        "explain": "An idea that is ordinary in one world can be new in another. "
                   "Carry it across.",
    },
    "strip_it_down": {
        "emoji": "🪚", "name": "Strip it down",
        "explain": "Find the expensive part and remove it, so everyone can afford "
                   "the thing. Simpler often beats better.",
    },
    "use_whats_local": {
        "emoji": "🧺", "name": "Use what's around you",
        "explain": "Scrap, local plants, what the village already has. "
                   "The limit becomes the design.",
    },
    "flip_the_problem": {
        "emoji": "🔄", "name": "Flip the problem",
        "explain": "Turn the question around. Ask what the problem itself wants, "
                   "or what would make it go away on its own.",
    },
    "old_knowledge": {
        "emoji": "📜", "name": "Dig up old knowledge",
        "explain": "Someone may have half-solved it centuries ago. "
                   "Old books and traditional remedies are a mine.",
    },
}


def label(key):
    t = TRICKS[key]
    return f"{t['emoji']} {t['name']}"
