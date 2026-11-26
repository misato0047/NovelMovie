extends Control
## NovelMovie 再生エンジン
## scenario/*.txt の台本を上から順に再生する。最後まで行くと自動で終了する。
## 横長(16:9)・縦長(9:16)は画面サイズから自動判定してレイアウトを切り替える。

const DEFAULT_SCENARIO := "res://scenario/sample.txt"
const IMG_EXT := ["png", "jpg", "jpeg", "webp"]
const AUDIO_EXT := ["ogg", "wav", "mp3"]

const POST_SHADER := """
shader_type canvas_item;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform float noise_amount = 0.0;
uniform float vignette = 0.0;
uniform float aberration = 0.0;
uniform float glitch = 0.0;

float rand(vec2 co) {
	return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
	vec2 uv = SCREEN_UV;
	float t = floor(TIME * 24.0);
	if (glitch > 0.0) {
		float band = floor(uv.y * 36.0);
		float r = rand(vec2(band, t));
		if (r < glitch * 0.45) {
			uv.x += (rand(vec2(t, band)) - 0.5) * 0.09 * glitch;
		}
	}
	float ab = aberration * 0.004 + glitch * 0.006;
	vec3 col;
	col.r = texture(screen_tex, uv + vec2(ab, 0.0)).r;
	col.g = texture(screen_tex, uv).g;
	col.b = texture(screen_tex, uv - vec2(ab, 0.0)).b;
	float n = rand(SCREEN_UV * 1000.0 + vec2(t * 0.37, t * 0.71)) - 0.5;
	col += n * noise_amount * 0.45;
	vec2 d = SCREEN_UV - 0.5;
	col *= clamp(1.0 - dot(d, d) * vignette * 2.4, 0.0, 1.0);
	COLOR = vec4(col, 1.0);
}
"""

# ---- 再生設定（台本の @speed / @autowait で変更可） ----
var text_speed := 20.0      # 1秒あたりの文字数
var auto_wait := 1.0        # 1行表示し終えてから次へ進むまでの待ち（秒）
var per_char_wait := 0.04   # 文字数に応じて追加で待つ秒数（長い文ほど長く読ませる）

var W := 1920.0
var H := 1080.0
var vertical := false
var textbox_on := true
var stopped := false
var font: Font
var fs := 40

var stage: Control
var bg_a: TextureRect
var bg_b: TextureRect
var chara_layer: Control
var charas := {}
var post: ColorRect
var post_mat: ShaderMaterial
var textbox: Panel
var body: RichTextLabel
var name_label: Label
var title_label: Label
var notice_label: Label
var flash_rect: ColorRect
var fade_rect: ColorRect
var bgm: AudioStreamPlayer
var voice: AudioStreamPlayer
var pending_voice: AudioStream = null
var bgm_loop := false
var fx := {"noise_amount": 0.0, "vignette": 0.0, "aberration": 0.0}

var shake_time := 0.0
var shake_total := 0.0
var shake_power := 0.0

var speech_re := RegEx.create_from_string("^([^「『\\s]{1,12})([「『].*[」』])$")
var tag_re := RegEx.create_from_string("\\[[^\\]]*\\]")


func _ready() -> void:
	var vs: Vector2 = get_viewport().get_visible_rect().size
	W = vs.x
	H = vs.y
	vertical = H > W
	font = _load_font()
	_build()
	var path := DEFAULT_SCENARIO
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--scenario="):
			path = arg.substr(11).strip_edges().trim_prefix("\"").trim_suffix("\"")
	if not path.begins_with("res://") and not path.is_absolute_path():
		path = "res://" + path
	_run(path)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().quit()


func _process(delta: float) -> void:
	if shake_time > 0.0:
		shake_time -= delta
		var p := shake_power * clampf(shake_time / maxf(shake_total, 0.001), 0.0, 1.0)
		stage.position = Vector2(randf_range(-p, p), randf_range(-p, p))
		if shake_time <= 0.0:
			stage.position = Vector2.ZERO


