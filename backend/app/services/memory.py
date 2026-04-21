from __future__ import annotations

import re


def _extract_words(text: str) -> set[str]:
    return set(re.findall(r"\b\w+\b", text.lower()))


def _keyword_hit_count(query: str, memory: dict) -> int:
    query_words = _extract_words(query)
    keyword_words: set[str] = set()
    for chunk in memory.get("keywords", "").split(","):
        keyword_words.update(_extract_words(chunk))
    return sum(1 for keyword in keyword_words if keyword in query_words)


def score_memory(query: str, emotion_label: str, memory: dict) -> float:
    hit_count = _keyword_hit_count(query, memory)
    importance = float(memory.get("importance", 0))
    emotion_bonus = 1.0 if memory.get("emotion_tag") == emotion_label else 0.0
    return hit_count + importance + emotion_bonus


def top_memories(
    query: str,
    emotion_label: str,
    memories: list[dict],
    limit: int = 2,
) -> list[dict]:
    scored = [
        (memory, score_memory(query, emotion_label, memory))
        for memory in memories
        if _keyword_hit_count(query, memory) > 0
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    return [memory for memory, _score in scored[:limit]]
