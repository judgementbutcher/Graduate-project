from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import NPC, NPCMemory, Quest, QuestProgress, RelationshipState

router = APIRouter(prefix="/api/npc", tags=["npc"])


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@router.get("/{npc_id}/state")
def npc_state(npc_id: int, player_id: int = 1, session: Session = Depends(get_session)) -> dict:
    npc = session.get(NPC, npc_id)
    if npc is None:
        raise HTTPException(status_code=404, detail=f"NPC {npc_id} not found")

    relation = session.scalar(
        select(RelationshipState).where(
            RelationshipState.player_id == player_id,
            RelationshipState.npc_id == npc_id,
        )
    )
    if relation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Relationship state missing for player {player_id} and npc {npc_id}",
        )

    memories = session.scalars(
        select(NPCMemory)
        .where(NPCMemory.npc_id == npc_id)
        .order_by(NPCMemory.importance.desc(), NPCMemory.id.asc())
    ).all()

    related_quests = session.scalars(
        select(Quest).where(Quest.giver_npc_id == npc_id).order_by(Quest.id.asc())
    ).all()
    progress_rows = session.scalars(
        select(QuestProgress).where(QuestProgress.player_id == player_id)
    ).all()
    progress_by_quest_id = {row.quest_id: row for row in progress_rows}

    return {
        "npc_id": npc.id,
        "name": npc.name,
        "emotion_state": npc.emotion_state,
        "relationship": {
            "favorability": relation.favorability,
            "trust": relation.trust,
            "alertness": relation.alertness,
        },
        "recent_memories": [item.content for item in memories[:2]],
        "related_quests": [
            {
                "quest_id": quest.id,
                "title": quest.title,
                "status": progress_by_quest_id[quest.id].status
                if quest.id in progress_by_quest_id
                else "locked",
                "current_stage": progress_by_quest_id[quest.id].current_stage
                if quest.id in progress_by_quest_id
                else 0,
            }
            for quest in related_quests
        ],
    }
