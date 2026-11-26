"""コード絵の共通部品（480x270 ドットの一枚絵を描くための道具）

描き方の流れ
  1. Scene を作り、明るさ（0..1）で面を塗る（環境）
  2. light 系の関数で光と影をつける
  3. 人物はマスクを描いて figure() で塗る（シルエット＋輪郭光）
  4. save() でパレットに落とし、最後に差し色（赤など）を重ねる
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BG_DIR = os.path.join(ROOT, "assets", "bg")

W, H = 480, 270

# ---- パレット（暗→明の階調） ----
PAL_COLD = [(4, 4, 6), (9, 10, 13), (14, 15, 19), (20, 22, 27), (27, 29, 35), (35, 38, 45), (45, 49, 57),
            (58, 63, 72), (74, 80, 88), (95, 102, 108), (122, 130, 132), (160, 170, 168), (205, 214, 208)]
# 教室：色あせた写真のようなセピア
PAL_WARM = [(10, 8, 7), (20, 16, 13), (31, 25, 20), (43, 35, 28), (57, 47, 37), (72, 60, 47), (89, 75, 58),
            (108, 92, 72), (129, 111, 88), (151, 132, 106), (174, 155, 127), (199, 181, 151), (226, 210, 180)]
# 夕方の洋館・食卓：くすんだ紫から橙
PAL_DUSK = [(8, 5, 10), (16, 10, 18), (26, 15, 25), (38, 20, 31), (52, 26, 36), (68, 33, 40), (86, 42, 43),
            (106, 53, 45), (128, 67, 49), (150, 84, 56), (172, 105, 66), (196, 132, 82), (222, 170, 112)]

RED = (196, 32, 28, 255)
RED_DARK = (110, 16, 16, 255)
RED_DIM = (92, 18, 18, 255)

BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0


def to_palette(a, pal):
    pal = np.array(pal, dtype=np.uint8)
    lv = np.clip(a, 0, 1) * (len(pal) - 1)
    h, w = lv.shape
    th = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]
    idx = np.clip(np.floor(lv + (th - 0.5) * 0.9).astype(int), 0, len(pal) - 1)
    return pal[idx]


class Scene:
    def __init__(self, base=0.0, seed=1):
        self.img = Image.new("F", (W, H), base)
        self.d = ImageDraw.Draw(self.img)
        self.acc = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # 差し色レイヤー
        self.ad = ImageDraw.Draw(self.acc)
        self.rnd = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.xx, self.yy = xx, yy

    # ---- numpy との行き来 ----
    @property
    def a(self):
        return np.array(self.img, dtype=np.float32)

    def set(self, arr):
        self.img = Image.fromarray(arr.astype(np.float32), "F")
        self.d = ImageDraw.Draw(self.img)

    # ---- 図形 ----
    def poly(self, pts, v, outline=None):
        self.d.polygon([(float(x), float(y)) for x, y in pts], fill=v, outline=outline)

    def rect(self, x0, y0, x1, y1, v, outline=None):
        self.d.rectangle([x0, y0, x1, y1], fill=v, outline=outline)

    def ellipse(self, x0, y0, x1, y1, v):
        self.d.ellipse([x0, y0, x1, y1], fill=v)

    def line(self, pts, v, width=1):
        self.d.line([(float(x), float(y)) for x, y in pts], fill=v, width=width)

    # ---- 光 ----
    def glow(self, cx, cy, rx, ry, amt):
        """足し算の光（光源そのもの、懐中電灯など）"""
        g = np.exp(-(((self.xx - cx) / rx) ** 2 + ((self.yy - cy) / ry) ** 2))
        self.set(self.a + amt * g)

    def light(self, cx, cy, rx, ry, amt):
        """掛け算の光（照らされた場所を明るく）"""
        g = np.exp(-(((self.xx - cx) / rx) ** 2 + ((self.yy - cy) / ry) ** 2))
        self.set(self.a * (1 + amt * g))

    def vignette(self, strength=1.1, cx=W / 2, cy=H / 2, floor=0.3):
        r = np.sqrt(((self.xx - cx) / W) ** 2 + ((self.yy - cy) / H) ** 2)
        self.set(self.a * np.clip(1.25 - r * strength, floor, 1))

    def grad_y(self, y0, y1, v0, v1):
        t = np.clip((self.yy - y0) / max(1, y1 - y0), 0, 1)
        return v0 + (v1 - v0) * t

    def mul(self, m):
        self.set(self.a * m)

    def grain(self, amt=0.05):
        self.set(self.a * (1 + self.np_rng.normal(0, amt, (H, W))))

    def gain(self, k=1.0, gamma=1.0):
        self.set(np.clip(self.a * k, 0, 1) ** gamma)

    # ---- 人物 ----
    def figure(self, mask, fill=0.03, rim=0.3, rim2=None, shade=None):
        """mask（bool 配列）をシルエットとして塗る。上と左の輪郭に光を当てる
        shade: 塗りに掛ける明るさの配列（白い着物の陰影など）"""
        a = self.a
        f = np.full((H, W), fill, np.float32) if shade is None else fill * shade
        a[mask] = f[mask]
        up = np.zeros_like(mask); up[1:] = mask[:-1]
        lf = np.zeros_like(mask); lf[:, 1:] = mask[:, :-1]
        if rim2 is None:
            rim2 = rim * 0.6
        a[mask & ~lf] = np.maximum(a[mask & ~lf], rim2) if fill < rim2 else a[mask & ~lf]
        a[mask & ~up] = np.maximum(a[mask & ~up], rim) if fill < rim else a[mask & ~up]
        self.set(a)

    # ---- 差し色 ----
    def red(self, x, y, size=1, color=RED):
        self.ad.rectangle([x, y, x + size - 1, y + size - 1], fill=color)

    def red_eye(self, x, y):
        """赤く光る目（2ドット＋にじみ）"""
        for dx, dy in ((-1, 0), (2, 0), (0, -1), (1, -1), (0, 1), (1, 1)):
            self.ad.point((x + dx, y + dy), fill=RED_DIM)
        self.ad.point((x, y), fill=RED)
        self.ad.point((x + 1, y), fill=RED)

    def splatter(self, cx, cy, n, spread, seed=0, dirs=(-math.pi, 0)):
        r = random.Random(seed)
        for _ in range(n):
            ang = r.uniform(*dirs)
            dist = abs(r.gauss(0, spread))
            x, y = cx + math.cos(ang) * dist, cy + math.sin(ang) * dist
            s = 1 if r.random() < 0.7 else 2
            self.ad.rectangle([x, y, x + s - 1, y + s - 1], fill=RED if r.random() < 0.6 else RED_DARK)

    def save(self, name, pal=PAL_COLD):
        rgb = Image.fromarray(to_palette(self.a, pal), "RGB").convert("RGBA")
        rgb.alpha_composite(self.acc)
        rgb.convert("RGB").save(os.path.join(BG_DIR, name + ".png"))
        return rgb


def mask_of(draw_fn):
    """draw_fn(ImageDraw) で描いた形を bool マスクにする"""
    m = Image.new("L", (W, H), 0)
    draw_fn(ImageDraw.Draw(m))
    return np.array(m) > 0


# =====================================================================
# 人物の部品
# =====================================================================

def child(d, cx, foot, h, paper=False):
    """小学1年生の女の子（正面、おかっぱ）。d は mask 用の ImageDraw"""
    hr = h * 0.14
    hy = foot - h + hr
    d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=255)                         # 頭
    d.rectangle([cx - hr * 1.05, hy - hr * 0.2, cx + hr * 1.05, hy + hr * 0.95], fill=255)  # おかっぱ
    sh = hy + hr * 1.05
    d.polygon([(cx - h * 0.13, sh), (cx + h * 0.13, sh), (cx + h * 0.2, foot - h * 0.3),
               (cx - h * 0.2, foot - h * 0.3)], fill=255)                           # 服（ワンピース）
    for lx in (-1, 1):                                                              # 脚
        d.rectangle([cx + lx * h * 0.07 - h * 0.035, foot - h * 0.31, cx + lx * h * 0.07 + h * 0.035, foot], fill=255)
    if paper:                                                                       # 胸の前で作文を持つ腕
        for s in (-1, 1):
            d.polygon([(cx + s * h * 0.12, sh + 2), (cx + s * h * 0.16, sh + 4),
                       (cx + s * h * 0.1, sh + h * 0.2), (cx + s * h * 0.06, sh + h * 0.18)], fill=255)


def adult(d, cx, foot, h, arms="down", hand_y=None, only_arms=False):
    """大人（先生など）の正面シルエット"""
    hr = h * 0.075
    hy = foot - h + hr
    sh = hy + hr * 1.5
    if only_arms:
        _adult_arms(d, cx, foot, h, sh, arms, hand_y)
        return
    d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=255)
    d.rectangle([cx - hr * 0.4, hy + hr * 0.8, cx + hr * 0.4, hy + hr * 1.6], fill=255)
    sh = hy + hr * 1.5
    d.polygon([(cx - h * 0.13, sh), (cx + h * 0.13, sh), (cx + h * 0.12, foot - h * 0.45),
               (cx - h * 0.12, foot - h * 0.45)], fill=255)                         # 上半身
    d.polygon([(cx - h * 0.12, foot - h * 0.46), (cx + h * 0.12, foot - h * 0.46), (cx + h * 0.15, foot - h * 0.12),
               (cx - h * 0.15, foot - h * 0.12)], fill=255)                         # スカート
    for lx in (-1, 1):
        d.rectangle([cx + lx * h * 0.06 - h * 0.025, foot - h * 0.13, cx + lx * h * 0.06 + h * 0.025, foot], fill=255)
    _adult_arms(d, cx, foot, h, sh, arms, hand_y)


def _adult_arms(d, cx, foot, h, sh, arms, hand_y):
    if arms == "none":
        return
    if arms == "down":
        for s in (-1, 1):
            d.polygon([(cx + s * h * 0.13, sh + 1), (cx + s * h * 0.17, sh + 3), (cx + s * h * 0.17, foot - h * 0.42),
                       (cx + s * h * 0.13, foot - h * 0.42)], fill=255)
    else:                                                                            # 拍手：手を胸の前へ
        gap = h * 0.07 if arms == "apart" else h * 0.0
        hy2 = hand_y if hand_y else sh + h * 0.17
        for s in (-1, 1):
            d.polygon([(cx + s * h * 0.13, sh + 1), (cx + s * h * 0.17, sh + 4), (cx + s * (gap + 3), hy2 + 2),
                       (cx + s * gap, hy2 - 3)], fill=255)
            d.ellipse([cx + s * gap - 3, hy2 - 4, cx + s * gap + 3, hy2 + 3], fill=255)


def man(d, cx, foot, h, arm=None, phone=False):
    """男（パーカーとキャップ）。arm=(x, y) で片腕をその方向へ伸ばす"""
    hr = h * 0.075
    hy = foot - h + hr
    d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=255)
    d.polygon([(cx - hr * 1.1, hy - hr * 0.3), (cx + hr * 1.9, hy - hr * 0.3), (cx + hr * 1.9, hy - hr * 0.05),
               (cx - hr * 1.1, hy + hr * 0.1)], fill=255)                           # キャップのつば
    sh = hy + hr * 1.3
    d.polygon([(cx - h * 0.15, sh), (cx + h * 0.15, sh), (cx + h * 0.14, foot - h * 0.46),
               (cx - h * 0.14, foot - h * 0.46)], fill=255)
    d.polygon([(cx - h * 0.13, foot - h * 0.47), (cx + h * 0.13, foot - h * 0.47), (cx + h * 0.11, foot),
               (cx + h * 0.02, foot), (cx, foot - h * 0.3), (cx - h * 0.02, foot), (cx - h * 0.11, foot)], fill=255)
    d.polygon([(cx - h * 0.15, sh + 2), (cx - h * 0.19, sh + 4), (cx - h * 0.18, foot - h * 0.48),
               (cx - h * 0.14, foot - h * 0.48)], fill=255)                         # 下げた左腕
    if arm:
        ax, ay = arm
        d.line([(cx + h * 0.14, sh + 3), (ax, ay)], fill=255, width=max(2, int(h * 0.05)))
    else:
        d.polygon([(cx + h * 0.15, sh + 2), (cx + h * 0.19, sh + 4), (cx + h * 0.18, foot - h * 0.48),
                   (cx + h * 0.14, foot - h * 0.48)], fill=255)


def mother_masks(cx, foot, h, view="front", hair_len=0.55, arm_up=None, head_turn=0, step=0.0):
    """母親：白い着物、床まで届く黒髪、青白い肌。部位ごとのマスクを返す
    view: front / back
    hair_len: 髪の長さ（身長に対する割合。1.0 で床まで）
    arm_up: (x, y) 右手をそこまで上げる（包丁）
    head_turn: 0 / 90 / 180（後ろ姿で頭だけ回す）"""
    hr = h * 0.06
    hy = foot - h + hr
    sh = hy + hr * 1.9
    kimono = Image.new("L", (W, H), 0); dk = ImageDraw.Draw(kimono)
    hair = Image.new("L", (W, H), 0); dh = ImageDraw.Draw(hair)
    skin = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(skin)
    # 着物：肩からくるぶしまで、裾がわずかに広がる
    dk.polygon([(cx - h * 0.11, sh), (cx + h * 0.11, sh), (cx + h * 0.12, foot - h * 0.03),
                (cx - h * 0.12, foot - h * 0.03)], fill=255)
    # 袂（垂れた袖）
    for s in (-1, 1):
        if arm_up is not None and s == 1:
            continue
        dk.polygon([(cx + s * h * 0.1, sh + 1), (cx + s * h * 0.17, sh + h * 0.03), (cx + s * h * 0.19, sh + h * 0.36),
                    (cx + s * h * 0.12, sh + h * 0.38)], fill=255)
        hx = cx + s * h * 0.16
        ds.polygon([(hx - 2, sh + h * 0.36), (hx + 2, sh + h * 0.36), (hx + 1, sh + h * 0.47), (hx - 1, sh + h * 0.47)], fill=255)
    if arm_up is not None:                                                          # 振り上げた右腕
        ax, ay = arm_up
        dk.line([(cx + h * 0.1, sh + 3), (ax, ay + h * 0.05)], fill=255, width=int(h * 0.07))
        ds.ellipse([ax - h * 0.025, ay - h * 0.01, ax + h * 0.025, ay + h * 0.05], fill=255)
    # 足
    for s, dy in ((-1, 0), (1, -step)):
        fx = cx + s * h * 0.045
        ds.polygon([(fx - h * 0.02, foot - h * 0.04 + dy), (fx + h * 0.02, foot - h * 0.04 + dy),
                    (fx + h * 0.025, foot + dy), (fx - h * 0.03, foot + dy)], fill=255)
    # 頭と髪
    dh.ellipse([cx - hr, hy - hr * 1.05, cx + hr, hy + hr], fill=255)
    hl = foot - h * (1 - hair_len)
    if view == "back" or head_turn:
        dh.polygon([(cx - hr * 1.05, hy), (cx + hr * 1.05, hy), (cx + hr * 1.6, hl), (cx - hr * 1.6, hl)], fill=255)
    else:                                                                             # 前髪で顔を隠し、肩から前へ垂らす
        dh.polygon([(cx - hr * 1.05, hy - hr * 0.2), (cx + hr * 1.05, hy - hr * 0.2), (cx + hr * 1.5, hl),
                    (cx + hr * 0.5, hl), (cx, hy + hr * 1.6), (cx - hr * 0.5, hl), (cx - hr * 1.5, hl)], fill=255)
    rr = random.Random(int(cx * 7 + h))
    for i in range(14):                                                               # 毛先のばらつき
        x = cx - hr * 1.5 + i * hr * 3 / 13
        dh.line([(x, hl - 6), (x + rr.randint(-2, 2), hl + rr.randint(0, 6))], fill=255)
    face = None
    eyes = []
    if view == "front":
        eyes = [(int(cx - hr * 0.45), int(hy + hr * 0.1)), (int(cx + hr * 0.25), int(hy + hr * 0.1))]
    if head_turn == 90:                                                               # 横顔が髪から突き出る
        face = Image.new("L", (W, H), 0); ImageDraw.Draw(face).polygon(
            [(cx + hr * 0.6, hy - hr * 0.5), (cx + hr * 1.35, hy - hr * 0.1), (cx + hr * 1.5, hy + hr * 0.3),
             (cx + hr * 1.2, hy + hr * 0.5), (cx + hr * 1.3, hy + hr * 0.8), (cx + hr * 0.6, hy + hr * 0.9)], fill=255)
        eyes = [(int(cx + hr * 1.0), int(hy + hr * 0.05))]
    if head_turn == 180:                                                              # 後ろ姿のまま、顔だけこちらを向く
        face = Image.new("L", (W, H), 0); ImageDraw.Draw(face).ellipse(
            [cx - hr * 0.75, hy - hr * 0.55, cx + hr * 0.75, hy + hr * 0.95], fill=255)
        eyes = [(int(cx - hr * 0.42), int(hy + hr * 0.05)), (int(cx + hr * 0.25), int(hy + hr * 0.05))]
    m = {"kimono": np.array(kimono) > 0, "hair": np.array(hair) > 0, "skin": np.array(skin) > 0,
         "face": (np.array(face) > 0) if face is not None else None, "eyes": eyes, "hy": hy, "hr": hr}
    return m


def draw_mother(sc, m, kimono_v=0.72, skin_v=0.85, light_from=-1, smile=False):
    """mother_masks の結果を Scene に塗る"""
    x0 = np.where(m["kimono"].any(0))[0]
    if len(x0):
        t = (sc.xx - x0.min()) / max(1, x0.max() - x0.min())
        shade = 1.0 - 0.35 * (t if light_from < 0 else 1 - t)
    else:
        shade = None
    sc.figure(m["kimono"], fill=kimono_v, rim=min(1, kimono_v + 0.15), shade=shade)
    a = sc.a
    # 着物のしわ（縦の線）
    k = m["kimono"]
    cols = np.where(k.any(0))[0]
    for c in cols[::5]:
        rows = np.where(k[:, c])[0]
        if len(rows) > 10:
            a[rows[len(rows) // 3:], c] *= 0.82
    sc.set(a)
    sc.figure(m["skin"], fill=skin_v, rim=min(1, skin_v + 0.1))
    hair = m["hair"] if m["face"] is None else (m["hair"] & ~m["face"])
    sc.figure(hair, fill=0.02, rim=0.22)
    if m["face"] is not None:
        sc.figure(m["face"], fill=skin_v * 0.9, rim=skin_v)
        # 前髪が顔に少しかかる
        a = sc.a
        f = m["face"]; ys, xs = np.where(f)
        top = ys.min()
        for x in range(xs.min(), xs.max() + 1, 2):
            a[top:top + 3 + (x % 5), x] = 0.03
        sc.set(a)
    for (ex, ey) in m["eyes"]:
        if smile:
            sc.line([(ex - 1, ey + 1), (ex, ey), (ex + 2, ey), (ex + 3, ey + 1)], 0.05)
        else:
            sc.red_eye(ex, ey)
