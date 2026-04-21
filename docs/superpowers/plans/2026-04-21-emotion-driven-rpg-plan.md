# Emotion-Driven RPG Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a two-scene Godot RPG prototype backed by FastAPI and SQLite where NPC dialogue and quest updates are driven by emotion detection, memory retrieval, and task-constrained behavior selection.

**Architecture:** Keep `game/` as a Godot 4 client that only handles movement, UI, and HTTP calls. Keep `backend/` as a FastAPI service that owns persistence, NPC state, quest progression, and decision-making. Use template-driven dialogue generation so the system is stable without an external LLM.

**Tech Stack:** Godot 4.x, GDScript, Python 3.11, FastAPI, SQLAlchemy, SQLite, Pydantic, pytest, httpx

---

## File Structure

### Repository Root

- Create: `.gitignore`
- Create: `backend/`
- Create: `game/`
- Create: `docs/demo-script.md`

### Backend

- Create: `backend/requirements.txt`
- Create: `backend/app/main.py`
- Create: `backend/app/db.py`
- Create: `backend/app/models.py`
- Create: `backend/app/schemas.py`
- Create: `backend/app/seed.py`
- Create: `backend/app/data/npcs.json`
- Create: `backend/app/data/quests.json`
- Create: `backend/app/services/emotion.py`
- Create: `backend/app/services/memory.py`
- Create: `backend/app/services/decision.py`
- Create: `backend/app/services/dialogue.py`
- Create: `backend/app/services/save_service.py`
- Create: `backend/app/routes/dialogue.py`
- Create: `backend/app/routes/npc.py`
- Create: `backend/app/routes/quest.py`
- Create: `backend/app/routes/save.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`
- Create: `backend/tests/test_models.py`
- Create: `backend/tests/test_decision.py`
- Create: `backend/tests/test_dialogue_api.py`
- Create: `backend/tests/test_save_api.py`

### Godot Client

- Create: `game/project.godot`
- Create: `game/scenes/Main.tscn`
- Create: `game/scenes/WorldVillage.tscn`
- Create: `game/scenes/WorldGate.tscn`
- Create: `game/scenes/ui/DialoguePanel.tscn`
- Create: `game/scenes/ui/QuestPanel.tscn`
- Create: `game/scenes/ui/SavePanel.tscn`
- Create: `game/scripts/autoload/api_client.gd`
- Create: `game/scripts/autoload/game_state.gd`
- Create: `game/scripts/player_controller.gd`
- Create: `game/scripts/npc_interaction.gd`
- Create: `game/scripts/dialogue_manager.gd`
- Create: `game/scripts/quest_panel.gd`
- Create: `game/scripts/save_panel.gd`
- Create: `game/assets/README.md`

### Responsibility Notes

- `backend/app/models.py` holds the seven required persistence models.
- `backend/app/services/*.py` holds all algorithmic logic and keeps route handlers thin.
- `backend/app/routes/*.py` exposes the six required endpoints.
- `game/scripts/autoload/api_client.gd` is the only place that knows backend URLs.
- `game/scripts/dialogue_manager.gd` binds UI choices to backend responses.
- `game/scripts/npc_interaction.gd` owns interaction triggers, not quest logic.

### Task 1: Bootstrap Repository and Health Check

**Files:**
- Create: `.gitignore`
- Create: `backend/requirements.txt`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Write the failing health test**

```python
# backend/tests/test_health.py
from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_ok():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Create ignore rules and dependency list**

```gitignore
# .gitignore
.venv/
__pycache__/
.pytest_cache/
*.pyc
backend/app.db
game/.godot/
game/export_presets.cfg
```

```text
# backend/requirements.txt
fastapi==0.115.0
uvicorn==0.30.6
sqlalchemy==2.0.35
pydantic==2.9.2
pytest==8.3.3
httpx==0.27.2
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd backend; python -m pytest tests/test_health.py -v`  
Expected: FAIL with `ModuleNotFoundError` for `app.main`

- [ ] **Step 4: Write the minimal FastAPI app**

```python
# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(title="Emotion-Driven RPG API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd backend; python -m pytest tests/test_health.py -v`  
Expected: PASS

- [ ] **Step 6: Initialize git if absent and commit**

Run:

```bash
git init
git add .gitignore backend/requirements.txt backend/app/main.py backend/tests/test_health.py
git commit -m "chore: bootstrap backend health check"
```

Expected: repository initialized and commit created

### Task 2: Add Database Models, Session Wiring, and Seed Data

**Files:**
- Create: `backend/app/db.py`
- Create: `backend/app/models.py`
- Create: `backend/app/seed.py`
- Create: `backend/app/data/npcs.json`
- Create: `backend/app/data/quests.json`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_models.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the failing model and seed tests**

```python
# backend/tests/test_models.py
from sqlalchemy import select

from app.models import Base, NPC, NPCMemory, Quest
from app.seed import seed_database


def test_seed_creates_three_npcs_and_three_quests(test_session):
    Base.metadata.create_all(bind=test_session.bind)

    seed_database(test_session)

    npcs = test_session.scalars(select(NPC)).all()
    quests = test_session.scalars(select(Quest)).all()

    assert len(npcs) == 3
    assert len(quests) == 3


def test_npc_names_match_design_spec(test_session):
    Base.metadata.create_all(bind=test_session.bind)
    seed_database(test_session)

    names = {npc.name for npc in test_session.scalars(select(NPC)).all()}

    assert names == {"Village Chief", "Gate Guard", "Merchant Lin"}


def test_seed_creates_memories_for_decision_logic(test_session):
    Base.metadata.create_all(bind=test_session.bind)
    seed_database(test_session)

    memories = test_session.scalars(select(NPCMemory)).all()

    assert len(memories) >= 3
```

