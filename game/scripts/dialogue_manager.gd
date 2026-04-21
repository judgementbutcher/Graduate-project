extends Control

@onready var reply_label: RichTextLabel = %ReplyLabel
@onready var option_help: Button = %OptionHelp
@onready var option_polite: Button = %OptionPolite
@onready var option_demand: Button = %OptionDemand

var current_npc_id := 1
var current_npc_name := ""


func _ready() -> void:
	add_to_group("dialogue_manager")
	visible = false
	option_help.pressed.connect(_submit.bind("Please help me understand what happened.", "ask_for_help"))
	option_polite.pressed.connect(_submit.bind("Thanks for speaking with me.", "be_polite"))
	option_demand.pressed.connect(_submit.bind("Tell me everything right now.", "demand_entry"))


func open_dialogue(npc_id: int, npc_name: String, _default_option: String) -> void:
	current_npc_id = npc_id
	current_npc_name = npc_name
	reply_label.text = "Talking to %s" % npc_name
	visible = true


func _submit(text: String, selected_option: String) -> void:
	var payload := {
		"player_id": GameState.player_id,
		"npc_id": current_npc_id,
		"scene_id": GameState.current_scene,
		"input_text": text,
		"selected_option": selected_option
	}
	var result := await ApiClient.post_json("/api/dialogue/interact", payload)
	if result.has("error"):
		reply_label.text = "The system is busy. Please try again."
		return

	GameState.last_dialogue = result
	reply_label.text = result.get("npc_reply", "The NPC stays silent.")
	get_tree().call_group("quest_panel", "refresh")
