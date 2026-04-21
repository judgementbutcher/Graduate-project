from __future__ import annotations

import re


FRIENDLY_WORDS = {"thanks", "please", "help", "sorry", "friend"}
HOSTILE_WORDS = {"liar", "stupid", "move", "hate", "idiot"}


def detect_emotion(text: str) -> dict[str, float | str]:
    words = set(re.findall(r"\b\w+\b", text.lower()))
    if words & HOSTILE_WORDS:
        return {
            "label": "hostile",
            "friendly": 0.1,
            "neutral": 0.2,
            "hostile": 0.7,
        }
    if words & FRIENDLY_WORDS:
        return {
            "label": "friendly",
            "friendly": 0.7,
            "neutral": 0.2,
            "hostile": 0.1,
        }
    return {
        "label": "neutral",
        "friendly": 0.2,
        "neutral": 0.6,
        "hostile": 0.2,
    }