```python
# backend/tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base


@pytest.fixture
def test_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend; python -m pytest tests/test_models.py -v`  
Expected: FAIL with `ModuleNotFoundError` for `app.models` or `app.seed`

- [ ] **Step 3: Implement database wiring and models**

```python
# backend/app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
```

```python
# backend/app/models.py
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "player"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), default="Hero")
    current_scene: Mapped[str] = mapped_column(String(50), default="village")
    position_x: Mapped[float] = mapped_column(Float, default=0)
    position_y: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NPC(Base):
    __tablename__ = "npc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(50))
    personality: Mapped[str] = mapped_column(String(100))
    current_scene: Mapped[str] = mapped_column(String(50))
    emotion_state: Mapped[str] = mapped_column(String(30), default="neutral")
    description: Mapped[str] = mapped_column(Text)


class RelationshipState(Base):
    __tablename__ = "relationship_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"))
    npc_id: Mapped[int] = mapped_column(ForeignKey("npc.id"))
    favorability: Mapped[int] = mapped_column(Integer, default=0)
    trust: Mapped[int] = mapped_column(Integer, default=0)
    alertness: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NPCMemory(Base):
    __tablename__ = "npc_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    npc_id: Mapped[int] = mapped_column(ForeignKey("npc.id"))
    content: Mapped[str] = mapped_column(Text)
    keywords: Mapped[str] = mapped_column(String(200))
    importance: Mapped[int] = mapped_column(Integer, default=1)
    emotion_tag: Mapped[str] = mapped_column(String(30), default="neutral")
    source_event: Mapped[str] = mapped_column(String(100), default="seed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Quest(Base):
    __tablename__ = "quest"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text)
    quest_type: Mapped[str] = mapped_column(String(30))
    giver_npc_id: Mapped[int] = mapped_column(ForeignKey("npc.id"))
    target_scene: Mapped[str] = mapped_column(String(50))
    reward_desc: Mapped[str] = mapped_column(String(100))


class QuestProgress(Base):
    __tablename__ = "quest_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"))
    quest_id: Mapped[int] = mapped_column(ForeignKey("quest.id"))
    current_stage: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="locked")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DialogueLog(Base):
    __tablename__ = "dialogue_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"))
    npc_id: Mapped[int] = mapped_column(ForeignKey("npc.id"))
    player_input: Mapped[str] = mapped_column(Text)
    emotion_result: Mapped[str] = mapped_column(String(30))
    chosen_action: Mapped[str] = mapped_column(String(30))
    npc_reply: Mapped[str] = mapped_column(Text)
    quest_update: Mapped[str] = mapped_column(String(100), default="none")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 4: Add deterministic seed content**

```json
// backend/app/data/npcs.json
[
  {
    "id": 1,
    "name": "Village Chief",
    "role": "chief",
    "personality": "careful but kind",
    "current_scene": "village",
    "emotion_state": "neutral",
    "description": "Knows the village history and controls the main quest."
  },
  {
    "id": 2,
    "name": "Gate Guard",
    "role": "guard",
    "personality": "strict and suspicious",
    "current_scene": "village",
    "emotion_state": "alert",
    "description": "Blocks access to the gate until trust is earned."
  },
  {
    "id": 3,
    "name": "Merchant Lin",
    "role": "merchant",
    "personality": "talkative and practical",
    "current_scene": "village",
    "emotion_state": "neutral",
    "description": "Offers a side quest and extra clues after help is given."
  }
]
```

```json
// backend/app/data/quests.json
[
  {
    "id": 1,
    "title": "Strange Footprints",
    "description": "Ask around the village and inspect the northern gate.",
    "quest_type": "main",
    "giver_npc_id": 1,
    "target_scene": "gate",
    "reward_desc": "Progress main story"
  },
  {
    "id": 2,
    "title": "Merchant's Lost Parcel",
    "description": "Recover the merchant parcel near the gate.",
    "quest_type": "side",
    "giver_npc_id": 3,
    "target_scene": "gate",
    "reward_desc": "Gain trust and clue"
  },
  {
    "id": 3,
    "title": "Permission to Pass",
    "description": "Convince the guard to open the gate.",
    "quest_type": "side",
    "giver_npc_id": 2,
    "target_scene": "village",
    "reward_desc": "Unlock access"
  }
]
```

```python
# backend/app/seed.py
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NPC, NPCMemory, Player, Quest, QuestProgress, RelationshipState

DATA_DIR = Path(__file__).parent / "data"


