import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import NPC, NPCMemory, Player, Quest, QuestProgress, RelationshipState
from app.seed import seed_database


def test_seed_creates_expected_core_rows(test_session):
    seed_database(test_session)

    hero = test_session.scalar(select(Player).where(Player.id == 1))
    npcs = test_session.scalars(select(NPC).order_by(NPC.id)).all()
    quests = test_session.scalars(select(Quest)).all()
    relationships = test_session.scalars(
        select(RelationshipState).where(RelationshipState.player_id == 1)
    ).all()
    progress_rows = test_session.scalars(
        select(QuestProgress).where(QuestProgress.player_id == 1)
    ).all()

    assert hero is not None
    assert hero.id == 1
    assert hero.name == "Hero"
    assert len(npcs) == 3
    assert len(quests) == 3
    assert len(relationships) == 3
    assert len(progress_rows) == 3
    assert [npc.name for npc in npcs] == [
        "Village Chief",
        "Gate Guard",
        "Merchant Lin",
    ]


def test_seed_creates_npc_memory_rows_for_decision_logic(test_session):
    seed_database(test_session)

    memories = test_session.scalars(select(NPCMemory)).all()
    assert len(memories) >= 3


def test_seed_is_idempotent_for_seeded_tables(test_session):
    seed_database(test_session)
    seed_database(test_session)

    npc_count = len(test_session.scalars(select(NPC)).all())
    quest_count = len(test_session.scalars(select(Quest)).all())
    memory_count = len(test_session.scalars(select(NPCMemory)).all())
    relationship_count = len(
        test_session.scalars(select(RelationshipState).where(RelationshipState.player_id == 1)).all()
    )
    progress_count = len(
        test_session.scalars(select(QuestProgress).where(QuestProgress.player_id == 1)).all()
    )

    assert npc_count == 3
    assert quest_count == 3
    assert memory_count == 3
    assert relationship_count == 3
    assert progress_count == 3


def test_foreign_keys_are_enforced(test_session):
    seed_database(test_session)

    test_session.add(RelationshipState(player_id=999, npc_id=1))
    with pytest.raises(IntegrityError):
        test_session.commit()
    test_session.rollback()
