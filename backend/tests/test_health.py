from sqlite3 import Connection as SQLite3Connection
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from pathlib import Path

import app.main as main_module
from app.main import app
from app.models import NPC, Player, Quest

def test_health_endpoint_returns_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_startup_bootstraps_seed_data(monkeypatch):
    temp_dir = Path(__file__).resolve().parent / "_tmp"
    temp_dir.mkdir(exist_ok=True)
    db_path = temp_dir / f"startup_test_{uuid4().hex}.db"
    isolated_db_url = f"sqlite:///{db_path.as_posix()}"
    isolated_engine = create_engine(
        isolated_db_url,
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(isolated_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        if isinstance(dbapi_connection, SQLite3Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    isolated_session_local = sessionmaker(
        bind=isolated_engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    monkeypatch.setattr(main_module, "engine", isolated_engine)
    monkeypatch.setattr(main_module, "SessionLocal", isolated_session_local)

    with TestClient(main_module.app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    with isolated_session_local() as session:
        hero = session.scalar(select(Player).where(Player.id == 1))
        npc_count = len(session.scalars(select(NPC)).all())
        quest_count = len(session.scalars(select(Quest)).all())

    assert hero is not None
    assert hero.name == "Hero"
    assert npc_count == 3
    assert quest_count == 3