def seed_database(session: Session) -> None:
    if session.scalars(select(Player)).first() is None:
        session.add(Player(id=1, name="Hero"))

    if session.scalars(select(NPC)).first() is None:
        npcs = json.loads((DATA_DIR / "npcs.json").read_text(encoding="utf-8"))
        for npc in npcs:
            session.add(NPC(**npc))

    if session.scalars(select(Quest)).first() is None:
        quests = json.loads((DATA_DIR / "quests.json").read_text(encoding="utf-8"))
        for quest in quests:
            session.add(Quest(**quest))

    if session.scalars(select(NPCMemory)).first() is None:
        session.add_all(
            [
                NPCMemory(
                    npc_id=1,
                    content="The chief heard reports of footprints near the northern gate.",
                    keywords="footprints,gate,north",
                    importance=3,
                    emotion_tag="neutral",
                ),
                NPCMemory(
                    npc_id=2,
                    content="The guard was ordered not to open the gate without proof.",
                    keywords="gate,proof,passage",
                    importance=3,
                    emotion_tag="alert",
                ),
                NPCMemory(
                    npc_id=3,
                    content="Merchant Lin lost a parcel near the gate road this morning.",
                    keywords="parcel,merchant,gate",
                    importance=2,
                    emotion_tag="neutral",
                ),
            ]
        )

    session.flush()

    for npc_id in (1, 2, 3):
        exists = session.scalars(
            select(RelationshipState).where(
                RelationshipState.player_id == 1,
                RelationshipState.npc_id == npc_id,
            )
        ).first()
        if exists is None:
            session.add(RelationshipState(player_id=1, npc_id=npc_id))

    for quest_id in (1, 2, 3):
        exists = session.scalars(
            select(QuestProgress).where(
                QuestProgress.player_id == 1,
                QuestProgress.quest_id == quest_id,
            )
        ).first()
        if exists is None:
            session.add(QuestProgress(player_id=1, quest_id=quest_id))

    session.commit()
```

- [ ] **Step 5: Initialize schema on startup**

```python
# backend/app/main.py
from fastapi import FastAPI

from app.db import SessionLocal, engine
from app.models import Base
from app.seed import seed_database

app = FastAPI(title="Emotion-Driven RPG API")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `cd backend; python -m pytest tests/test_models.py -v`  
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app backend/tests
git commit -m "feat: add database models and seed data"
```

### Task 3: Implement Emotion, Memory, and Decision Services

**Files:**
- Create: `backend/app/services/emotion.py`
- Create: `backend/app/services/memory.py`
- Create: `backend/app/services/decision.py`
- Create: `backend/tests/test_decision.py`

- [ ] **Step 1: Write the failing service tests**

```python
# backend/tests/test_decision.py
from app.services.decision import choose_action
from app.services.emotion import detect_emotion
from app.services.memory import score_memory


def test_detect_emotion_marks_hostile_input():
    result = detect_emotion("Get out of my way, you liar")
    assert result["label"] == "hostile"


def test_memory_score_prefers_keyword_match():
    memory = {
        "content": "The gate was closed after strange footprints appeared.",
        "keywords": "gate,footprints",
        "importance": 2,
        "emotion_tag": "alert",
    }

    score = score_memory("Tell me about the gate", "neutral", memory)

    assert score > 2


def test_guard_refuses_when_trust_is_too_low():
    action = choose_action(
        npc_role="guard",
        emotion_label="neutral",
        relation={"trust": 0, "favorability": 0, "alertness": 2},
        top_memories=[{"content": "No one passes without proof.", "importance": 3}],
        quest_state={"main_stage": 0, "parcel_done": False},
    )

    assert action == "refuse"


def test_merchant_gives_clue_after_parcel_quest():
    action = choose_action(
        npc_role="merchant",
        emotion_label="friendly",
        relation={"trust": 2, "favorability": 3, "alertness": 0},
        top_memories=[{"content": "The parcel went missing near the gate.", "importance": 2}],
        quest_state={"main_stage": 1, "parcel_done": True},
    )

    assert action == "give_clue"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend; python -m pytest tests/test_decision.py -v`  
Expected: FAIL with `ModuleNotFoundError` for the service modules

- [ ] **Step 3: Implement the minimal emotion detector**

```python
# backend/app/services/emotion.py
FRIENDLY_WORDS = {"thanks", "please", "help", "sorry", "friend"}
HOSTILE_WORDS = {"liar", "stupid", "move", "hate", "idiot"}


def detect_emotion(text: str) -> dict[str, float | str]:
    lower_text = text.lower()
    friendly_hits = sum(word in lower_text for word in FRIENDLY_WORDS)
    hostile_hits = sum(word in lower_text for word in HOSTILE_WORDS)

    if hostile_hits > friendly_hits:
        return {"label": "hostile", "friendly": 0.1, "neutral": 0.2, "hostile": 0.7}
    if friendly_hits > hostile_hits:
        return {"label": "friendly", "friendly": 0.7, "neutral": 0.2, "hostile": 0.1}
    return {"label": "neutral", "friendly": 0.2, "neutral": 0.6, "hostile": 0.2}
```

- [ ] **Step 4: Implement memory scoring and retrieval helpers**

```python
# backend/app/services/memory.py
def score_memory(query: str, emotion_label: str, memory: dict) -> float:
    keywords = [item.strip() for item in memory.get("keywords", "").split(",") if item.strip()]
    keyword_hits = sum(keyword.lower() in query.lower() for keyword in keywords)
    importance = float(memory.get("importance", 1))
    emotion_bonus = 1.0 if memory.get("emotion_tag") == emotion_label else 0.0
    return keyword_hits + importance + emotion_bonus


def top_memories(query: str, emotion_label: str, memories: list[dict], limit: int = 2) -> list[dict]:
    ranked = sorted(memories, key=lambda item: score_memory(query, emotion_label, item), reverse=True)
    return ranked[:limit]
