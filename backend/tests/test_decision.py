from app.services.decision import choose_action
from app.services.emotion import detect_emotion
from app.services.memory import score_memory, top_memories


def test_detect_emotion_flags_hostile_text():
    result = detect_emotion("Get out of my way, you liar")
    assert result["label"] == "hostile"


def test_detect_emotion_flags_friendly_text():
    result = detect_emotion("Please help me, friend.")
    assert result["label"] == "friendly"


def test_score_memory_gate_match_scores_above_two():
    memory = {
        "keywords": "gate,parcel,road",
        "importance": 1.5,
        "emotion_tag": "hostile",
    }
    score = score_memory("Gate! parcel?", "hostile", memory)
    assert score == 4.5


def test_choose_action_guard_refuses_on_low_trust_without_parcel_done():
    action = choose_action(
        npc_role="guard",
        emotion_label="neutral",
        relation={"trust": 0},
        top_memories=[],
        quest_state={"parcel_done": False},
    )
    assert action == "refuse"


def test_choose_action_merchant_gives_clue_when_parcel_done():
    action = choose_action(
        npc_role="merchant",
        emotion_label="neutral",
        relation={"trust": 0},
        top_memories=[],
        quest_state={"parcel_done": True},
    )
    assert action == "give_clue"


def test_top_memories_orders_descending_and_respects_limit():
    memories = [
        {"id": "m1", "keywords": "gate", "importance": 0.1, "emotion_tag": "neutral"},
        {"id": "m2", "keywords": "parcel,gate", "importance": 1.0, "emotion_tag": "neutral"},
        {"id": "m3", "keywords": "road", "importance": 0.0, "emotion_tag": "hostile"},
    ]

    result = top_memories("Gate, parcel.", "neutral", memories, limit=2)
    assert [memory["id"] for memory in result] == ["m2", "m1"]


def test_choose_action_precedence_merchant_clue_over_hostile_and_probe():
    action = choose_action(
        npc_role="merchant",
        emotion_label="hostile",
        relation={"trust": 0},
        top_memories=[{"id": "m1"}],
        quest_state={"parcel_done": True},
    )
    assert action == "give_clue"


def test_choose_action_chief_friendly_gives_hint():
    action = choose_action(
        npc_role="chief",
        emotion_label="friendly",
        relation={},
        top_memories=[],
        quest_state={"parcel_done": False},
    )
    assert action == "give_hint"


def test_choose_action_hostile_warns_without_earlier_matches():
    action = choose_action(
        npc_role="villager",
        emotion_label="hostile",
        relation={},
        top_memories=[],
        quest_state={"parcel_done": False},
    )
    assert action == "warn"


def test_choose_action_memories_probe_without_earlier_matches():
    action = choose_action(
        npc_role="villager",
        emotion_label="neutral",
        relation={},
        top_memories=[{"id": "m1"}],
        quest_state={"parcel_done": False},
    )
    assert action == "probe"


def test_choose_action_no_matches_returns_neutral_reply():
    action = choose_action(
        npc_role="villager",
        emotion_label="neutral",
        relation={},
        top_memories=[],
        quest_state={"parcel_done": False},
    )
    assert action == "neutral_reply"


def test_keyword_parsing_handles_punctuation_and_multiword_formatting():
    memory = {
        "keywords": "north-gate, parcel road",
        "importance": 0.0,
        "emotion_tag": "neutral",
    }
    score = score_memory("The north gate road is blocked.", "hostile", memory)
    assert score == 3.0


def test_irrelevant_memories_do_not_trigger_probe_and_return_neutral_reply():
    memories = [
        {"keywords": "market,apple", "importance": 0.0, "emotion_tag": "friendly"},
        {"keywords": "river,boat", "importance": 0.0, "emotion_tag": "hostile"},
    ]
    relevant = top_memories("gate permit", "neutral", memories, limit=2)

    action = choose_action(
        npc_role="villager",
        emotion_label="neutral",
        relation={},
        top_memories=relevant,
        quest_state={"parcel_done": False},
    )
    assert relevant == []
    assert action == "neutral_reply"
