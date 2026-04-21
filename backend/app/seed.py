import json
from pathlib import Path

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models import NPC, NPCMemory, Player, Quest, QuestProgress, RelationshipState


DATA_DIR = Path(__file__).resolve().parent / "data"


def _load_json(filename: str) -> list[dict]:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as data_file:
        return json.load(data_file)


def seed_database(session: Session) -> None:
    session.execute(
        sqlite_insert(Player)
        .values(id=1, name="Hero")
        .on_conflict_do_nothing(index_elements=["id"])
    )

    for npc_data in _load_json("npcs.json"):
        session.execute(
            sqlite_insert(NPC)
            .values(**npc_data)
            .on_conflict_do_nothing(index_elements=["id"])
        )

    for quest_data in _load_json("quests.json"):
        session.execute(
            sqlite_insert(Quest)
            .values(**quest_data)
            .on_conflict_do_nothing(index_elements=["id"])
        )

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
        session.execute(
            sqlite_insert(NPCMemory)
            .values(**memory_data)
            .on_conflict_do_nothing(index_elements=["npc_id", "content"])
        )

    for npc_id in (1, 2, 3):
        session.execute(
            sqlite_insert(RelationshipState)
            .values(player_id=1, npc_id=npc_id)
            .on_conflict_do_nothing(index_elements=["player_id", "npc_id"])
        )

    for quest_id in (1, 2, 3):
        session.execute(
            sqlite_insert(QuestProgress)
            .values(player_id=1, quest_id=quest_id)
            .on_conflict_do_nothing(index_elements=["player_id", "quest_id"])
        )
