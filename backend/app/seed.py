import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NPC, NPCMemory, Player, Quest, QuestProgress, RelationshipState


DATA_DIR = Path(__file__).resolve().parent / "data"


def _load_json(filename: str) -> list[dict]:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as data_file:
        return json.load(data_file)


def seed_database(session: Session) -> None:
    if session.get(Player, 1) is None:
        session.add(Player(id=1, name="Hero"))

    for npc_data in _load_json("npcs.json"):
        if session.get(NPC, npc_data["id"]) is None:
            session.add(NPC(**npc_data))

    for quest_data in _load_json("quests.json"):
        if session.get(Quest, quest_data["id"]) is None:
            session.add(Quest(**quest_data))

    required_memories = [
        {
            "npc_id": 1,
            "content": "I noticed footprints near the northern gate after sunset.",
            "keywords": "footprints,gate,north",
            "importance": 3,
            "emotion_tag": "neutral",
            "source_event": "gate_report",
        },
        {
            "npc_id": 2,
            "content": "I do not open the gate without proof of safe passage.",
            "keywords": "gate,proof,passage",
            "importance": 3,
            "emotion_tag": "alert",
            "source_event": "guard_protocol",
        },
        {
            "npc_id": 3,
            "content": "I lost a parcel near the gate road this morning.",
            "keywords": "parcel,merchant,gate",
            "importance": 2,
            "emotion_tag": "neutral",
            "source_event": "merchant_request",
        },
    ]
    for memory_data in required_memories:
        existing_memory = session.scalar(
            select(NPCMemory).where(
                NPCMemory.npc_id == memory_data["npc_id"],
                NPCMemory.content == memory_data["content"],
            )
        )
        if existing_memory is None:
            session.add(NPCMemory(**memory_data))

    for npc_id in (1, 2, 3):
        relationship = session.scalar(
            select(RelationshipState).where(
                RelationshipState.player_id == 1,
                RelationshipState.npc_id == npc_id,
            )
        )
        if relationship is None:
            session.add(RelationshipState(player_id=1, npc_id=npc_id))

    for quest_id in (1, 2, 3):
        progress = session.scalar(
            select(QuestProgress).where(
                QuestProgress.player_id == 1,
                QuestProgress.quest_id == quest_id,
            )
        )
        if progress is None:
            session.add(QuestProgress(player_id=1, quest_id=quest_id))

    session.commit()
