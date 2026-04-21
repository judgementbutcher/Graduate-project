from sqlalchemy.orm import Session

from app.models import Player


def write_save(session: Session, payload: dict) -> dict[str, str]:
    player = session.get(Player, payload["player_id"])
    if player is None:
        player = Player(id=payload["player_id"], name="Hero")
        session.add(player)

    player.current_scene = payload["scene_id"]
    player.position_x = float(payload["position_x"])
    player.position_y = float(payload["position_y"])
    session.commit()
    return {"status": "saved"}


def read_save(session: Session, player_id: int) -> dict[str, int | float | str]:
    player = session.get(Player, player_id)
    if player is None:
        return {
            "player_id": player_id,
            "scene_id": "village",
            "position_x": 0.0,
            "position_y": 0.0,
        }

    return {
        "player_id": player.id,
        "scene_id": player.current_scene,
        "position_x": player.position_x,
        "position_y": player.position_y,
    }
