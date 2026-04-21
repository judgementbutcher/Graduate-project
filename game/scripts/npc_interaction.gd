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
		get_tree().call_group(
			"dialogue_manager",
			"open_dialogue",
			npc_id,
			npc_name,
			selected_option
		)


func _on_body_entered(_body: Node) -> void:
	player_in_range = true


func _on_body_exited(_body: Node) -> void:
	player_in_range = false
