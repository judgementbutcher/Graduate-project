from collections.abc import Generator

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.services.save_service import read_save, write_save

router = APIRouter(prefix="/api/save", tags=["save"])


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class SaveRequest(BaseModel):
    player_id: int
    scene_id: str
    position_x: float
    position_y: float


@router.post("/create")
def create_save(payload: SaveRequest, session: Session = Depends(get_session)) -> dict[str, str]:
    return write_save(session, payload.model_dump())


@router.get("/load")
def load_save(player_id: int, session: Session = Depends(get_session)) -> dict[str, int | float | str]:
    return read_save(session, player_id)
