import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import NPC, NPCMemory, Player, Quest, QuestProgress, RelationshipState
from app.seed import seed_database


def test_seed_creates_expected_core_rows(test_session):
    seed_database(test_session)

    hero = test_session.scalar(select(Player).where(Player.id == 1))
    npcs = test_session.scalars(select(NPC).order_by(NPC.id)).all()
    quests = test_session.scalars(select(Quest).order_by(Quest.id)).all()
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
    assert [quest.title for quest in quests] == [
        "Strange Footprints",
        "Merchant's Lost Parcel",
        "Permission to Pass",
    ]


def test_seed_creates_npc_memory_rows_for_decision_logic(test_session):
    seed_database(test_session)

    memories = test_session.scalars(select(NPCMemory).order_by(NPCMemory.npc_id)).all()
    assert len(memories) == 3
    assert [memory.content for memory in memories] == [
        "I noticed footprints near the northern gate after sunset.",
        "I do not open the gate without proof of safe passage.",
        "I lost a parcel near the gate road this morning.",
    ]


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


def test_relationship_state_unique_pair_is_enforced(test_session):
    seed_database(test_session)
    test_session.commit()

    test_session.add(RelationshipState(player_id=1, npc_id=1))
    with pytest.raises(IntegrityError):
        test_session.commit()
    test_session.rollback()


def test_quest_progress_unique_pair_is_enforced(test_session):
    seed_database(test_session)
    test_session.commit()

    test_session.add(QuestProgress(player_id=1, quest_id=1))
    with pytest.raises(IntegrityError):
        test_session.commit()
    test_session.rollback()


def test_seed_repairs_static_seed_drift(test_session):
    seed_database(test_session)
    test_session.commit()

    npc = test_session.scalar(select(NPC).where(NPC.id == 1))
    quest = test_session.scalar(select(Quest).where(Quest.id == 1))
    memory = test_session.scalar(
        select(NPCMemory).where(
            NPCMemory.npc_id == 1,
            NPCMemory.source_event == "gate_report",
        )
    )
    assert npc is not None
    assert quest is not None
    assert memory is not None

    npc.name = "Drifted Chief"
    quest.title = "Drifted Quest"
    memory.content = "Drifted memory content."
    test_session.commit()

    seed_database(test_session)
    test_session.commit()

    repaired_npc = test_session.scalar(select(NPC).where(NPC.id == 1))
    repaired_quest = test_session.scalar(select(Quest).where(Quest.id == 1))
    repaired_memory = test_session.scalar(
        select(NPCMemory).where(
            NPCMemory.npc_id == 1,
            NPCMemory.source_event == "gate_report",
        )
    )
    assert repaired_npc is not None
    assert repaired_quest is not None
    assert repaired_memory is not None
    assert repaired_npc.name == "Village Chief"
    assert repaired_quest.title == "Strange Footprints"
    assert repaired_memory.content == "I noticed footprints near the northern gate after sunset."
    assert repaired_memory.source_event == "gate_report"
    assert len(
        test_session.scalars(
            select(NPCMemory).where(NPCMemory.npc_id == 1, NPCMemory.source_event == "gate_report")
        ).all()
    ) == 1