```

- [ ] **Step 5: Implement constrained behavior selection**

```python
# backend/app/services/decision.py
def choose_action(
    npc_role: str,
    emotion_label: str,
    relation: dict,
    top_memories: list[dict],
    quest_state: dict,
) -> str:
    if npc_role == "guard" and relation["trust"] < 1 and not quest_state.get("parcel_done", False):
        return "refuse"

    if npc_role == "merchant" and quest_state.get("parcel_done", False):
        return "give_clue"

    if npc_role == "chief" and emotion_label == "friendly":
        return "give_hint"

    if emotion_label == "hostile":
        return "warn"

    if top_memories:
        return "probe"

    return "neutral_reply"
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `cd backend; python -m pytest tests/test_decision.py -v`  
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/services backend/tests/test_decision.py
git commit -m "feat: add emotion memory and decision services"
```

### Task 4: Build Dialogue Endpoint and Logging

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/services/dialogue.py`
- Create: `backend/app/routes/dialogue.py`
- Create: `backend/tests/test_dialogue_api.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the failing dialogue API tests**

```python
# backend/tests/test_dialogue_api.py
from fastapi.testclient import TestClient

from app.main import app


def test_dialogue_interact_returns_reply_and_action():
    client = TestClient(app)

    response = client.post(
        "/api/dialogue/interact",
        json={
            "player_id": 1,
            "npc_id": 1,
            "scene_id": "village",
            "input_text": "Please help me understand the footprints.",
            "selected_option": "ask_for_help",
        },
    )

    payload = response.json()

    assert response.status_code == 200
    assert payload["chosen_action"] in {"give_hint", "probe", "neutral_reply"}
    assert payload["npc_reply"]
    assert "quest_update" in payload


def test_dialogue_with_guard_blocks_when_untrusted():
    client = TestClient(app)

    response = client.post(
        "/api/dialogue/interact",
        json={
            "player_id": 1,
            "npc_id": 2,
            "scene_id": "village",
            "input_text": "Open the gate now.",
            "selected_option": "demand_entry",
        },
    )

    assert response.status_code == 200
    assert response.json()["chosen_action"] == "refuse"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend; python -m pytest tests/test_dialogue_api.py -v`  
Expected: FAIL with `404 Not Found` for `/api/dialogue/interact`

- [ ] **Step 3: Define request and response schemas**

```python
# backend/app/schemas.py
from pydantic import BaseModel


class DialogueRequest(BaseModel):
    player_id: int
    npc_id: int
    scene_id: str
    input_text: str
    selected_option: str


class DialogueResponse(BaseModel):
    npc_reply: str
    emotion_result: str
    chosen_action: str
    relationship_change: dict[str, int]
    quest_update: str
```

- [ ] **Step 4: Implement the dialogue orchestration service**

```python
# backend/app/services/dialogue.py
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DialogueLog, NPC, NPCMemory, QuestProgress, RelationshipState
from app.services.decision import choose_action
from app.services.emotion import detect_emotion
from app.services.memory import top_memories


TEMPLATES = {
    "give_hint": "The chief lowers his voice. 'Check the northern gate. Something changed there last night.'",
    "probe": "The NPC studies you carefully before answering with another question.",
    "refuse": "The guard folds his arms. 'No proof, no passage.'",
    "warn": "The NPC stiffens. 'Watch your tone if you want help.'",
    "give_clue": "Merchant Lin nods. 'You earned this clue. I saw tracks near the old gate.'",
    "neutral_reply": "The NPC offers a short, cautious reply.",
}


def run_dialogue(session: Session, payload) -> dict:
    npc = session.get(NPC, payload.npc_id)
    relation = session.scalars(
        select(RelationshipState).where(
            RelationshipState.player_id == payload.player_id,
            RelationshipState.npc_id == payload.npc_id,
        )
    ).one()
    memories = [
        {
            "content": row.content,
            "keywords": row.keywords,
            "importance": row.importance,
            "emotion_tag": row.emotion_tag,
        }
        for row in session.scalars(select(NPCMemory).where(NPCMemory.npc_id == payload.npc_id)).all()
    ]
    quest_rows = session.scalars(select(QuestProgress).where(QuestProgress.player_id == payload.player_id)).all()
    quest_state = {
        "main_stage": next((row.current_stage for row in quest_rows if row.quest_id == 1), 0),
        "parcel_done": any(row.quest_id == 2 and row.status == "completed" for row in quest_rows),
    }
    emotion = detect_emotion(payload.input_text)
    relevant = top_memories(payload.input_text, emotion["label"], memories)
    action = choose_action(
        npc_role=npc.role,
        emotion_label=emotion["label"],
        relation={"trust": relation.trust, "favorability": relation.favorability, "alertness": relation.alertness},
        top_memories=relevant,
        quest_state=quest_state,
    )

    delta = {"favorability": 0, "trust": 0, "alertness": 0}
    if emotion["label"] == "friendly":
        delta["favorability"] += 1
        delta["trust"] += 1
    elif emotion["label"] == "hostile":
        delta["alertness"] += 1

    relation.favorability += delta["favorability"]
    relation.trust += delta["trust"]
    relation.alertness += delta["alertness"]

    quest_update = "none"
    if npc.id == 1 and action == "give_hint":
        main_row = next(row for row in quest_rows if row.quest_id == 1)
        main_row.status = "active"
        main_row.current_stage = 1
        quest_update = "main_started"

    reply = TEMPLATES[action]
    session.add(
        DialogueLog(
            player_id=payload.player_id,
            npc_id=payload.npc_id,
            player_input=payload.input_text,
            emotion_result=emotion["label"],
            chosen_action=action,
            npc_reply=reply,
            quest_update=quest_update,
        )
    )
    session.commit()

    return {
        "npc_reply": reply,
        "emotion_result": emotion["label"],
        "chosen_action": action,
        "relationship_change": delta,
        "quest_update": quest_update,
    }
```

- [ ] **Step 5: Expose the route and mount it**

```python
# backend/app/routes/dialogue.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.schemas import DialogueRequest, DialogueResponse
from app.services.dialogue import run_dialogue

