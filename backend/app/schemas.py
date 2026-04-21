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
