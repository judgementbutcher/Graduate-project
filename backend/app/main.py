from fastapi import FastAPI

from app.db import SessionLocal, engine
from app.models import Base
from app.seed import seed_database

app = FastAPI(title="Emotion-Driven RPG API")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