router = APIRouter(prefix="/api/dialogue", tags=["dialogue"])


def get_session():
    with SessionLocal() as session:
        yield session


@router.post("/interact", response_model=DialogueResponse)
def interact(payload: DialogueRequest, session: Session = Depends(get_session)):
    return run_dialogue(session, payload)
```

```python
# backend/app/main.py
from fastapi import FastAPI

from app.db import SessionLocal, engine
from app.models import Base
from app.routes.dialogue import router as dialogue_router
from app.seed import seed_database

app = FastAPI(title="Emotion-Driven RPG API")
app.include_router(dialogue_router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `cd backend; python -m pytest tests/test_dialogue_api.py -v`  
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app backend/tests/test_dialogue_api.py
git commit -m "feat: add dialogue interaction endpoint"
```

### Task 5: Add NPC State, Quest List, and Save/Load Endpoints

**Files:**
- Create: `backend/app/routes/npc.py`
- Create: `backend/app/routes/quest.py`
- Create: `backend/app/routes/save.py`
- Create: `backend/app/services/save_service.py`
- Create: `backend/tests/test_save_api.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the failing API tests**

```python
# backend/tests/test_save_api.py
from fastapi.testclient import TestClient

from app.main import app


def test_quest_list_endpoint_returns_three_quests():
    client = TestClient(app)

    response = client.get("/api/quest/list", params={"player_id": 1})

    assert response.status_code == 200
    assert len(response.json()["quests"]) == 3


def test_quest_update_endpoint_advances_status():
    client = TestClient(app)

    response = client.post(
        "/api/quest/update",
        json={"player_id": 1, "quest_id": 2, "status": "completed", "current_stage": 2},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_save_create_and_load_round_trip():
    client = TestClient(app)

    save_response = client.post(
        "/api/save/create",
        json={"player_id": 1, "scene_id": "gate", "position_x": 12, "position_y": 24},
    )
    load_response = client.get("/api/save/load", params={"player_id": 1})

    assert save_response.status_code == 200
    assert load_response.status_code == 200
    assert load_response.json()["scene_id"] == "gate"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend; python -m pytest tests/test_save_api.py -v`  
Expected: FAIL with `404 Not Found` for the missing routes

- [ ] **Step 3: Implement save persistence as a small JSON snapshot**

```python
# backend/app/services/save_service.py
import json
from pathlib import Path

SAVE_FILE = Path(__file__).resolve().parent.parent / "save_slot.json"


def write_save(payload: dict) -> dict:
    SAVE_FILE.write_text(json.dumps(payload), encoding="utf-8")
    return {"status": "saved"}


def read_save(player_id: int) -> dict:
    if not SAVE_FILE.exists():
        return {"player_id": player_id, "scene_id": "village", "position_x": 0, "position_y": 0}
    return json.loads(SAVE_FILE.read_text(encoding="utf-8"))
```

- [ ] **Step 4: Expose the remaining routes**

```python
# backend/app/routes/npc.py
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import NPC, NPCMemory, RelationshipState

router = APIRouter(prefix="/api/npc", tags=["npc"])


def get_session():
    with SessionLocal() as session:
        yield session


@router.get("/{npc_id}/state")
def npc_state(npc_id: int, player_id: int = 1, session: Session = Depends(get_session)):
    npc = session.get(NPC, npc_id)
    relation = session.scalars(
        select(RelationshipState).where(
            RelationshipState.player_id == player_id,
            RelationshipState.npc_id == npc_id,
        )
    ).one()
    memories = session.scalars(select(NPCMemory).where(NPCMemory.npc_id == npc_id)).all()
    return {
        "npc_id": npc.id,
        "name": npc.name,
        "emotion_state": npc.emotion_state,
        "relationship": {
            "favorability": relation.favorability,
            "trust": relation.trust,
            "alertness": relation.alertness,
        },
        "recent_memories": [item.content for item in memories[:2]],
    }
```

```python
# backend/app/routes/quest.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Quest, QuestProgress

router = APIRouter(prefix="/api/quest", tags=["quest"])


def get_session():
    with SessionLocal() as session:
        yield session


class QuestUpdateRequest(BaseModel):
    player_id: int
    quest_id: int
    status: str
    current_stage: int


@router.get("/list")
def quest_list(player_id: int, session: Session = Depends(get_session)):
    progress_rows = session.scalars(select(QuestProgress).where(QuestProgress.player_id == player_id)).all()
    quest_map = {quest.id: quest for quest in session.scalars(select(Quest)).all()}
    return {
        "quests": [
            {
                "quest_id": row.quest_id,
                "title": quest_map[row.quest_id].title,
                "status": row.status,
                "current_stage": row.current_stage,
            }
            for row in progress_rows
        ]
    }


@router.post("/update")
def update_quest(payload: QuestUpdateRequest, session: Session = Depends(get_session)):
    row = session.scalars(
        select(QuestProgress).where(
            QuestProgress.player_id == payload.player_id,
            QuestProgress.quest_id == payload.quest_id,
        )
    ).one()
    row.status = payload.status
    row.current_stage = payload.current_stage
    session.commit()
    return {"quest_id": payload.quest_id, "status": row.status, "current_stage": row.current_stage}
```

```python
# backend/app/routes/save.py
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.save_service import read_save, write_save

router = APIRouter(prefix="/api/save", tags=["save"])


class SaveRequest(BaseModel):
    player_id: int
    scene_id: str
    position_x: float
    position_y: float


@router.post("/create")
def create_save(payload: SaveRequest):
    write_save(payload.model_dump())
    return {"status": "saved"}


@router.get("/load")
def load_save(player_id: int):
    return read_save(player_id)
```

```python
# backend/app/main.py
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
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd backend; python -m pytest tests/test_save_api.py -v`  
Expected: PASS

- [ ] **Step 6: Run the full backend suite**

Run: `cd backend; python -m pytest tests -v`  
Expected: all backend tests PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app backend/tests/test_save_api.py
git commit -m "feat: add quest npc and save endpoints"
```

### Task 6: Create the Godot Project Shell and HTTP Client

**Files:**
- Create: `game/project.godot`
- Create: `game/scenes/Main.tscn`
- Create: `game/scenes/WorldVillage.tscn`
- Create: `game/scenes/WorldGate.tscn`
- Create: `game/scripts/autoload/api_client.gd`
- Create: `game/scripts/autoload/game_state.gd`
- Create: `game/scripts/player_controller.gd`

- [ ] **Step 1: Write a headless smoke target**

```text
# Expected scene tree for game/scenes/Main.tscn
Main (Node)
├── WorldRoot (Node)
├── CanvasLayer
├── HTTPRequest
```

- [ ] **Step 2: Run Godot headless to confirm the project does not exist yet**

Run: `godot4 --path game --headless --quit`  
Expected: FAIL with project file not found

- [ ] **Step 3: Create the project shell, autoloads, and player movement**

```ini
; game/project.godot
config_version=5

[application]
config/name="EmotionDrivenRPG"
run/main_scene="res://scenes/Main.tscn"

[autoload]
ApiClient="*res://scripts/autoload/api_client.gd"
GameState="*res://scripts/autoload/game_state.gd"
```

```gdscript
# game/scripts/autoload/api_client.gd
extends Node

const BASE_URL := "http://127.0.0.1:8000"

func post_json(path: String, body: Dictionary) -> Dictionary:
	var http := HTTPRequest.new()
	add_child(http)
	var headers := PackedStringArray(["Content-Type: application/json"])
	var error := http.request(
		BASE_URL + path,
		headers,
		HTTPClient.METHOD_POST,
		JSON.stringify(body)
	)
	if error != OK:
		return {"error": "request_failed"}
	var result := await http.request_completed
	http.queue_free()
	var parsed := JSON.parse_string(result[3].get_string_from_utf8())
	return parsed if parsed != null else {"error": "bad_response"}


func get_json(path: String) -> Dictionary:
	var http := HTTPRequest.new()
	add_child(http)
	var error := http.request(BASE_URL + path)
	if error != OK:
		return {"error": "request_failed"}
	var result := await http.request_completed
	http.queue_free()
	var parsed := JSON.parse_string(result[3].get_string_from_utf8())
	return parsed if parsed != null else {"error": "bad_response"}
```

```gdscript
# game/scripts/autoload/game_state.gd
extends Node

var player_id := 1
var current_scene := "village"
var quests: Array = []
var last_dialogue: Dictionary = {}
```

```gdscript
# game/scripts/player_controller.gd
extends CharacterBody2D

@export var speed := 140.0

func _physics_process(_delta: float) -> void:
	var direction := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	velocity = direction * speed
	move_and_slide()
```

- [ ] **Step 4: Create the three base scenes in the editor**

```text
WorldVillage.tscn
- Node2D
  - TileMapLayer
  - Player (CharacterBody2D, script = player_controller.gd)
  - NPCChief (Area2D)
  - NPCGuard (Area2D)
  - NPCMerchant (Area2D)

WorldGate.tscn
- Node2D
  - TileMapLayer
  - PlayerSpawn (Marker2D)
  - ReturnZone (Area2D)

Main.tscn
- Node
  - WorldRoot (Node)
  - CanvasLayer
```

- [ ] **Step 5: Run headless smoke again**

Run: `godot4 --path game --headless --quit`  
Expected: exit code 0 and no script parse errors

- [ ] **Step 6: Commit**

```bash
git add game/project.godot game/scenes game/scripts
git commit -m "feat: bootstrap godot project shell"
```

### Task 7: Implement NPC Interaction and Dialogue UI

**Files:**
- Create: `game/scenes/ui/DialoguePanel.tscn`
- Create: `game/scripts/npc_interaction.gd`
- Create: `game/scripts/dialogue_manager.gd`
- Modify: `game/scenes/Main.tscn`
- Modify: `game/scenes/WorldVillage.tscn`

- [ ] **Step 1: Add a smoke target for the dialogue flow**

```text
DialoguePanel.tscn
- Control
  - PanelContainer
    - VBoxContainer
      - RichTextLabel (name = ReplyLabel)
      - Button (name = OptionHelp)
      - Button (name = OptionPolite)
      - Button (name = OptionDemand)
```

- [ ] **Step 2: Run the game and confirm dialogue UI is not wired yet**

Run: `godot4 --path game`  
Expected: the village scene opens, but talking to NPCs does nothing yet

- [ ] **Step 3: Implement interaction trigger and dialogue manager**

```gdscript
# game/scripts/npc_interaction.gd
extends Area2D

@export var npc_id := 1
@export var npc_name := "Village Chief"
@export var selected_option := "ask_for_help"

var player_in_range := false


func _ready() -> void:
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)


