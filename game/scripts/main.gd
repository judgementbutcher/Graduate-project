extends Node

const SCENE_MAP := {
	"village": preload("res://scenes/WorldVillage.tscn"),
	"gate": preload("res://scenes/WorldGate.tscn")
}

@onready var world_root: Node = $WorldRoot


func _ready() -> void:
	_load_current_world()


func _load_current_world() -> void:
	for child in world_root.get_children():
		child.queue_free()

	var next_scene: PackedScene = SCENE_MAP.get(GameState.current_scene, SCENE_MAP["village"])
	world_root.add_child(next_scene.instantiate())
