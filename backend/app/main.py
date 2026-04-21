from fastapi import FastAPI

from app.db import SessionLocal, engine
from app.models import Base
from app.routes.dialogue import router as dialogue_router
from app.routes.npc import router as npc_router
from app.routes.quest import router as quest_router
from app.routes.save import router as save_router
from app.seed import seed_database

app = FastAPI(title="Emotion-Driven RPG API")
app.include_router(dialogue_router)
app.include_router(npc_router)
app.include_router(quest_router)
app.include_router(save_router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session)
        session.commit()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
