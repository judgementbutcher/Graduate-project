from sqlite3 import Connection as SQLite3Connection
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker
from pathlib import Path

import app.main as main_module
import app.routes.dialogue as dialogue_module
from app.models import DialogueLog, QuestProgress, RelationshipState


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
        assert body["chosen_action"] == "give_hint"
        assert (
            body["npc_reply"]
            == "The chief lowers his voice. 'Check the northern gate. Something changed there last night.'"
        )
        assert body["quest_update"] == "main_started"

        with isolated_session_local() as session:
            relationship = session.scalar(
                select(RelationshipState).where(
                    RelationshipState.player_id == 1,
                    RelationshipState.npc_id == 1,
                )
            )
            quest_one = session.scalar(
                select(QuestProgress).where(
                    QuestProgress.player_id == 1,
                    QuestProgress.quest_id == 1,
                )
            )
            log = session.scalar(select(DialogueLog).order_by(DialogueLog.id.desc()))

        assert relationship is not None
        assert relationship.favorability == 1
        assert relationship.trust == 1
        assert relationship.alertness == 0

        assert quest_one is not None
        assert quest_one.status == "active"
        assert quest_one.current_stage == 1

        assert log is not None
        assert log.player_id == payload["player_id"]
        assert log.npc_id == payload["npc_id"]
        assert log.player_input == payload["input_text"]
        assert log.emotion_result == body["emotion_result"]
        assert log.chosen_action == body["chosen_action"]
        assert log.npc_reply == body["npc_reply"]
        assert log.quest_update == body["quest_update"]
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


def test_dialogue_interact_chief_does_not_rewind_progressed_quest(monkeypatch):
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
            with isolated_session_local() as session:
                quest_one = session.scalar(
                    select(QuestProgress).where(
                        QuestProgress.player_id == 1,
                        QuestProgress.quest_id == 1,
                    )
                )
                assert quest_one is not None
                quest_one.status = "completed"
                quest_one.current_stage = 3
                session.commit()

            response = client.post("/api/dialogue/interact", json=payload)
            assert response.status_code == 200
            body = response.json()
            assert body["chosen_action"] == "give_hint"
            assert body["quest_update"] == "none"

            with isolated_session_local() as session:
                quest_after = session.scalar(
                    select(QuestProgress).where(
                        QuestProgress.player_id == 1,
                        QuestProgress.quest_id == 1,
                    )
                )
            assert quest_after is not None
            assert quest_after.status == "completed"
            assert quest_after.current_stage == 3
    finally:
        isolated_engine.dispose()
        if db_path.exists():
            db_path.unlink()
