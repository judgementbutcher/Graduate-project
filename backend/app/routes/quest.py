from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Quest, QuestProgress

router = APIRouter(prefix="/api/quest", tags=["quest"])


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class QuestUpdateRequest(BaseModel):
    player_id: int
    quest_id: int
    status: str
    current_stage: int


@router.get("/list")
def quest_list(player_id: int, session: Session = Depends(get_session)) -> dict:
    progress_rows = session.scalars(
        select(QuestProgress)
        .where(QuestProgress.player_id == player_id)
        .order_by(QuestProgress.quest_id.asc())
    ).all()
    quest_map = {
        quest.id: quest for quest in session.scalars(select(Quest).order_by(Quest.id.asc())).all()
    }

    return {
        "quests": [
            {
                "quest_id": row.quest_id,
                "title": quest_map[row.quest_id].title,
                "status": row.status,
                "current_stage": row.current_stage,
                "quest_type": quest_map[row.quest_id].quest_type,
                "target_scene": quest_map[row.quest_id].target_scene,
            }
            for row in progress_rows
            if row.quest_id in quest_map
        ]
    }


@router.post("/update")
def update_quest(payload: QuestUpdateRequest, session: Session = Depends(get_session)) -> dict:
    row = session.scalar(
        select(QuestProgress).where(
            QuestProgress.player_id == payload.player_id,
            QuestProgress.quest_id == payload.quest_id,
        )
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Quest progress missing for player {payload.player_id} and quest {payload.quest_id}",
        )

    row.status = payload.status
    row.current_stage = payload.current_stage
    session.commit()
    return {
        "quest_id": payload.quest_id,
        "status": row.status,
        "current_stage": row.current_stage,
    }
