from __future__ import annotations

import re


def score_memory(query: str, emotion_label: str, memory: dict) -> float:
    query_words = set(re.findall(r"\b\w+\b", query.lower()))
    keywords = [part.strip().lower() for part in memory.get("keywords", "").split(",")]
    hit_count = sum(1 for keyword in keywords if keyword and keyword in query_words)
    importance = float(memory.get("importance", 0))
    emotion_bonus = 1.0 if memory.get("emotion_tag") == emotion_label else 0.0
    return hit_count + importance + emotion_bonus


def top_memories(
    query: str,
    emotion_label: str,
    memories: list[dict],
    limit: int = 2,
) -> list[dict]:
    return sorted(
        memories,
        key=lambda memory: score_memory(query, emotion_label, memory),
        reverse=True,
    )[:limit]
