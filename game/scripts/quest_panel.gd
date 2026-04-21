extends Control

@onready var quest_list: ItemList = %QuestList
@onready var travel_gate_button: Button = %TravelGateButton


func _ready() -> void:
	add_to_group("quest_panel")
	travel_gate_button.pressed.connect(_travel_to_gate)
	refresh()


func refresh() -> void:
	var result := await ApiClient.get_json("/api/quest/list?player_id=%d" % GameState.player_id)
	quest_list.clear()
	for quest in result.get("quests", []):
		quest_list.add_item("%s [%s]" % [quest["title"], quest["status"]])

	GameState.quests = result.get("quests", [])
	travel_gate_button.disabled = true
	for quest in GameState.quests:
		if quest["quest_id"] == 1 and quest["status"] == "active":
			travel_gate_button.disabled = false
			break


func _travel_to_gate() -> void:
	GameState.current_scene = "gate"
	get_tree().change_scene_to_file("res://scenes/Main.tscn")