# =====================================================================
# 画面の組み立て
# =====================================================================

func _build() -> void:
	stage = Control.new()
	stage.size = Vector2(W, H)
	stage.pivot_offset = Vector2(W, H) / 2.0
	stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# ドット絵をくっきり表示（拡大してもぼやけない）。背景と立ち絵はすべてこの設定を引き継ぐ
	stage.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(stage)

	bg_a = _make_bg()
	bg_b = _make_bg()
	bg_b.modulate.a = 0.0
	stage.add_child(bg_a)
	stage.add_child(bg_b)
	bg_a.texture = _solid(Color.BLACK)

	chara_layer = Control.new()
	chara_layer.size = Vector2(W, H)
	chara_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stage.add_child(chara_layer)

	# 画面全体にかかるノイズ・周辺減光・グリッチ
	post = ColorRect.new()
	post.size = Vector2(W, H)
	post.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = POST_SHADER
	post_mat = ShaderMaterial.new()
	post_mat.shader = sh
	post.material = post_mat
	add_child(post)

	# テキストボックスの位置と文字サイズ（縦長はショートのUIに隠れない位置へ）
	var box: Rect2
	if vertical:
		box = Rect2(W * 0.05, H * 0.585, W * 0.90, H * 0.19)
		fs = int(W * 0.047)
	else:
		box = Rect2(W * 0.08, H * 0.70, W * 0.84, H * 0.26)
		fs = int(H * 0.040)

	textbox = Panel.new()
	textbox.position = box.position
	textbox.size = box.size
	textbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0.62)
	sb.border_color = Color(1, 1, 1, 0.16)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(6)
	textbox.add_theme_stylebox_override("panel", sb)
	textbox.visible = false
	add_child(textbox)

	var pad := fs * 0.9
	body = RichTextLabel.new()
	body.bbcode_enabled = true
	body.scroll_active = false
	body.fit_content = false
	body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	body.position = Vector2(pad, pad * 0.75)
	body.size = box.size - Vector2(pad * 2.0, pad * 1.5)
	body.add_theme_font_override("normal_font", font)
	body.add_theme_font_size_override("normal_font_size", fs)
	body.add_theme_color_override("default_color", Color(0.93, 0.92, 0.90))
	body.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
	body.add_theme_constant_override("shadow_offset_x", 2)
	body.add_theme_constant_override("shadow_offset_y", 2)
	body.add_theme_constant_override("line_separation", int(fs * 0.35))
	textbox.add_child(body)

	name_label = Label.new()
	name_label.add_theme_font_override("font", font)
	name_label.add_theme_font_size_override("font_size", int(fs * 0.85))
	name_label.add_theme_color_override("font_color", Color(0.86, 0.78, 0.66))
	var nsb := StyleBoxFlat.new()
	nsb.bg_color = Color(0, 0, 0, 0.75)
	nsb.border_color = Color(1, 1, 1, 0.16)
	nsb.set_border_width_all(2)
	nsb.set_corner_radius_all(4)
	nsb.content_margin_left = fs * 0.6
	nsb.content_margin_right = fs * 0.6
	nsb.content_margin_top = fs * 0.15
	nsb.content_margin_bottom = fs * 0.15
	name_label.add_theme_stylebox_override("normal", nsb)
	name_label.position = box.position + Vector2(fs * 0.5, -fs * 1.45)
	name_label.visible = false
	add_child(name_label)

	title_label = Label.new()
	title_label.size = Vector2(W, H)
	title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	title_label.add_theme_font_override("font", font)
	title_label.add_theme_font_size_override("font_size", int(fs * 1.8))
	title_label.add_theme_color_override("font_color", Color(0.9, 0.88, 0.85))
	title_label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 1))
	title_label.add_theme_constant_override("shadow_offset_x", 3)
	title_label.add_theme_constant_override("shadow_offset_y", 3)
	title_label.modulate.a = 0.0
	add_child(title_label)

	flash_rect = ColorRect.new()
	flash_rect.size = Vector2(W, H)
	flash_rect.color = Color.WHITE
	flash_rect.modulate.a = 0.0
	flash_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(flash_rect)

	fade_rect = ColorRect.new()
	fade_rect.size = Vector2(W, H)
	fade_rect.color = Color.BLACK
	fade_rect.modulate.a = 0.0
	fade_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(fade_rect)

	# 素材が見つからないときの警告（動画書き出し中は表示しない）
	notice_label = Label.new()
	notice_label.position = Vector2(16, 12)
	notice_label.add_theme_font_override("font", font)
	notice_label.add_theme_font_size_override("font_size", 22)
	notice_label.add_theme_color_override("font_color", Color(1, 0.4, 0.3))
	add_child(notice_label)

	bgm = AudioStreamPlayer.new()
	add_child(bgm)
	bgm.finished.connect(_on_bgm_finished)
	voice = AudioStreamPlayer.new()
	add_child(voice)


