from __future__ import annotations


def choose_action(
    npc_role: str,
    emotion_label: str,
    relation: dict,
    top_memories: list[dict],
    quest_state: dict,
) -> str:
    trust = relation.get("trust", 0)
    if npc_role == "guard" and trust < 1 and not quest_state.get(
        "parcel_done", False
    ):
        return "refuse"
    if npc_role == "merchant" and quest_state.get("parcel_done", False):
        return "give_clue"
    if npc_role == "chief" and emotion_label == "friendly":
        return "give_hint"
    if emotion_label == "hostile":
        return "warn"
    if top_memories:
        return "probe"
    return "neutral_reply"
