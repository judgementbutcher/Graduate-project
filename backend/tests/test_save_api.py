import importlib
from pathlib import Path
from sqlite3 import Connection as SQLite3Connection
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

import app.main as main_module
from app.models import Player, QuestProgress


def _build_isolated_session():
    temp_dir = Path(__file__).resolve().parent
    db_path = temp_dir / f"save_api_test_{uuid4().hex}.db"
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


def _patch_session_sources(monkeypatch, isolated_engine, isolated_session_local) -> None:
    monkeypatch.setattr(main_module, "engine", isolated_engine)
    monkeypatch.setattr(main_module, "SessionLocal", isolated_session_local)

    for module_name in (
        "app.routes.dialogue",
        "app.routes.npc",
        "app.routes.quest",
        "app.routes.save",
    ):
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        monkeypatch.setattr(module, "SessionLocal", isolated_session_local)


def test_npc_state_endpoint_returns_relationship_and_memories(monkeypatch):
    isolated_engine, isolated_session_local, db_path = _build_isolated_session()
    _patch_session_sources(monkeypatch, isolated_engine, isolated_session_local)

    try:
        with TestClient(main_module.app) as client:
            response = client.get("/api/npc/1/state", params={"player_id": 1})

        assert response.status_code == 200
        body = response.json()
        assert body["npc_id"] == 1
        assert body["name"] == "Village Chief"
        assert body["emotion_state"] == "neutral"
        assert body["relationship"] == {"favorability": 0, "trust": 0, "alertness": 0}
        assert body["recent_memories"] == [
            "I noticed footprints near the northern gate after sunset."
        ]
    finally:
        isolated_engine.dispose()
        if db_path.exists():
            db_path.unlink()


def test_quest_list_endpoint_returns_three_quests(monkeypatch):
    isolated_engine, isolated_session_local, db_path = _build_isolated_session()
    _patch_session_sources(monkeypatch, isolated_engine, isolated_session_local)

    try:
        with TestClient(main_module.app) as client:
            response = client.get("/api/quest/list", params={"player_id": 1})

        assert response.status_code == 200
        body = response.json()
        assert len(body["quests"]) == 3
        assert body["quests"][0]["title"] == "Strange Footprints"
        assert body["quests"][0]["status"] == "locked"
    finally:
        isolated_engine.dispose()
        if db_path.exists():
            db_path.unlink()


def test_quest_update_endpoint_advances_status(monkeypatch):
    isolated_engine, isolated_session_local, db_path = _build_isolated_session()
    _patch_session_sources(monkeypatch, isolated_engine, isolated_session_local)

    try:
        with TestClient(main_module.app) as client:
            response = client.post(
                "/api/quest/update",
                json={"player_id": 1, "quest_id": 2, "status": "completed", "current_stage": 2},
            )

        assert response.status_code == 200
        assert response.json() == {"quest_id": 2, "status": "completed", "current_stage": 2}

        with isolated_session_local() as session:
            progress = session.scalar(
                select(QuestProgress).where(
                    QuestProgress.player_id == 1,
                    QuestProgress.quest_id == 2,
                )
            )

        assert progress is not None
        assert progress.status == "completed"
        assert progress.current_stage == 2
    finally:
        isolated_engine.dispose()
        if db_path.exists():
            db_path.unlink()


def test_save_create_and_load_round_trip(monkeypatch):
    isolated_engine, isolated_session_local, db_path = _build_isolated_session()
    _patch_session_sources(monkeypatch, isolated_engine, isolated_session_local)

    try:
        with TestClient(main_module.app) as client:
            save_response = client.post(
                "/api/save/create",
                json={"player_id": 1, "scene_id": "gate", "position_x": 12, "position_y": 24},
            )
            load_response = client.get("/api/save/load", params={"player_id": 1})

        assert save_response.status_code == 200
        assert save_response.json() == {"status": "saved"}
        assert load_response.status_code == 200
        assert load_response.json() == {
            "player_id": 1,
            "scene_id": "gate",
            "position_x": 12.0,
            "position_y": 24.0,
        }

        with isolated_session_local() as session:
            player = session.scalar(select(Player).where(Player.id == 1))

        assert player is not None
        assert player.current_scene == "gate"
        assert player.position_x == 12.0
        assert player.position_y == 24.0
    finally:
        isolated_engine.dispose()
        if db_path.exists():
            db_path.unlink()