func _process(_delta: float) -> void:
	if player_in_range and Input.is_action_just_pressed("ui_accept"):
		get_tree().call_group("dialogue_manager", "open_dialogue", npc_id, npc_name, selected_option)


func _on_body_entered(_body: Node) -> void:
	player_in_range = true


func _on_body_exited(_body: Node) -> void:
	player_in_range = false
```

```gdscript
# game/scripts/dialogue_manager.gd
extends Control

@onready var reply_label: RichTextLabel = %ReplyLabel
@onready var option_help: Button = %OptionHelp
@onready var option_polite: Button = %OptionPolite
@onready var option_demand: Button = %OptionDemand

var current_npc_id := 1
var current_npc_name := ""


func _ready() -> void:
	add_to_group("dialogue_manager")
	visible = false
	option_help.pressed.connect(_submit.bind("Please help me understand what happened.", "ask_for_help"))
	option_polite.pressed.connect(_submit.bind("Thanks for speaking with me.", "be_polite"))
	option_demand.pressed.connect(_submit.bind("Tell me everything right now.", "demand_entry"))


func open_dialogue(npc_id: int, npc_name: String, _default_option: String) -> void:
	current_npc_id = npc_id
	current_npc_name = npc_name
	reply_label.text = "Talking to %s" % npc_name
	visible = true


