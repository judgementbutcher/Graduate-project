from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import SessionLocal
from app.main import app
from app.models import NPC, Player, Quest

def test_health_endpoint_returns_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_startup_bootstraps_seed_data():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    with SessionLocal() as session:
        hero = session.scalar(select(Player).where(Player.id == 1))
        npc_count = len(session.scalars(select(NPC)).all())
        quest_count = len(session.scalars(select(Quest)).all())

    assert hero is not None
    assert hero.name == "Hero"
    assert npc_count == 3
    assert quest_count == 3
