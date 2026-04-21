from app.services.decision import choose_action
from app.services.emotion import detect_emotion
from app.services.memory import score_memory


def test_detect_emotion_flags_hostile_text():
    result = detect_emotion("Get out of my way, you liar")
    assert result["label"] == "hostile"


def test_score_memory_gate_match_scores_above_two():
    memory = {
        "keywords": "gate,parcel,road",
        "importance": 1.5,
        "emotion_tag": "hostile",
    }
    score = score_memory("I need to pass the gate now", "hostile", memory)
    assert score > 2


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