func _submit(text: String, selected_option: String) -> void:
	var payload := {
		"player_id": GameState.player_id,
		"npc_id": current_npc_id,
		"scene_id": GameState.current_scene,
		"input_text": text,
		"selected_option": selected_option
	}
	var result := await ApiClient.post_json("/api/dialogue/interact", payload)
	GameState.last_dialogue = result
	reply_label.text = result.get("npc_reply", "The NPC stays silent.")
```

- [ ] **Step 4: Wire the scene tree**

```text
Main.tscn additions
- CanvasLayer
  - DialoguePanel (instance of scenes/ui/DialoguePanel.tscn, script = dialogue_manager.gd)

WorldVillage.tscn additions
- NPCChief (script = npc_interaction.gd, npc_id = 1)
- NPCGuard (script = npc_interaction.gd, npc_id = 2)
- NPCMerchant (script = npc_interaction.gd, npc_id = 3)
```

- [ ] **Step 5: Manual verification**

Run:

```bash
cd backend
uvicorn app.main:app --reload
```

In another terminal:

```bash
godot4 --path game
```

Expected: pressing interact near each NPC opens the dialogue panel and shows a reply returned from the backend

- [ ] **Step 6: Commit**

```bash
git add game/scenes game/scripts
git commit -m "feat: add godot dialogue interaction flow"
```

### Task 8: Add Quest Panel, Save Panel, and Scene Transition Flow

**Files:**
- Create: `game/scenes/ui/QuestPanel.tscn`
- Create: `game/scenes/ui/SavePanel.tscn`
- Create: `game/scripts/quest_panel.gd`
- Create: `game/scripts/save_panel.gd`
- Modify: `game/scenes/Main.tscn`
- Modify: `game/scripts/dialogue_manager.gd`

- [ ] **Step 1: Define the UI targets**

```text
QuestPanel.tscn
- Control
  - PanelContainer
    - VBoxContainer
      - Label (name = QuestTitle)
      - ItemList (name = QuestList)
      - Button (name = TravelGateButton)

SavePanel.tscn
- Control
  - PanelContainer
    - VBoxContainer
      - Button (name = SaveButton)
      - Button (name = LoadButton)
      - Label (name = StatusLabel)
```

- [ ] **Step 2: Verify the current build lacks quest and save UI**

Run: `godot4 --path game`  
Expected: dialogue works, but there is no quest panel and no save/load control

- [ ] **Step 3: Implement quest refresh and save/load scripts**

```gdscript
# game/scripts/quest_panel.gd
extends Control

@onready var quest_list: ItemList = %QuestList
@onready var travel_gate_button: Button = %TravelGateButton


func _ready() -> void:
	add_to_group("quest_panel")
	travel_gate_button.pressed.connect(_travel_to_gate)
	refresh()


func refresh() -> void:
	var result := await ApiClient.get_json("/api/quest/list?player_id=%d" % GameState.player_id)
	quest_list.clear()
	for quest in result.get("quests", []):
		quest_list.add_item("%s [%s]" % [quest["title"], quest["status"]])
	GameState.quests = result.get("quests", [])
	travel_gate_button.disabled = true
	for quest in GameState.quests:
		if quest["quest_id"] == 1 and quest["status"] == "active":
			travel_gate_button.disabled = false


func _travel_to_gate() -> void:
	GameState.current_scene = "gate"
	get_tree().change_scene_to_file("res://scenes/WorldGate.tscn")
```

```gdscript
# game/scripts/save_panel.gd
extends Control

@onready var save_button: Button = %SaveButton
@onready var load_button: Button = %LoadButton
@onready var status_label: Label = %StatusLabel


func _ready() -> void:
	save_button.pressed.connect(_save_game)
	load_button.pressed.connect(_load_game)


func _save_game() -> void:
	var payload := {
		"player_id": GameState.player_id,
		"scene_id": GameState.current_scene,
		"position_x": 0,
		"position_y": 0
	}
	var result := await ApiClient.post_json("/api/save/create", payload)
	status_label.text = result.get("status", "save_failed")


func _load_game() -> void:
	var result := await ApiClient.get_json("/api/save/load?player_id=%d" % GameState.player_id)
	GameState.current_scene = result.get("scene_id", "village")
	status_label.text = "loaded %s" % GameState.current_scene
	if GameState.current_scene == "gate":
		get_tree().change_scene_to_file("res://scenes/WorldGate.tscn")
	else:
		get_tree().change_scene_to_file("res://scenes/WorldVillage.tscn")
