from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DialogueLog, NPC, NPCMemory, QuestProgress, RelationshipState
from app.schemas import DialogueRequest
from app.services.decision import choose_action
from app.services.emotion import detect_emotion
from app.services.memory import top_memories


REPLY_TEMPLATES = {
    "give_hint": "The chief lowers his voice. 'Check the northern gate. Something changed there last night.'",
    "probe": "The NPC studies you carefully before answering with another question.",
    "refuse": "The guard folds his arms. 'No proof, no passage.'",
    "warn": "The NPC stiffens. 'Watch your tone if you want help.'",
    "give_clue": "Merchant Lin nods. 'You earned this clue. I saw tracks near the old gate.'",
    "neutral_reply": "The NPC offers a short, cautious reply.",
}


def run_dialogue(session: Session, payload: DialogueRequest) -> dict:
    npc = session.scalar(select(NPC).where(NPC.id == payload.npc_id))
    if npc is None:
        raise ValueError(f"NPC {payload.npc_id} not found")

    relationship = session.scalar(
        select(RelationshipState).where(
            RelationshipState.player_id == payload.player_id,
            RelationshipState.npc_id == payload.npc_id,
        )
    )

    memory_rows = session.scalars(select(NPCMemory).where(NPCMemory.npc_id == payload.npc_id)).all()
    memories = [
        {
            "content": memory.content,
            "keywords": memory.keywords,
            "importance": memory.importance,
            "emotion_tag": memory.emotion_tag,
        }
        for memory in memory_rows
    ]

    quest_rows = session.scalars(
        select(QuestProgress).where(QuestProgress.player_id == payload.player_id)
    ).all()
    quest_by_id = {quest.quest_id: quest for quest in quest_rows}
    quest_state = {
        "main_stage": quest_by_id[1].current_stage if 1 in quest_by_id else 0,
        "parcel_done": 2 in quest_by_id and quest_by_id[2].status == "completed",
    }

    emotion = detect_emotion(payload.input_text)
    emotion_label = str(emotion["label"])
    selected_memories = top_memories(payload.input_text, emotion_label, memories)
    chosen_action = choose_action(
        npc_role=npc.role,
        emotion_label=emotion_label,
        relation={"trust": relationship.trust},
        top_memories=selected_memories,
        quest_state=quest_state,
    )

    delta = {"favorability": 0, "trust": 0, "alertness": 0}
    if emotion_label == "friendly":
        delta["favorability"] += 1
        delta["trust"] += 1
    elif emotion_label == "hostile":
        delta["alertness"] += 1

    relationship.favorability += delta["favorability"]
    relationship.trust += delta["trust"]
    relationship.alertness += delta["alertness"]

    quest_update = "none"
    if payload.npc_id == 1 and chosen_action == "give_hint":
        quest_one = quest_by_id.get(1)
        if quest_one is not None:
            quest_one.status = "active"
            quest_one.current_stage = 1
            quest_update = "main_started"

    npc_reply = REPLY_TEMPLATES.get(chosen_action, REPLY_TEMPLATES["neutral_reply"])

    session.add(
        DialogueLog(
            player_id=payload.player_id,
            npc_id=payload.npc_id,
            player_input=payload.input_text,
            emotion_result=emotion_label,
            chosen_action=chosen_action,
            npc_reply=npc_reply,
            quest_update=quest_update,
        )
    )
    session.commit()

    return {
        "npc_reply": npc_reply,
        "emotion_result": emotion_label,
        "chosen_action": chosen_action,
        "relationship_change": delta,
        "quest_update": quest_update,
    }
