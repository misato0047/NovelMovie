@tool
extends VBoxContainer
## エディタ右側の「NovelMovie」パネル
## 台本を選んで、プレビューと動画の書き出しをボタンだけで行う

const RUN_CFG := "res://.run_settings.cfg"       # ゲーム側が読む再生設定（台本・文字なし）
const OVERRIDE := "res://override.cfg"            # 縦長のときだけ置く画面サイズの上書き
const VERTICAL_CFG := "res://formats/vertical.cfg"
const MOVIE_KEY := "editor/movie_writer/movie_file"

var scen: OptionButton
var chk_h: CheckBox
var chk_v: CheckBox
var chk_nt: CheckBox
var buttons: Array = []
var status: Label

var queue: Array = []
var state := "idle"            # idle / starting / playing
var wait_t := 0.0
var recording := false
var saved_movie_file := ""


func _ready() -> void:
	_build_ui()
	_refresh()


func _build_ui() -> void:
	add_theme_constant_override("separation", 8)
	var t := Label.new()
	t.text = "台本"
	add_child(t)
	var row := HBoxContainer.new()
	add_child(row)
	scen = OptionButton.new()
	scen.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(scen)
	var rb := Button.new()
	rb.text = "更新"
	rb.tooltip_text = "scenario フォルダの台本を読み直す"
	rb.pressed.connect(_refresh)
	row.add_child(rb)

	add_child(HSeparator.new())
	var pt := Label.new()
	pt.text = "プレビュー（録画しない）"
	add_child(pt)
	var prow := HBoxContainer.new()
	add_child(prow)
	var ph := Button.new()
	ph.text = "▶ 横長"
	ph.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ph.pressed.connect(func() -> void: _begin([{"fmt": "16x9", "notext": false}], false))
	prow.add_child(ph)
	var pv := Button.new()
	pv.text = "▶ 縦長"
	pv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pv.pressed.connect(func() -> void: _begin([{"fmt": "9x16", "notext": false}], false))
	prow.add_child(pv)

	add_child(HSeparator.new())
	var rt := Label.new()
	rt.text = "動画の書き出し"
	add_child(rt)
	chk_h = CheckBox.new()
	chk_h.text = "横長 16:9"
	chk_h.button_pressed = true
	add_child(chk_h)
	chk_v = CheckBox.new()
	chk_v.text = "縦長 9:16（ショート）"
	chk_v.button_pressed = true
	add_child(chk_v)
	chk_nt = CheckBox.new()
	chk_nt.text = "文字なし版も書き出す"
	add_child(chk_nt)
	var rec := Button.new()
	rec.text = "● 書き出す"
	rec.pressed.connect(_on_record)
	add_child(rec)
	var op := Button.new()
	op.text = "書き出し先（out フォルダ）を開く"
	op.pressed.connect(_open_out)
	add_child(op)
	buttons = [rb, ph, pv, rec]

	add_child(HSeparator.new())
	status = Label.new()
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	status.custom_minimum_size = Vector2(160, 0)
	status.text = "台本を選んで、プレビューか書き出しを押してください。"
	add_child(status)


func _refresh() -> void:
	var prev := ""
	if scen.item_count > 0 and scen.selected >= 0:
		prev = scen.get_item_text(scen.selected)
	scen.clear()
	var files := DirAccess.get_files_at("res://scenario")
	var names: Array = []
	for f in files:
		if f.ends_with(".txt") and not f.begins_with("_"):
			names.append(f)
	names.sort()
	for n in names:
		scen.add_item(n)
		if n == prev:
			scen.select(scen.item_count - 1)


func _on_record() -> void:
	var jobs: Array = []
	var variants: Array = [false]
	if chk_nt.button_pressed:
		variants.append(true)
	for nt in variants:
		if chk_h.button_pressed:
			jobs.append({"fmt": "16x9", "notext": nt})
		if chk_v.button_pressed:
			jobs.append({"fmt": "9x16", "notext": nt})
	if jobs.is_empty():
		status.text = "横長か縦長のどちらかにチェックを入れてください。"
		return
	_begin(jobs, true)


func _begin(jobs: Array, record: bool) -> void:
	if state != "idle":
		return
	if scen.item_count == 0 or scen.selected < 0:
		status.text = "scenario フォルダに台本（.txt）がありません。"
		return
	if EditorInterface.is_playing_scene():
		EditorInterface.stop_playing_scene()
	queue = jobs.duplicate()
	recording = record
	if record:
		saved_movie_file = str(ProjectSettings.get_setting(MOVIE_KEY, ""))
		if not EditorInterface.has_method("set_movie_maker_enabled"):
			status.text = "※ エディタ右上のフィルム（Movie Maker）ボタンを押して有効にしてから、もう一度書き出してください。"
	for b in buttons:
		(b as Button).disabled = true
	_next()


func _scenario_file() -> String:
	return scen.get_item_text(scen.selected)


func _next() -> void:
	if queue.is_empty():
		_finish()
		return
	var job: Dictionary = queue.pop_front()
	var notext: bool = job["notext"]
	var fmt: String = job["fmt"]
	# ゲーム側が読む設定
	var cf := ConfigFile.new()
	cf.set_value("run", "scenario", "res://scenario/" + _scenario_file())
	cf.set_value("run", "notext", notext)
	cf.save(RUN_CFG)
	# 画面の向き
	if fmt == "9x16":
		DirAccess.copy_absolute(ProjectSettings.globalize_path(VERTICAL_CFG), ProjectSettings.globalize_path(OVERRIDE))
	else:
		_remove_override()
	# 録画
	var label := ("横長" if fmt == "16x9" else "縦長") + ("・文字なし" if notext else "")
	if recording:
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://out"))
		var out := "res://out/%s_%s%s.avi" % [_scenario_file().get_basename(), fmt, "_notext" if notext else ""]
		ProjectSettings.set_setting(MOVIE_KEY, ProjectSettings.globalize_path(out))
		_set_movie_maker(true)
		status.text = "書き出し中：%s（あと%d本）\n終わるまで再生ウィンドウを閉じないでください。" % [label, queue.size()]
	else:
		_set_movie_maker(false)
		status.text = "プレビュー中：%s　（Esc で止まります）" % label
	EditorInterface.play_main_scene()
	state = "starting"
	wait_t = 0.0


func _process(delta: float) -> void:
	if state == "starting":
		wait_t += delta
		if EditorInterface.is_playing_scene() or wait_t > 8.0:
			state = "playing"
	elif state == "playing":
		if not EditorInterface.is_playing_scene():
			state = "idle_between"
			_next_after_stop()


func _next_after_stop() -> void:
	state = "idle"
	if queue.is_empty():
		_finish()
	else:
		state = "busy"
		_next()


func _finish() -> void:
	_remove_override()
	if recording:
		_set_movie_maker(false)
		ProjectSettings.set_setting(MOVIE_KEY, saved_movie_file)
		status.text = "書き出しが終わりました。「書き出し先を開く」で確認できます。\n（動画と一緒に、字幕 .srt とタイミング表 .csv もできています）"
	else:
		status.text = "プレビューが終わりました。"
	state = "idle"
	recording = false
	for b in buttons:
		(b as Button).disabled = false


func _set_movie_maker(on: bool) -> void:
	if EditorInterface.has_method("set_movie_maker_enabled"):
		EditorInterface.call("set_movie_maker_enabled", on)


func _remove_override() -> void:
	var p := ProjectSettings.globalize_path(OVERRIDE)
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(p)


func _open_out() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://out"))
	OS.shell_open(ProjectSettings.globalize_path("res://out"))
