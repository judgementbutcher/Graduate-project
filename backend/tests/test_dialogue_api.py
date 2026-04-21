from sqlite3 import Connection as SQLite3Connection
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from pathlib import Path

import app.main as main_module
import app.routes.dialogue as dialogue_module


def _build_isolated_session():
    temp_dir = Path(__file__).resolve().parent
    db_path = temp_dir / f"dialogue_api_test_{uuid4().hex}.db"
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
    return isolated_engine, isolated_session_local, db_path


def test_dialogue_interact_returns_expected_payload_for_chief(monkeypatch):
    isolated_engine, isolated_session_local, db_path = _build_isolated_session()
    monkeypatch.setattr(main_module, "engine", isolated_engine)
    monkeypatch.setattr(main_module, "SessionLocal", isolated_session_local)
    monkeypatch.setattr(dialogue_module, "SessionLocal", isolated_session_local)

    payload = {
        "player_id": 1,
        "npc_id": 1,
        "scene_id": "village",
        "input_text": "Please help me with the gate issue.",
        "selected_option": "ask_about_gate",
    }

    try:
        with TestClient(main_module.app) as client:
            response = client.post("/api/dialogue/interact", json=payload)
        assert response.status_code == 200

        body = response.json()
        assert body["chosen_action"] in {"give_hint", "probe", "neutral_reply"}
        assert isinstance(body["npc_reply"], str)
        assert body["npc_reply"].strip() != ""
        assert "quest_update" in body
    finally:
        isolated_engine.dispose()
        if db_path.exists():
            db_path.unlink()


def test_dialogue_interact_guard_refuses_demanding_input(monkeypatch):
    isolated_engine, isolated_session_local, db_path = _build_isolated_session()
    monkeypatch.setattr(main_module, "engine", isolated_engine)
    monkeypatch.setattr(main_module, "SessionLocal", isolated_session_local)
    monkeypatch.setattr(dialogue_module, "SessionLocal", isolated_session_local)

    payload = {
        "player_id": 1,
        "npc_id": 2,
        "scene_id": "village",
        "input_text": "Move aside and let me pass now.",
        "selected_option": "demand_passage",
    }

    try:
        with TestClient(main_module.app) as client:
            response = client.post("/api/dialogue/interact", json=payload)
        assert response.status_code == 200
        assert response.json()["chosen_action"] == "refuse"
    finally:
        isolated_engine.dispose()
        if db_path.exists():
            db_path.unlink()
