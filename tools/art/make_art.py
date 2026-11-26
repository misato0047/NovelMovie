"""NovelMovie の素材をコードで描くスクリプト（シルエット調のドット絵）

使い方:  python tools/art/make_art.py
  assets/bg/ と assets/chara/ に PNG を書き出す。

絵柄のルール
  - 背景は 480x270 ドット。Godot 側で 4 倍（1920x1080）に拡大して表示する
  - 人物は高さ 256 ドット。背景と同じ 1 ドット = 4px で表示される
  - 色はほぼ黒〜青灰色だけ。差し色は赤を一点だけ使う
  - 人物は顔や表情を描かない。輪郭と姿勢、光る目で見せる
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BG_DIR = os.path.join(ROOT, "assets", "bg")
CH_DIR = os.path.join(ROOT, "assets", "chara")

# ---- 共通パレット（暗い青灰色の階調） ----
PALETTE = np.array([
    (4, 4, 6), (9, 10, 13), (14, 15, 19), (20, 22, 27), (27, 29, 35),
    (35, 38, 45), (45, 49, 57), (58, 63, 72), (74, 80, 88), (95, 102, 108),
    (122, 130, 132), (160, 170, 168), (205, 214, 208),
], dtype=np.float32)
RED = (196, 32, 28)
RED_DIM = (92, 18, 18)

BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0


def to_palette(img_f):
    """明るさの連続値(0..1)をパレットの階調へ。ディザで中間を表現する"""
    lv = np.clip(img_f, 0, 1) * (len(PALETTE) - 1)
    h, w = lv.shape
    th = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]
    idx = np.floor(lv + (th - 0.5) * 0.9).astype(int)
    idx = np.clip(idx, 0, len(PALETTE) - 1)
    return PALETTE[idx].astype(np.uint8)


# =====================================================================
# 背景：夜の学校の廊下（一点透視）
# =====================================================================

def bg_corridor(name="corridor_night", seed=1, lit=(2,), w=480, h=270):
    rnd = random.Random(seed)
    vx, vy = w // 2, int(h * 0.44)
    fw, fh = 64, 42
    fx0, fy0, fx1, fy1 = vx - fw // 2, vy - fh // 2, vx + fw // 2, vy + fh // 2

    # 明るさ（0..1）を面ごとに描く
    base = Image.new("F", (w, h), 0.0)
    d = ImageDraw.Draw(base)
    d.polygon([(0, h), (w, h), (fx1, fy1), (fx0, fy1)], fill=0.22)    # 床
    d.polygon([(0, 0), (w, 0), (fx1, fy0), (fx0, fy0)], fill=0.12)    # 天井
    d.polygon([(0, 0), (fx0, fy0), (fx0, fy1), (0, h)], fill=0.30)    # 左壁
    d.polygon([(w, 0), (fx1, fy0), (fx1, fy1), (w, h)], fill=0.26)    # 右壁
    d.rectangle([fx0, fy0, fx1, fy1], fill=0.0)                       # 奥の闇

    def wall_pt(side, t, v):
        """side=-1 左壁 / 1 右壁、t=奥行き(0手前..1奥)、v=高さ(0天井..1床)"""
        k = t ** 0.55
        x_near = 0 if side < 0 else w
        x_far = fx0 if side < 0 else fx1
        x = x_near + (x_far - x_near) * k
        top = 0 + (fy0 - 0) * k
        bot = h + (fy1 - h) * k
        return (x, top + (bot - top) * v)

    # 床板の継ぎ目（奥へ向かう線）
    for i in range(-9, 10):
        x_near = vx + i * 34
        x_far = vx + i * (fw / 18)
        d.line([(x_near, h), (x_far, fy1)], fill=0.17)

    # 左右のドアと窓
    for side in (-1, 1):
        for j in range(5):
            t0 = 0.08 + j * 0.19
            t1 = t0 + 0.09
            p = [wall_pt(side, t0, 0.32), wall_pt(side, t1, 0.32), wall_pt(side, t1, 0.97), wall_pt(side, t0, 0.97)]
            d.polygon(p, fill=0.13, outline=0.08)                       # 引き戸
            q = [wall_pt(side, t0 + 0.015, 0.38), wall_pt(side, t1 - 0.015, 0.38),
                 wall_pt(side, t1 - 0.015, 0.55), wall_pt(side, t0 + 0.015, 0.55)]
            d.polygon(q, fill=0.05)                                     # 戸の小窓
            if side < 0:                                                # 左は廊下側の窓（月明かり）
                t2, t3 = t1 + 0.02, t1 + 0.08
                r = [wall_pt(side, t2, 0.12), wall_pt(side, t3, 0.12), wall_pt(side, t3, 0.5), wall_pt(side, t2, 0.5)]
                d.polygon(r, fill=0.36, outline=0.1)
        # 腰板の線
        d.line([wall_pt(side, 0, 0.66), wall_pt(side, 1, 0.66)], fill=0.18)

    # 蛍光灯
    tubes = []
    for k in range(5):
        t = 0.05 + k * 0.2
        s = 1 - t ** 0.55 * (1 - fw / w)
        y = 0 + (fy0 - 0) * t ** 0.55 + 4 * s
        half = 26 * s
        tubes.append((vx, y, half, s, k in lit))
        d.rectangle([vx - half, y, vx + half, y + max(1, 3 * s)], fill=0.9 if k in lit else 0.2)

    a = np.array(base, dtype=np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)

    # 点いている蛍光灯の光だまり（天井と床）
    for (cx, cy, half, s, on) in tubes:
        if not on:
            continue
        g1 = np.exp(-(((xx - cx) / (90 * s)) ** 2 + ((yy - cy) / (40 * s)) ** 2))
        floor_y = h + (fy1 - h) * ((cy / fy0) if fy0 else 0)
        g2 = np.exp(-(((xx - cx) / (120 * s)) ** 2 + ((yy - floor_y) / (30 * s)) ** 2))
        a = a * (1 + 1.3 * g1 + 1.2 * g2) + 0.25 * g1

    # 奥ほど暗く、周辺減光
    depth = np.clip(1 - np.maximum(np.abs(xx - vx) / (w / 2), np.abs(yy - vy) / (h / 2)), 0, 1)
    a *= 1 - 0.85 * depth ** 1.6
    r = np.sqrt(((xx - vx) / w) ** 2 + ((yy - vy) / h) ** 2)
    a *= np.clip(1.25 - r * 1.1, 0.35, 1)

    # 汚れ・ムラ
    rng = np.random.default_rng(seed)
    a *= 1 + rng.normal(0, 0.05, a.shape)
    a = np.clip(a * 1.9, 0, 1) ** 0.85

    out = Image.fromarray(to_palette(a), "RGB")
    out.save(os.path.join(BG_DIR, name + ".png"))
    return out


# =====================================================================
# 人物：少女のシルエット（高さ 256 ドット）
# =====================================================================

SIL = (8, 8, 11, 255)
RIM = (52, 58, 70, 255)
RIM2 = (30, 33, 41, 255)


def _hair(d, cx, cy, rnd, length=100, spread=19):
    """頭頂から垂れる長い髪。毛先をばらつかせる"""
    d.ellipse([cx - 17, cy - 22, cx + 17, cy + 18], fill=SIL)
    d.polygon([(cx - 18, cy - 6), (cx + 18, cy - 6), (cx + spread, cy + length - 40),
               (cx - spread, cy + length - 40)], fill=SIL)
    for x in range(cx - spread + 1, cx + spread):
        end = cy + length - 40 + rnd.randint(-6, 14)
        d.line([(x, cy + length - 60), (x, end)], fill=SIL)
    for _ in range(5):                                                   # 跳ねた毛
        x = cx + rnd.choice([-1, 1]) * rnd.randint(15, 20)
        y = cy + rnd.randint(-10, 40)
        d.line([(x, y), (x + rnd.randint(-3, 3), y + rnd.randint(6, 18))], fill=SIL)


def _body(d, cx, top, rnd, arms="down"):
    """セーラー服・スカート・脚"""
    sh = top                                                            # 肩の高さ
    d.polygon([(cx - 22, sh), (cx + 22, sh), (cx + 25, sh + 56), (cx - 25, sh + 56)], fill=SIL)   # 胴
    d.polygon([(cx - 22, sh), (cx - 30, sh + 6), (cx - 24, sh + 12)], fill=SIL)                    # 襟の張り
    d.polygon([(cx + 22, sh), (cx + 30, sh + 6), (cx + 24, sh + 12)], fill=SIL)
    sk = sh + 52                                                        # スカート
    d.polygon([(cx - 25, sk), (cx + 25, sk), (cx + 34, sk + 48), (cx - 34, sk + 48)], fill=SIL)
    for x in range(cx - 33, cx + 34, 5):                                # プリーツの裾
        d.polygon([(x, sk + 47), (x + 4, sk + 47), (x + 2, sk + 50)], fill=SIL)
    leg_top, leg_bot = sk + 48, 248
    for lx in (cx - 12, cx + 3):                                        # 脚と靴
        d.rectangle([lx, leg_top - 2, lx + 8, leg_bot], fill=SIL)
        d.rectangle([lx - 1, leg_bot - 3, lx + 10, leg_bot + 4], fill=SIL)
    if arms == "down":                                                  # だらりと下げた腕
        for side in (-1, 1):
            x0 = cx + side * 24
            d.polygon([(x0, sh + 4), (x0 + side * 6, sh + 6), (x0 + side * 9, sh + 86),
                       (x0 + side * 4, sh + 88)], fill=SIL)
            d.ellipse([x0 + side * 4 - 3, sh + 84, x0 + side * 4 + 4, sh + 94], fill=SIL)


def _finish(img, eyes, lowered=False):
    """輪郭に光を当て、目を光らせる"""
    a = np.array(img)
    m = a[..., 3] > 0
    up = np.zeros_like(m); up[1:] = m[:-1]
    lf = np.zeros_like(m); lf[:, 1:] = m[:, :-1]
    rt = np.zeros_like(m); rt[:, :-1] = m[:, 1:]
    top_edge = m & ~up
    side_edge = m & ~lf
    a[side_edge] = RIM2
    a[top_edge] = RIM
    for (x, y) in eyes:                                                 # 赤い目と、にじむ光
        for dx, dy in ((-1, 0), (2, 0), (0, -1), (1, -1), (0, 1), (1, 1)):
            if a[y + dy, x + dx, 3] > 0:
                a[y + dy, x + dx, :3] = RED_DIM
        a[y, x, :3] = RED
        a[y, x + 1, :3] = RED
    return Image.fromarray(a, "RGBA")


def _close(img):
    """回転でできた1ドットのすき間を埋める"""
    a = np.array(img)
    m = a[..., 3] > 0
    dil = m.copy()
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        dil |= np.roll(np.roll(m, dy, 0), dx, 1)
    ero = dil.copy()
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        ero &= np.roll(np.roll(dil, dy, 0), dx, 1)
    a[ero & ~m] = SIL
    return Image.fromarray(a, "RGBA")


def chara_girl(pose, seed=7):
    rnd = random.Random(seed)
    w, h = 120, 256
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = w // 2
    if pose == "normal":
        _body(d, cx, 70, rnd)
        _hair(d, cx, 40, rnd)
        d.rectangle([cx - 5, 56, cx + 5, 72], fill=SIL)                 # 首
        img = _finish(img, eyes=[(cx + 6, 40)])
    elif pose == "down":                                                # うつむき：頭が下がり、目は見えない
        _body(d, cx, 70, rnd)
        _hair(d, cx, 50, rnd, length=104)
        d.rectangle([cx - 5, 62, cx + 5, 72], fill=SIL)
        img = _finish(img, eyes=[])
    elif pose == "tilt":                                                # 首を不自然に傾ける
        _body(d, cx, 70, rnd)
        d.rectangle([cx - 5, 56, cx + 5, 72], fill=SIL)
        head = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        hd = ImageDraw.Draw(head)
        _hair(hd, cx, 40, random.Random(seed))
        head = head.rotate(-38, resample=Image.NEAREST, center=(cx, 62))
        head = _close(head)
        img.alpha_composite(head)
        img = _finish(img, eyes=[])
        ex, ey = cx + 13, 44                                            # 傾いた頭の位置に目を置き直す
        a = np.array(img); a[ey, ex, :3] = RED; a[ey, ex + 1, :3] = RED
        a[ey + 1, ex, :3] = RED_DIM; a[ey - 1, ex + 1, :3] = RED_DIM
        img = Image.fromarray(a, "RGBA")
    img.save(os.path.join(CH_DIR, f"girl_{pose}.png"))
    return img


if __name__ == "__main__":
    os.makedirs(BG_DIR, exist_ok=True)
    os.makedirs(CH_DIR, exist_ok=True)
    bg_corridor()
    for p in ("normal", "down", "tilt"):
        chara_girl(p)
    print("done")
