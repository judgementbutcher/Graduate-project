from collections.abc import Generator

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.schemas import DialogueRequest, DialogueResponse
from app.services.dialogue import run_dialogue

router = APIRouter(prefix="/api/dialogue", tags=["dialogue"])


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@router.post("/interact", response_model=DialogueResponse)
def interact(
    payload: DialogueRequest, session: Session = Depends(get_session)
) -> DialogueResponse:
    result = run_dialogue(session, payload)
    return DialogueResponse(**result)
