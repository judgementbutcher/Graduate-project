extends Node

const BASE_URL := "http://127.0.0.1:8000"


func post_json(path: String, body: Dictionary) -> Dictionary:
	var http := HTTPRequest.new()
	add_child(http)

	var headers := PackedStringArray(["Content-Type: application/json"])
	var error := http.request(
		BASE_URL + path,
		headers,
		HTTPClient.METHOD_POST,
		JSON.stringify(body)
	)
	if error != OK:
		http.queue_free()
		return {"error": "request_failed"}

	var result := await http.request_completed
	http.queue_free()
	var parsed := JSON.parse_string(result[3].get_string_from_utf8())
	return parsed if parsed != null else {"error": "bad_response"}


func get_json(path: String) -> Dictionary:
	var http := HTTPRequest.new()
	add_child(http)

	var error := http.request(BASE_URL + path)
	if error != OK:
		http.queue_free()
		return {"error": "request_failed"}

	var result := await http.request_completed
	http.queue_free()
	var parsed := JSON.parse_string(result[3].get_string_from_utf8())
	return parsed if parsed != null else {"error": "bad_response"}