```

- [ ] **Step 4: Refresh quests after dialogue and add the panels**

```gdscript
# game/scripts/dialogue_manager.gd
extends Control

@onready var reply_label: RichTextLabel = %ReplyLabel
@onready var option_help: Button = %OptionHelp
@onready var option_polite: Button = %OptionPolite
@onready var option_demand: Button = %OptionDemand

var current_npc_id := 1
var current_npc_name := ""


func _ready() -> void:
	add_to_group("dialogue_manager")
	visible = false
	option_help.pressed.connect(_submit.bind("Please help me understand what happened.", "ask_for_help"))
	option_polite.pressed.connect(_submit.bind("Thanks for speaking with me.", "be_polite"))
	option_demand.pressed.connect(_submit.bind("Tell me everything right now.", "demand_entry"))


func open_dialogue(npc_id: int, npc_name: String, _default_option: String) -> void:
	current_npc_id = npc_id
	current_npc_name = npc_name
	reply_label.text = "Talking to %s" % npc_name
	visible = true


func _submit(text: String, selected_option: String) -> void:
	var payload := {
		"player_id": GameState.player_id,
		"npc_id": current_npc_id,
		"scene_id": GameState.current_scene,
		"input_text": text,
		"selected_option": selected_option
	}
	var result := await ApiClient.post_json("/api/dialogue/interact", payload)
	GameState.last_dialogue = result
	reply_label.text = result.get("npc_reply", "The NPC stays silent.")
	get_tree().call_group("quest_panel", "refresh")
```

```text
Main.tscn additions
- CanvasLayer
  - QuestPanel (instance of scenes/ui/QuestPanel.tscn, script = quest_panel.gd, group = quest_panel)
  - SavePanel (instance of scenes/ui/SavePanel.tscn, script = save_panel.gd)
```

- [ ] **Step 5: Manual verification**

Run backend and client again.  
Expected:
- Quest list shows three quests
- Talking to the chief changes the main quest to active
- `TravelGateButton` becomes enabled after the main quest starts
- Pressing the button changes the scene to `WorldGate.tscn`
- Save button writes state
- Load button restores the stored scene and actually loads the matching map

- [ ] **Step 6: Commit**

```bash
git add game/scenes game/scripts
git commit -m "feat: add quest and save ui panels"
```

### Task 9: Add Content Completion, Failure Handling, and Demo Checklist

**Files:**
- Create: `game/assets/README.md`
- Create: `docs/demo-script.md`
- Modify: `backend/app/services/dialogue.py`
- Modify: `game/scripts/dialogue_manager.gd`

- [ ] **Step 1: Write down the failure cases to verify**

```text
Manual cases:
1. Stop the backend and confirm the client shows a fallback message.
2. Use a hostile option with the guard and confirm the action is refuse or warn.
3. Finish the merchant parcel quest path and confirm the merchant gives a clue.
4. Save in the gate scene and load the save.
```

- [ ] **Step 2: Add backend-safe fallback responses**

```python
# backend/app/services/dialogue.py
TEMPLATES = {
    "give_hint": "The chief lowers his voice. 'Check the northern gate. Something changed there last night.'",
    "probe": "The NPC studies you carefully before answering with another question.",
    "refuse": "The guard folds his arms. 'No proof, no passage.'",
    "warn": "The NPC stiffens. 'Watch your tone if you want help.'",
    "give_clue": "Merchant Lin nods. 'You earned this clue. I saw tracks near the old gate.'",
    "neutral_reply": "The NPC offers a short, cautious reply.",
    "fallback": "The NPC hesitates, saying nothing useful for the moment.",
}

# Inside run_dialogue(...)
reply = TEMPLATES.get(action, TEMPLATES["fallback"])
```

- [ ] **Step 3: Add client-side network fallback**

```gdscript
# game/scripts/dialogue_manager.gd
func _submit(text: String, selected_option: String) -> void:
	var payload := {
		"player_id": GameState.player_id,
		"npc_id": current_npc_id,
		"scene_id": GameState.current_scene,
		"input_text": text,
		"selected_option": selected_option
	}
	var result := await ApiClient.post_json("/api/dialogue/interact", payload)
	if result.has("error"):
		reply_label.text = "The system is busy. Please try again."
		return
	GameState.last_dialogue = result
	reply_label.text = result.get("npc_reply", "The NPC stays silent.")
	get_tree().call_group("quest_panel", "refresh")
```

- [ ] **Step 4: Document asset sourcing and the demo path**

```markdown
# game/assets/README.md

- Use one public-domain or CC0 top-down village tileset.
- Use one simple character sprite sheet for the player.
- Recolor three NPC sprites instead of drawing unique art.
- Keep UI art limited to flat panels and bitmap fonts.
```

```markdown
# docs/demo-script.md

1. Start backend with `cd backend && uvicorn app.main:app --reload`
2. Start client with `godot4 --path game`
3. Speak to the chief politely to start the main quest.
4. Speak to the guard rudely and show that passage is denied.
5. Speak to Merchant Lin and complete the parcel clue path.
6. Save the game, reload it, and show the saved scene status.
```

- [ ] **Step 5: Run final verification**

Run:

```bash
cd backend
python -m pytest tests -v
```

Expected: all backend tests PASS

Then run:

```bash
uvicorn app.main:app --reload
godot4 --path game
```

Expected: the demo script can be completed end-to-end without a crash

- [ ] **Step 6: Commit**

```bash
git add backend/app game/assets docs/demo-script.md
git commit -m "chore: harden prototype for demo"
```
