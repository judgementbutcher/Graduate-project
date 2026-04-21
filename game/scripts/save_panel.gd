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
	status_label.text = str(result.get("status", "save_failed"))


func _load_game() -> void:
	var result := await ApiClient.get_json("/api/save/load?player_id=%d" % GameState.player_id)
	GameState.current_scene = str(result.get("scene_id", "village"))
	status_label.text = "loaded %s" % GameState.current_scene
	get_tree().change_scene_to_file("res://scenes/Main.tscn")