func _make_bg() -> TextureRect:
	var t := TextureRect.new()
	t.size = Vector2(W, H)
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return t


func _load_font() -> Font:
	for f in ["main.ttf", "main.otf", "main.woff2", "main.woff"]:
		var p := ProjectSettings.globalize_path("res://assets/fonts/" + f)
		if FileAccess.file_exists(p):
			var ff := FontFile.new()
			if ff.load_dynamic_font(p) == OK:
				return ff
	var sf := SystemFont.new()
	sf.font_names = PackedStringArray(["Yu Mincho", "游明朝", "Noto Serif JP", "Noto Serif CJK JP", "Hiragino Mincho ProN", "MS PMincho", "serif"])
	return sf


# =====================================================================
# 台本の実行
# =====================================================================

func _run(path: String) -> void:
	await get_tree().process_frame
	if not FileAccess.file_exists(path):
		textbox.visible = true
		body.text = "台本が見つかりません：\n" + path
		return
	var lines := FileAccess.get_file_as_string(path).replace("\r", "").split("\n")
	for raw: String in lines:
		if stopped:
			break
		await _exec(raw)
	await _sleep(0.5)
	get_tree().quit()


func _exec(raw: String) -> void:
	var line := raw.strip_edges()
	if line == "" or line.begins_with("#") or line.begins_with("//"):
		return
	if line.begins_with("@") or line.begins_with("＠"):
		var parts := line.substr(1).replace("　", " ").split(" ", false)
		if parts.is_empty():
			return
		var cmd := parts[0].to_lower()
		parts.remove_at(0)
		var a := _parse_args(parts)
		if a["nowait"]:
			_dispatch(cmd, a)
		else:
			await _dispatch(cmd, a)
	else:
		await _text_line(line)


func _parse_args(parts: PackedStringArray) -> Dictionary:
	var pos: Array = []
	var kw := {}
	var nowait := false
	for p: String in parts:
		if p == "nowait":
			nowait = true
			continue
		var eq := p.find("=")
		if eq > 0:
			kw[p.substr(0, eq).to_lower()] = p.substr(eq + 1)
		else:
			pos.append(p)
	return {"pos": pos, "kw": kw, "nowait": nowait}


func _p(a: Dictionary, i: int, def: String = "") -> String:
	var pos: Array = a["pos"]
	return str(pos[i]) if pos.size() > i else def


func _pf(a: Dictionary, i: int, def: float) -> float:
	var pos: Array = a["pos"]
	return float(pos[i]) if pos.size() > i else def


func _k(a: Dictionary, key: String, def: String = "") -> String:
	var kw: Dictionary = a["kw"]
	return str(kw[key]) if kw.has(key) else def


func _kf(a: Dictionary, key: String, def: float) -> float:
	var kw: Dictionary = a["kw"]
	return float(kw[key]) if kw.has(key) else def


