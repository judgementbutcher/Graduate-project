from sqlalchemy import select

from app.models import NPC, NPCMemory, Quest
from app.seed import seed_database


def test_seed_creates_expected_npcs_and_quests(test_session):
    seed_database(test_session)

    npcs = test_session.scalars(select(NPC).order_by(NPC.id)).all()
    quests = test_session.scalars(select(Quest)).all()

    assert len(npcs) == 3
    assert len(quests) == 3
    assert [npc.name for npc in npcs] == [
        "Village Chief",
        "Gate Guard",
        "Merchant Lin",
    ]


def test_seed_creates_npc_memory_rows_for_decision_logic(test_session):
    seed_database(test_session)

    memories = test_session.scalars(select(NPCMemory)).all()
    assert len(memories) >= 3