func _dispatch(cmd: String, a: Dictionary) -> void:
	match cmd:
		"bg":
			await _cmd_bg(a)
		"chara", "ch":
			await _cmd_chara(a)
		"move":
			await _cmd_move(a)
		"hide":
			await _cmd_hide(_p(a, 0), _kf(a, "fade", 0.4))
		"hideall":
			var dur := _kf(a, "fade", 0.4)
			for n in charas.keys():
				_cmd_hide(str(n), dur)
			await _sleep(dur)
		"say":
			var pos: Array = a["pos"]
			if pos.size() >= 2:
				var t := " ".join(PackedStringArray(pos.slice(1)))
				await _show_line(str(pos[0]), "「" + t + "」")
		"voice":
			pending_voice = _load_audio("res://assets/voice/" + _p(a, 0))
		"wait":
			await _sleep(_pf(a, 0, 1.0))
		"fadeout":
			fade_rect.color = Color.from_string(_k(a, "color", "black"), Color.BLACK)
			await _tween(fade_rect, "modulate:a", 1.0, _pf(a, 0, 1.0))
		"fadein":
			await _tween(fade_rect, "modulate:a", 0.0, _pf(a, 0, 1.0))
		"flash":
			flash_rect.color = Color.from_string(_k(a, "color", "white"), Color.WHITE)
			flash_rect.modulate.a = 1.0
			await _tween(flash_rect, "modulate:a", 0.0, _pf(a, 0, 0.15))
		"shake":
			shake_total = _pf(a, 0, 0.4)
			shake_time = shake_total
			shake_power = _kf(a, "power", 24.0) * (W / 1920.0 if not vertical else H / 1920.0)
			await _sleep(shake_total)
		"zoom":
			stage.pivot_offset = Vector2(W * _kf(a, "x", 0.5), H * _kf(a, "y", 0.5))
			var s := _pf(a, 0, 1.0)
			await _tween(stage, "scale", Vector2(s, s), _pf(a, 1, 1.0))
		"noise":
			await _tween_param("noise_amount", _pf(a, 0, 0.0), _kf(a, "fade", 0.0))
		"vignette":
			await _tween_param("vignette", _pf(a, 0, 0.0), _kf(a, "fade", 0.0))
		"aberration":
			await _tween_param("aberration", _pf(a, 0, 0.0), _kf(a, "fade", 0.0))
		"glitch":
			post_mat.set_shader_parameter("glitch", _kf(a, "power", 1.0))
			await _sleep(_pf(a, 0, 0.4))
			post_mat.set_shader_parameter("glitch", 0.0)
		"bgm":
			await _cmd_bgm(a)
		"bgmstop":
			bgm_loop = false
			await _tween(bgm, "volume_db", -60.0, _kf(a, "fade", 1.5))
			bgm.stop()
		"se":
			var st := _load_audio("res://assets/se/" + _p(a, 0))
			if st != null:
				var pl := AudioStreamPlayer.new()
				pl.stream = st
				pl.volume_db = _kf(a, "vol", 0.0)
				add_child(pl)
				pl.finished.connect(pl.queue_free)
				pl.play()
				if _k(a, "wait") == "true":
					await pl.finished
		"title":
			var pos2: Array = a["pos"]
			title_label.text = " ".join(PackedStringArray(pos2))
			await _tween(title_label, "modulate:a", 1.0, 0.8)
			await _sleep(_kf(a, "dur", 2.0))
			await _tween(title_label, "modulate:a", 0.0, 0.8)
		"textbox":
			textbox_on = _p(a, 0, "on") != "off"
			textbox.visible = textbox_on and body.text != ""
			name_label.visible = textbox.visible and name_label.text != ""
		"clear":
			body.text = ""
			name_label.text = ""
			name_label.visible = false
			textbox.visible = false
		"speed":
			text_speed = maxf(_pf(a, 0, 20.0), 1.0)
		"autowait":
			auto_wait = _pf(a, 0, 1.0)
		"end":
			stopped = true
		_:
			_notice("不明なコマンド: @" + cmd)


# =====================================================================
# テキスト
# =====================================================================

func _text_line(line: String) -> void:
	var m := speech_re.search(line)
	if m != null:
		await _show_line(m.get_string(1), m.get_string(2))
	else:
		await _show_line("", line)


func _show_line(speaker: String, text: String) -> void:
	if speaker == "":
		name_label.text = ""
		name_label.visible = false
	else:
		name_label.text = speaker
		name_label.visible = textbox_on
	textbox.visible = textbox_on
	body.text = text
	body.visible_characters = 0
	var total := tag_re.sub(text, "", true).length()
	var v := pending_voice
	pending_voice = null
	if v != null:
		voice.stream = v
		voice.play()
	await _tween(body, "visible_characters", total, total / text_speed)
	body.visible_characters = -1
	if v != null and voice.playing:
		await voice.finished
	await _sleep(auto_wait + total * per_char_wait)


# =====================================================================
# 背景・立ち絵
# =====================================================================

func _cmd_bg(a: Dictionary) -> void:
	var nm := _p(a, 0, "black")
	var tex := _load_tex("res://assets/bg/" + nm, "bg")
	var dur := _kf(a, "fade", 1.0)
	bg_b.texture = tex
	bg_b.modulate.a = 0.0
	await _tween(bg_b, "modulate:a", 1.0, dur)
	bg_a.texture = tex
	bg_b.modulate.a = 0.0


func _chara_height() -> float:
	return H * 0.60 if vertical else H * 0.95


func _chara_bottom() -> float:
	return H * 0.80 if vertical else H * 1.02


func _pos_x(place: String) -> float:
	match place:
		"left", "l", "左":
			return W * (0.27 if vertical else 0.25)
		"right", "r", "右":
			return W * (0.73 if vertical else 0.75)
		"center", "c", "中", "":
			return W * 0.5
	return W * float(place)


func _fit_chara(node: TextureRect, cx: float) -> void:
	var h := _chara_height()
	var asp := 0.5
	if node.texture != null and node.texture.get_height() > 0:
		asp = float(node.texture.get_width()) / float(node.texture.get_height())
	node.size = Vector2(h * asp, h)
	node.position = Vector2(cx - h * asp / 2.0, _chara_bottom() - h)


func _cmd_chara(a: Dictionary) -> void:
	var cname := _p(a, 0)
	var face := _p(a, 1)
	var place := _k(a, "pos")
	var dur := _kf(a, "fade", 0.4)
	var file := cname if face == "" else cname + "_" + face
	var tex := _load_tex("res://assets/chara/" + file, "chara")
	if not charas.has(cname):
		var node := TextureRect.new()
		node.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		node.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		node.mouse_filter = Control.MOUSE_FILTER_IGNORE
		node.texture = tex
		chara_layer.add_child(node)
		charas[cname] = node
		_fit_chara(node, _pos_x(place))
		node.modulate.a = 0.0
		await _tween(node, "modulate:a", 1.0, dur)
	else:
		var node: TextureRect = charas[cname]
		var cx := node.position.x + node.size.x / 2.0
		if place != "":
			cx = _pos_x(place)
		# 表情差分：古い絵を上に重ねて消すことでクロスフェード
		var ghost := TextureRect.new()
		ghost.expand_mode = node.expand_mode
		ghost.stretch_mode = node.stretch_mode
		ghost.texture = node.texture
		ghost.position = node.position
		ghost.size = node.size
		chara_layer.add_child(ghost)
		node.texture = tex
		_fit_chara(node, cx)
		await _tween(ghost, "modulate:a", 0.0, dur)
		ghost.queue_free()


func _cmd_move(a: Dictionary) -> void:
	var cname := _p(a, 0)
	if not charas.has(cname):
		return
	var node: TextureRect = charas[cname]
	var cx := _pos_x(_p(a, 1, "center"))
	await _tween(node, "position:x", cx - node.size.x / 2.0, _kf(a, "dur", 0.5))


func _cmd_hide(cname: String, dur: float) -> void:
	if not charas.has(cname):
		return
	var node: TextureRect = charas[cname]
	charas.erase(cname)
	await _tween(node, "modulate:a", 0.0, dur)
	node.queue_free()


# =====================================================================
# 音
# =====================================================================

func _cmd_bgm(a: Dictionary) -> void:
	var st := _load_audio("res://assets/bgm/" + _p(a, 0))
	if st == null:
		return
	var vol := _kf(a, "vol", -8.0)
	bgm.stream = st
	bgm_loop = true
	bgm.volume_db = -60.0
	bgm.play()
	await _tween(bgm, "volume_db", vol, _kf(a, "fade", 1.0))


func _on_bgm_finished() -> void:
	if bgm_loop:
		bgm.play()


# =====================================================================
# 素材の読み込み（見つからない場合は仮の絵で続行）
# =====================================================================

func _load_tex(base: String, kind: String) -> Texture2D:
	var nm := base.get_file()
	match nm:
		"black", "黒":
			return _solid(Color.BLACK)
		"white", "白":
			return _solid(Color.WHITE)
	if nm.begins_with("#"):
		return _solid(Color.from_string(nm, Color.BLACK))
	for ext in IMG_EXT:
		var p: String = base + "." + ext
		if ResourceLoader.exists(p):
			var r = load(p)
			if r is Texture2D:
				return r
		if FileAccess.file_exists(p):
			var img := Image.load_from_file(ProjectSettings.globalize_path(p))
			if img != null:
				return ImageTexture.create_from_image(img)
	_notice("画像が見つかりません: " + base.trim_prefix("res://assets/"))
	return _placeholder(kind)


func _load_audio(base: String) -> AudioStream:
	for ext in AUDIO_EXT:
		var p: String = base + "." + ext
		if ResourceLoader.exists(p):
			var r = load(p)
			if r is AudioStream:
				return r
		if FileAccess.file_exists(p):
			var g := ProjectSettings.globalize_path(p)
			if ext == "ogg":
				return AudioStreamOggVorbis.load_from_file(g)
			if ext == "mp3":
				var m := AudioStreamMP3.new()
				m.data = FileAccess.get_file_as_bytes(g)
				return m
	_notice("音声が見つかりません: " + base.trim_prefix("res://assets/"))
	return null


func _solid(c: Color) -> Texture2D:
	var img := Image.create(8, 8, false, Image.FORMAT_RGBA8)
	img.fill(c)
	return ImageTexture.create_from_image(img)


func _placeholder(kind: String) -> Texture2D:
	var img: Image
	if kind == "chara":
		img = Image.create(300, 640, false, Image.FORMAT_RGBA8)
		img.fill(Color(0, 0, 0, 0))
		var c := Color(0.35, 0.35, 0.4, 0.9)
		for y in range(30, 150):
			for x in range(90, 210):
				if Vector2(x - 150, y - 90).length() < 55.0:
					img.set_pixel(x, y, c)
		img.fill_rect(Rect2i(80, 150, 140, 490), c)
	else:
		img = Image.create(320, 180, false, Image.FORMAT_RGBA8)
		img.fill(Color(0.18, 0.18, 0.22))
	return ImageTexture.create_from_image(img)


func _notice(msg: String) -> void:
	push_warning(msg)
	if OS.has_feature("movie"):
		return
	notice_label.text += msg + "\n"


# =====================================================================
# 補助
# =====================================================================

func _sleep(t: float) -> void:
	if t > 0.0:
		await get_tree().create_timer(t).timeout


func _tween(obj: Object, prop: String, to: Variant, dur: float) -> void:
	if dur <= 0.0:
		obj.set_indexed(prop, to)
		return
	var tw := create_tween()
	tw.tween_property(obj, prop, to, dur).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	await tw.finished


func _tween_param(param: String, to: float, dur: float) -> void:
	var from: float = fx.get(param, 0.0)
	fx[param] = to
	if dur <= 0.0:
		post_mat.set_shader_parameter(param, to)
		return
	var tw := create_tween()
	tw.tween_method(func(v: float) -> void: post_mat.set_shader_parameter(param, v), from, to, dur)
	await tw.finished
