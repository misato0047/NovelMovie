"""「私のお母さんは変わり者」の一枚絵（assets/bg/oka_*.png）

使い方:  python tools/art/okaasan.py          すべて描く
         python tools/art/okaasan.py sheet    確認用の一覧画像も作る
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from pixlib import (BG_DIR, H, PAL_COLD, PAL_DUSK, PAL_WARM, RED, RED_DARK, W, Scene, adult, child,
                    draw_mother, man, mask_of, mother_masks)


# =====================================================================
# 教室（セピア）：教室の後ろから見た黒板、作文を読む女の子、先生
# =====================================================================

def classroom(name, teacher="down"):
    sc = Scene(0.5, seed=11)
    sc.rect(0, 0, W, 205, 0.55)                                          # 前の壁
    sc.rect(0, 205, W, H, 0.38)                                          # 床
    for i in range(0, W, 22):
        sc.line([(i, 205), (i - 40 + i * 0.15, H)], 0.33)
    sc.rect(70, 38, 410, 138, 0.42)                                      # 黒板の枠
    sc.rect(74, 42, 406, 134, 0.16)                                      # 黒板
    for k, (x, y, n) in enumerate([(96, 58, 9), (96, 76, 13), (96, 94, 7)]):   # チョークの文字（読めない程度）
        for j in range(n):
            xx = x + j * 9
            sc.line([(xx, y + sc.rnd.randint(0, 3)), (xx + sc.rnd.randint(3, 7), y + sc.rnd.randint(0, 6))], 0.55)
    sc.rect(150, 30, 330, 35, 0.48)                                      # 掲示物
    sc.rect(300, 150, 372, 210, 0.3, outline=0.22)                       # 教卓
    sc.rect(296, 146, 376, 152, 0.36)
    sc.rect(20, 20, 54, 60, 0.6, outline=0.4)                            # 時計
    sc.light(-40, 80, 260, 200, 0.9)                                     # 左の窓からの光
    sc.vignette(0.9)
    # 女の子（教壇の横で作文を読む）
    girl = mask_of(lambda d: child(d, 214, 214, 92, paper=True))
    sc.figure(girl, fill=0.07, rim=0.3)
    sc.rect(198, 152, 230, 176, 0.92)                                    # 作文の紙
    for y in range(156, 174, 4):
        sc.line([(202, y), (226, y)], 0.7)
    # 先生（右、教卓の横）
    t = mask_of(lambda d: adult(d, 410, 218, 150, arms="none"))
    sc.figure(t, fill=0.08, rim=0.28)
    ar = mask_of(lambda d: adult(d, 410, 218, 150, arms=teacher, only_arms=True))
    sc.figure(ar, fill=0.1, rim=0.42)
    # 手前の席の子どもたちの頭（後ろ姿）
    for x, y, r in [(40, 262, 26), (130, 270, 30), (250, 268, 27), (360, 266, 29), (455, 262, 24)]:
        sc.ellipse(x - r, y - r, x + r, y + r, 0.05)
        sc.line([(x - r * 0.7, y - r * 0.7), (x - r * 0.2, y - r)], 0.15)
    sc.grain(0.04)
    sc.gain(1.0, 0.95)
    sc.save(name, PAL_WARM)


# =====================================================================
# 洋館の外観（森の中、昼でも薄暗い／夕方）
# =====================================================================

def mansion_ext(name, pal, sky=(0.5, 0.35), lit_windows=(), red_window=False):
    sc = Scene(0.0, seed=21)
    sc.set(sc.grad_y(0, 200, sky[0], sky[1]))                            # 空
    for i in range(40):                                                  # 奥の森
        x = i * 13 + sc.rnd.randint(-4, 4)
        top = 70 + sc.rnd.randint(-25, 15)
        sc.poly([(x - 14, 200), (x, top), (x + 14, 200)], 0.2)
    # 洋館
    sc.rect(130, 100, 350, 222, 0.24)                                    # 壁
    sc.poly([(120, 102), (240, 52), (360, 102)], 0.12)                   # 屋根
    sc.rect(215, 70, 265, 222, 0.27)                                     # 中央の塔
    sc.poly([(208, 72), (240, 26), (272, 72)], 0.1)
    for gx in (150, 315):                                                # 左右の破風
        sc.poly([(gx - 22, 104), (gx, 78), (gx + 22, 104)], 0.14)
    sc.rect(110, 76, 118, 104, 0.12); sc.rect(330, 60, 338, 92, 0.12)   # 煙突
    wins = []
    for row, y in enumerate((116, 160)):
        for x in (145, 175, 290, 320):
            wins.append((x, y))
    wins.append((232, 90))
    for i, (x, y) in enumerate(wins):
        v = 0.75 if i in lit_windows else 0.05
        sc.rect(x, y, x + 16, y + 26, v, outline=0.32)
        sc.line([(x + 8, y), (x + 8, y + 26)], 0.32)
        sc.line([(x, y + 12), (x + 16, y + 12)], 0.32)
    sc.rect(226, 172, 254, 222, 0.06, outline=0.3)                       # 玄関
    sc.poly([(220, 172), (240, 160), (260, 172)], 0.2)
    for x in range(130, 350, 6):                                         # 蔦
        if sc.rnd.random() < 0.5:
            y0 = sc.rnd.randint(100, 180)
            sc.line([(x, y0), (x + sc.rnd.randint(-3, 3), y0 + sc.rnd.randint(8, 40))], 0.1)
    sc.rect(0, 222, W, H, 0.18)                                          # 地面
    sc.poly([(226, 222), (254, 222), (300, H), (180, H)], 0.3)           # 小道
    # 手前の木（左右を覆う）
    for x, w_ in [(10, 26), (60, 14), (410, 18), (455, 30)]:
        sc.rect(x - w_ // 2, 0, x + w_ // 2, H, 0.03)
    for cx, cy, r in [(30, 10, 70), (100, -10, 60), (440, 0, 80), (380, -20, 50)]:
        sc.ellipse(cx - r, cy - r * 0.7, cx + r, cy + r * 0.7, 0.04)
    sc.set(sc.a + 0.12 * np.exp(-((sc.yy - 225) / 25) ** 2))          # 地面近くの霧
    sc.vignette(1.2)
    sc.grain(0.05)
    if red_window:
        sc.red_eye(181, 128)
    sc.save(name, pal)


# =====================================================================
# 洋館の廊下（一点透視）
# =====================================================================

def hall(sc, vy=110, fw=90, fh=70, depth_dark=0.9):
    vx = W // 2
    fx0, fy0, fx1, fy1 = vx - fw // 2, vy - fh // 2, vx + fw // 2, vy + fh // 2
    sc.poly([(0, H), (W, H), (fx1, fy1), (fx0, fy1)], 0.22)              # 床
    sc.poly([(0, 0), (W, 0), (fx1, fy0), (fx0, fy0)], 0.1)               # 天井
    sc.poly([(0, 0), (fx0, fy0), (fx0, fy1), (0, H)], 0.3)               # 左壁
    sc.poly([(W, 0), (fx1, fy0), (fx1, fy1), (W, H)], 0.27)              # 右壁
    sc.rect(fx0, fy0, fx1, fy1, 0.0)

    def wp(side, t, v):
        k = t ** 0.6
        xn = 0 if side < 0 else W
        xf = fx0 if side < 0 else fx1
        x = xn + (xf - xn) * k
        top, bot = fy0 * k, H + (fy1 - H) * k
        return (x, top + (bot - top) * v)

    for side in (-1, 1):
        for j in range(18):                                              # 壁紙の縦縞
            t = j / 18
            sc.line([wp(side, t, 0.05), wp(side, t, 0.62)], 0.24 if side < 0 else 0.22)
        sc.poly([wp(side, 0, 0.62), wp(side, 1, 0.62), wp(side, 1, 1), wp(side, 0, 1)], 0.18)   # 腰板
        sc.line([wp(side, 0, 0.62), wp(side, 1, 0.62)], 0.34)
        for j in range(3):                                               # 扉
            t0 = 0.12 + j * 0.3
            t1 = t0 + 0.12
            sc.poly([wp(side, t0, 0.2), wp(side, t1, 0.2), wp(side, t1, 1), wp(side, t0, 1)], 0.1, outline=0.2)
        for j in range(3):                                               # 額縁
            t0 = 0.3 + j * 0.3
            sc.poly([wp(side, t0, 0.2), wp(side, t0 + 0.05, 0.2), wp(side, t0 + 0.05, 0.45), wp(side, t0, 0.45)], 0.12, outline=0.3)
    for i in range(-8, 9):                                               # 床板
        sc.line([(vx + i * 40, H), (vx + i * fw / 16, fy1)], 0.18)
    sc.line([(vx - 24, H), (fx0 + 30, fy1)], 0.3); sc.line([(vx + 24, H), (fx1 - 30, fy1)], 0.3)   # 絨毯の縁
    sc.poly([(vx - 24, H), (vx + 24, H), (fx1 - 30, fy1), (fx0 + 30, fy1)], 0.15)
    d = np.clip(1 - np.maximum(np.abs(sc.xx - vx) / (W / 2), np.abs(sc.yy - vy) / (H / 2)), 0, 1)
    sc.mul(1 - depth_dark * d ** 1.5)
    return (fx0, fy0, fx1, fy1), wp


def hall_height_at(y_floor, vy=110, fh=70):
    """床の y 座標から、その奥行きでの天井までの高さを返す"""
    k = (H - y_floor) / (H - (vy + fh / 2))
    top = (vy - fh / 2) * k
    return y_floor - top


# =====================================================================
# 各場面
# =====================================================================

def mother_feet():
    """青白い素足と白い着物の裾（床すれすれ、横から見た一歩）"""
    sc = Scene(0.0, seed=31)
    sc.rect(0, 0, W, 205, 0.12)                                           # 奥の壁（腰板）
    for x in range(0, W, 30):
        sc.line([(x, 120), (x, 205)], 0.09)
    sc.line([(0, 120), (W, 120)], 0.2)
    sc.set(sc.a + sc.grad_y(205, H, 0.0, 0.0))
    sc.rect(0, 205, W, H, 0.24)                                           # 床板
    for y in (214, 226, 242, 262):
        sc.line([(0, y), (W, y)], 0.17)
    # 着物の裾（右から左へ歩いている）
    k = mask_of(lambda d: d.polygon([(150, -5), (430, -5), (440, 200), (380, 206), (300, 198), (210, 204), (140, 196)], fill=255))
    sc.figure(k, fill=0.78, rim=0.92, shade=1 - 0.45 * np.clip((sc.yy) / 210, 0, 1) * np.clip((sc.xx - 140) / 300, 0.3, 1))
    a = sc.a
    for x in range(160, 430, 11):                                         # 裾のしわ
        a[0:200, x] *= 0.82
        a[0:200, x + 1] *= 0.9
    sc.set(a)
    # 前に出した足（かかとから指先まで）
    f1 = mask_of(lambda d: d.polygon([(232, 196), (262, 196), (266, 228), (250, 240), (206, 242), (176, 246),
                                      (170, 240), (196, 230), (226, 222)], fill=255))
    sc.figure(f1, fill=0.86, rim=0.97, shade=1 - 0.3 * np.clip((sc.yy - 196) / 50, 0, 1))
    # 後ろの足（かかとが上がり、つま先で床を押す）
    f2 = mask_of(lambda d: d.polygon([(346, 198), (372, 198), (378, 214), (360, 232), (336, 246), (318, 246),
                                      (322, 238), (340, 226)], fill=255))
    sc.figure(f2, fill=0.8, rim=0.92, shade=1 - 0.3 * np.clip((sc.yy - 198) / 50, 0, 1))
    for (x0, y0) in ((176, 246), (318, 246)):                             # 指の境目
        for t in range(1, 4):
            sc.line([(x0 + t * 5, y0 - 4), (x0 + t * 5, y0)], 0.55)
    sc.line([(214, 226), (244, 214)], 0.62)                               # くるぶしと腱の影
    # 床まで届く髪の先
    for x in range(380, 470, 3):
        if sc.rnd.random() < 0.6:
            sc.line([(x, 130), (x + sc.rnd.randint(4, 12), 250 + sc.rnd.randint(0, 12))], 0.02)
    sc.light(250, 230, 220, 80, 0.8)
    sc.vignette(1.3, floor=0.15)
    sc.grain(0.04)
    sc.save("oka_feet", PAL_COLD)


def mother_hall():
    """天井に頭がつきそうな母が廊下を歩いてくる"""
    sc = Scene(0.0, seed=41)
    hall(sc)
    foot = 205
    h = hall_height_at(foot) * 1.0
    m = mother_masks(240, foot, h, view="front", hair_len=0.62, step=4)
    sc.light(240, 30, 160, 140, 0.8)
    draw_mother(sc, m, kimono_v=0.7)
    sc.vignette(1.1)
    sc.grain(0.05)
    sc.save("oka_hall_mother", PAL_COLD)


def mother_drag():
    """床まで届く髪の母が、男女二人を引きずって廊下の奥へ"""
    sc = Scene(0.0, seed=51)
    hall(sc)
    foot = 200
    h = hall_height_at(foot) * 0.95
    m = mother_masks(240, foot, h, view="back", hair_len=1.02)
    sc.light(240, 200, 200, 90, 1.2)
    # 引きずられる二人（頭が母の足元、脚がこちら側）
    for side, (hx, hy), (fx, fy) in [(-1, (222, 204), (140, 262)), (1, (260, 206), (350, 266))]:
        b = mask_of(lambda d, hx=hx, hy=hy, fx=fx, fy=fy: (
            d.line([(hx, hy), (fx, fy)], fill=255, width=16),
            d.ellipse([hx - 7, hy - 6, hx + 7, hy + 6], fill=255),
            d.line([(fx, fy), (fx + side * 14, fy + 8)], fill=255, width=9)))
        sc.figure(b, fill=0.05, rim=0.4)
    sc.line([(217, 202), (226, 202)], 0.85)                                # サングラスの反射
    # 床に引きずられたスマートフォンの光
    sc.glow(170, 236, 22, 12, 0.35)
    sc.rect(166, 232, 176, 240, 0.95)
    draw_mother(sc, m, kimono_v=0.66, light_from=1)
    sc.ad.line([(140, 262), (222, 206)], fill=(92, 18, 18, 255))           # 床に残る跡
    sc.vignette(1.2)
    sc.grain(0.05)
    sc.save("oka_drag", PAL_COLD)


def kitchen_base(sc):
    sc.set(sc.grad_y(0, H, 0.2, 0.12))
    sc.rect(150, 30, 330, 110, 0.12, outline=0.3)                         # 小窓
    sc.line([(240, 30), (240, 110)], 0.3); sc.line([(150, 70), (330, 70)], 0.3)
    sc.glow(240, 70, 90, 50, 0.18)
    for x, l in [(60, 60), (95, 45), (380, 55), (420, 70)]:                # 吊るされた鍋や道具
        sc.line([(x, 0), (x, l)], 0.08)
        sc.ellipse(x - 10, l, x + 10, l + 14, 0.08)
    sc.rect(0, 200, W, 214, 0.32)                                         # 調理台
    sc.rect(0, 214, W, H, 0.1)
    for x in range(0, W, 60):
        sc.line([(x, 214), (x, H)], 0.05)


def mother_chop(name, phase):
    """後ろ姿で包丁を振るう母（腰から上）。phase: down / up / turn90 / turn180"""
    sc = Scene(0.0, seed=61)
    kitchen_base(sc)
    sc.gain(1.6)
    sc.light(240, 60, 220, 140, 0.6)
    cx, hy, hr = 228, 62, 30
    raised = phase != "down"
    # 白い着物の肩と背中
    body = mask_of(lambda d: d.polygon([(cx - 100, 128), (cx + 100, 128), (cx + 112, H), (cx - 112, H)], fill=255))
    sc.figure(body, fill=0.68, rim=0.85, shade=1 - 0.35 * np.clip((sc.xx - (cx - 110)) / 220, 0, 1))
    a = sc.a
    for x in range(cx - 100, cx + 110, 8):                                # 背中のしわ
        a[150:H, x] *= 0.85
    sc.set(a)
    # 左の袂
    sl = mask_of(lambda d: d.polygon([(cx - 100, 130), (cx - 128, 150), (cx - 140, H), (cx - 98, H)], fill=255))
    sc.figure(sl, fill=0.6, rim=0.8)
    # 右腕：振り上げる／前へ下ろす
    if raised:
        arm = mask_of(lambda d: (d.line([(cx + 92, 140), (cx + 128, 70), (cx + 138, 34)], fill=255, width=24),
                                 d.polygon([(cx + 120, 70), (cx + 150, 60), (cx + 160, 150), (cx + 132, 160)], fill=255)))
        sc.figure(arm, fill=0.62, rim=0.82)
        hand = mask_of(lambda d: d.ellipse([cx + 130, 18, cx + 148, 40], fill=255))
        sc.figure(hand, fill=0.85, rim=0.95)
        sc.poly([(cx + 135, 20), (cx + 143, 20), (cx + 141, -20), (cx + 134, -12)], 0.97)   # 刃
        sc.ad.line([(cx + 139, -16), (cx + 140, 14)], fill=RED_DARK, width=2)
    else:
        arm = mask_of(lambda d: d.polygon([(cx + 90, 132), (cx + 118, 140), (cx + 112, 210), (cx + 86, 205)], fill=255))
        sc.figure(arm, fill=0.62, rim=0.82)
    # 床まで流れる黒髪（背中を覆う）
    hair = mask_of(lambda d: (d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=255),
                              d.polygon([(cx - hr, hy), (cx + hr, hy), (cx + 52, H), (cx - 52, H)], fill=255)))
    face = None
    if phase == "turn90":
        face = mask_of(lambda d: d.polygon([(cx + 14, hy - 22), (cx + 40, hy - 8), (cx + 46, hy + 6), (cx + 38, hy + 10),
                                             (cx + 40, hy + 22), (cx + 14, hy + 30)], fill=255))
    if phase == "turn180":
        face = mask_of(lambda d: d.ellipse([cx - 22, hy - 20, cx + 22, hy + 30], fill=255))
    hm = hair if face is None else (hair & ~face)
    sc.figure(hm, fill=0.02, rim=0.24)
    a = sc.a
    for x in range(cx - 50, cx + 52, 3):                                  # 毛筋
        a[hy + 20:H, x] = np.minimum(a[hy + 20:H, x] + 0.02, 0.06) * hm[hy + 20:H, x] + a[hy + 20:H, x] * ~hm[hy + 20:H, x]
    sc.set(a)
    if face is not None:
        sc.figure(face, fill=0.8, rim=0.92)
        for x in range(cx - 22, cx + 46, 2):                              # 顔にかかる前髪
            if face[:, x].any():
                top = np.where(face[:, x])[0].min()
                sc.line([(x, top - 1), (x, top + 4 + (x * 7) % 9)], 0.02)
        if phase == "turn90":
            sc.red_eye(cx + 30, hy - 2)
        else:
            sc.red_eye(cx - 12, hy + 2)
            sc.red_eye(cx + 9, hy + 2)
            sc.line([(cx - 12, hy + 18), (cx, hy + 22), (cx + 13, hy + 17)], 0.05)    # 口元
    # 血しぶき（振り下ろした直後は多く、止まったあとは壁に残ったものだけ）
    sc.splatter(cx + 130, 175, 80 if phase == "down" else 30, 55, seed=3, dirs=(-math.pi * 0.95, -math.pi * 0.05))
    sc.splatter(cx + 160, 110, 30, 45, seed=4)
    sc.vignette(1.1)
    sc.grain(0.05)
    sc.save(name, PAL_COLD)


def window_lights():
    """暗い部屋の窓の外に、いくつもの懐中電灯"""
    sc = Scene(0.03, seed=71)
    sc.rect(130, 20, 350, 240, 0.14)                                      # 窓の外（夜の森）
    for i in range(16):
        x = 130 + i * 14 + sc.rnd.randint(-3, 3)
        sc.poly([(x - 10, 240), (x, 60 + sc.rnd.randint(-20, 30)), (x + 10, 240)], 0.06)
    for (x, y, r) in [(180, 190, 6), (226, 176, 5), (300, 196, 7), (268, 182, 4)]:   # 懐中電灯
        sc.glow(x, y, r * 4, r * 3, 0.45)
        sc.ellipse(x - r / 2, y - r / 2, x + r / 2, y + r / 2, 1.0)
    a = sc.a
    beam = np.zeros_like(a)
    for (x, y, tx, ty) in [(180, 190, 160, 60), (300, 196, 330, 70)]:
        for t in np.linspace(0, 1, 60):
            px, py = x + (tx - x) * t, y + (ty - y) * t
            beam += 0.012 * np.exp(-(((sc.xx - px) / (4 + 20 * t)) ** 2 + ((sc.yy - py) / 6) ** 2))
    sc.set(a + beam)
    # 窓枠
    for x in (130, 203, 276, 350):
        sc.rect(x - 4, 16, x + 4, 244, 0.1)
    for y in (16, 128, 244):
        sc.rect(126, y - 4, 354, y + 4, 0.1)
    sc.line([(126, 12), (354, 12)], 0.25)
    # 破れたカーテン
    sc.poly([(60, 0), (138, 0), (128, 190), (110, 230), (92, 200), (70, 260), (60, 270)], 0.07)
    sc.poly([(342, 0), (420, 0), (420, 270), (400, 240), (380, 268), (356, 150)], 0.07)
    sc.rect(0, 0, 60, H, 0.03); sc.rect(420, 0, W, H, 0.03)
    sc.vignette(1.3)
    sc.grain(0.05)
    sc.save("oka_window", PAL_COLD)


def men_outside():
    """夜の洋館を指差し、スマートフォンで撮影して笑う男二人"""
    sc = Scene(0.0, seed=81)
    sc.set(sc.grad_y(0, 160, 0.3, 0.16))
    sc.glow(420, 30, 40, 40, 0.5)                                         # 月
    sc.rect(150, 60, 380, 175, 0.05)                                      # 洋館の影
    sc.poly([(140, 62), (265, 18), (390, 62)], 0.04)
    for x, y in [(170, 80), (210, 80), (310, 80), (350, 80), (170, 120), (350, 120)]:
        sc.rect(x, y, x + 14, y + 22, 0.02, outline=0.09)
    sc.rect(0, 175, W, H, 0.1)                                            # 地面の草
    for x in range(0, W, 3):
        sc.line([(x, 175 + sc.rnd.randint(0, 6)), (x + sc.rnd.randint(-2, 2), 168 + sc.rnd.randint(0, 8))], 0.08)
    # 懐中電灯の光が洋館を照らす
    a = sc.a
    for t in np.linspace(0, 1, 80):
        px, py = 360 + (300 - 360) * t, 200 + (100 - 200) * t
        a += 0.02 * np.exp(-(((sc.xx - px) / (3 + 26 * t)) ** 2 + ((sc.yy - py) / (3 + 26 * t)) ** 2))
    sc.set(a)
    sc.glow(300, 100, 30, 26, 0.3)
    m1 = mask_of(lambda d: man(d, 120, 268, 170, arm=(200, 120)))
    m2 = mask_of(lambda d: man(d, 360, 270, 160, arm=(330, 160), phone=True))
    sc.figure(m1, fill=0.04, rim=0.42)
    sc.figure(m2, fill=0.04, rim=0.42)
    sc.glow(328, 156, 16, 14, 0.4)                                        # スマートフォンの画面
    sc.rect(322, 148, 333, 164, 0.95)
    sc.glow(362, 200, 10, 8, 0.6)                                         # 懐中電灯
    sc.vignette(1.2)
    sc.grain(0.05)
    sc.red_eye(214, 88)                                                   # 二階の窓にだけ、赤い目
    sc.save("oka_men", PAL_COLD)


def lunge(name, far=False):
    """暗闇から一瞬で迫る母（far=True は遠くに立つ姿）"""
    sc = Scene(0.02, seed=91)
    for i in range(30):                                                   # 夜の森
        x = i * 17 + sc.rnd.randint(-5, 5)
        sc.rect(x, 0, x + sc.rnd.randint(3, 8), H, 0.05 + sc.rnd.random() * 0.04)
    sc.set(sc.a + sc.grad_y(150, H, 0.0, 0.05))
    if far:
        m = mother_masks(250, 190, 120, view="front", hair_len=0.7)
        sc.light(250, 150, 60, 60, 2.0)
        draw_mother(sc, m, kimono_v=0.55)
        sc.vignette(1.5, floor=0.1)
        sc.grain(0.06)
        sc.save(name, PAL_COLD)
        return
    # 画面いっぱいに迫る：長い腕が四隅へ、包丁、見開いた赤い目
    body = mask_of(lambda d: d.polygon([(170, 120), (310, 120), (360, H), (120, H)], fill=255))
    sc.figure(body, fill=0.6, rim=0.8, shade=1 - 0.5 * np.clip((sc.yy - 120) / 150, 0, 1))
    arms = mask_of(lambda d: (d.line([(180, 140), (60, 60), (-10, 20)], fill=255, width=14),
                              d.line([(300, 140), (420, 70), (490, 30)], fill=255, width=14)))
    sc.figure(arms, fill=0.55, rim=0.75)
    hands = mask_of(lambda d: [d.line([(x0, y0), (x0 + dx, y0 + dy)], fill=255, width=3)
                               for (x0, y0) in ((10, 25), (470, 35))
                               for (dx, dy) in ((-20, -12), (-24, 0), (-18, 14), (20, -14), (24, 4))])
    sc.figure(hands, fill=0.85, rim=0.95)
    legs = mask_of(lambda d: (d.line([(160, H), (40, 200), (0, 270)], fill=255, width=12),
                              d.line([(320, H), (440, 210), (480, 270)], fill=255, width=12)))
    sc.figure(legs, fill=0.08, rim=0.3)
    hair = mask_of(lambda d: (d.ellipse([180, 20, 300, 140], fill=255),
                              [d.line([(240, 60), (240 + dx, 60 + abs(dx) * 0.4 + 120)], fill=255, width=6)
                               for dx in range(-150, 151, 12)]))
    sc.figure(hair, fill=0.02, rim=0.2)
    face = mask_of(lambda d: d.ellipse([206, 52, 274, 130], fill=255))
    sc.figure(face, fill=0.8, rim=0.9)
    for x in range(206, 275, 3):                                          # 顔にかかる髪
        sc.line([(x, 50), (x + sc.rnd.randint(-4, 4), 60 + sc.rnd.randint(0, 30))], 0.02)
    sc.poly([(330, 30), (345, 28), (300, 140), (292, 136)], 0.97)          # 包丁
    sc.ad.ellipse([218, 84, 232, 94], fill=RED)                            # 見開いた目
    sc.ad.ellipse([248, 84, 262, 94], fill=RED)
    sc.ad.ellipse([223, 87, 227, 91], fill=(20, 4, 4, 255))
    sc.ad.ellipse([253, 87, 257, 91], fill=(20, 4, 4, 255))
    pts_top = [(208 + i * 4, 110 + 0.045 * (i * 4 - 32) ** 2 * -0.25 + 6) for i in range(17)]
    pts_bot = [(x, y + 3 + 4 * math.sin(math.pi * (x - 208) / 64)) for (x, y) in pts_top][::-1]
    sc.poly(pts_top + pts_bot, 0.02)                                      # 耳まで裂けた笑み
    for (x, y) in pts_top[2:-2:2]:
        sc.line([(x, y + 1), (x, y + 3)], 0.7)                            # 歯
    sc.vignette(1.0, floor=0.25)
    sc.grain(0.06)
    sc.save(name, PAL_COLD)


def entrance():
    """玄関ホール：二人を引きずって入ってくる母と、柱時計"""
    sc = Scene(0.0, seed=101)
    sc.rect(0, 0, W, 190, 0.26)                                           # 奥の壁
    sc.rect(0, 190, W, H, 0.2)                                            # 床（市松）
    for i in range(-10, 11):
        sc.line([(240 + i * 50, H), (240 + i * 26, 190)], 0.14)
    for y in (204, 222, 246):
        sc.line([(0, y), (W, y)], 0.14)
    sc.rect(170, 40, 310, 190, 0.05, outline=0.3)                         # 開いた扉
    sc.rect(176, 46, 304, 190, 0.62)                                      # 外の光（曇りの午後）
    for i in range(10):
        x = 176 + i * 13
        sc.rect(x, 90 + sc.rnd.randint(0, 30), x + 6, 190, 0.35)          # 外の木々
    sc.poly([(170, 40), (130, 30), (130, 200), (170, 190)], 0.12)          # 開いた扉板
    sc.poly([(310, 40), (350, 30), (350, 200), (310, 190)], 0.12)
    sc.poly([(176, 190), (304, 190), (370, H), (110, H)], 0.42)            # 床に差し込む光
    # 柱時計（右）
    sc.rect(392, 30, 440, 250, 0.1, outline=0.24)
    sc.ellipse(398, 40, 434, 76, 0.55)
    sc.line([(416, 58), (424, 61)], 0.1); sc.line([(416, 58), (402, 58)], 0.1)
    sc.rect(404, 96, 428, 200, 0.06, outline=0.2)
    sc.ellipse(410, 170, 422, 182, 0.4); sc.line([(416, 100), (416, 172)], 0.3)
    # 逆光の母と、引きずられる二人
    m = mother_masks(240, 205, 190, view="front", hair_len=0.95)
    for (hx, hy, fx, fy) in [(214, 140, 186, 190), (268, 140, 300, 190)]:
        b = mask_of(lambda d, hx=hx, hy=hy, fx=fx, fy=fy: (d.line([(hx, hy), (fx, fy)], fill=255, width=13),
                                                            d.ellipse([hx - 7, hy - 6, hx + 7, hy + 6], fill=255),
                                                            d.line([(fx, fy), (fx + (fx - 240) * 0.3, fy + 4)], fill=255, width=8)))
        sc.figure(b, fill=0.04, rim=0.5)
    draw_mother(sc, m, kimono_v=0.35, skin_v=0.45)                         # 逆光なので暗め
    sc.vignette(1.1)
    sc.grain(0.05)
    sc.save("oka_entrance", PAL_COLD)


def clock_face():
    """柱時計のアップ：15時45分"""
    sc = Scene(0.08, seed=111)
    sc.rect(110, 0, 370, H, 0.14)                                         # 木の箱
    for x in range(110, 370, 7):
        sc.line([(x, 0), (x + 2, H)], 0.11)
    sc.ellipse(150, 20, 330, 200, 0.2)
    sc.ellipse(158, 28, 322, 192, 0.66)                                   # 文字盤
    cx, cy, r = 240, 110, 78
    for i in range(12):
        ang = math.radians(i * 30 - 90)
        l = 12 if i % 3 == 0 else 7
        sc.line([(cx + math.cos(ang) * (r - l), cy + math.sin(ang) * (r - l)),
                 (cx + math.cos(ang) * (r - 2), cy + math.sin(ang) * (r - 2))], 0.12, width=2 if i % 3 == 0 else 1)
    for i in range(60):
        ang = math.radians(i * 6 - 90)
        sc.d.point((cx + math.cos(ang) * (r - 3), cy + math.sin(ang) * (r - 3)), fill=0.3)
    ah = math.radians((3 + 45 / 60) * 30 - 90)                            # 短針（3時45分）
    am = math.radians(45 * 6 - 90)                                        # 長針（45分）
    sc.line([(cx, cy), (cx + math.cos(ah) * 42, cy + math.sin(ah) * 42)], 0.05, width=4)
    sc.line([(cx, cy), (cx + math.cos(am) * 66, cy + math.sin(am) * 66)], 0.05, width=2)
    sc.ellipse(cx - 4, cy - 4, cx + 4, cy + 4, 0.05)
    sc.rect(190, 214, 290, H, 0.06, outline=0.24)                         # 振り子の窓
    sc.line([(240, 214), (236, 262)], 0.3); sc.ellipse(226, 250, 246, 270, 0.4)
    sc.light(200, 80, 160, 140, 0.7)
    sc.vignette(1.3, floor=0.2)
    sc.grain(0.04)
    # 文字盤の縁に、赤い指の跡
    for i, (x, y) in enumerate([(318, 120), (322, 128), (321, 137), (316, 145)]):
        sc.ad.line([(x, y), (x + 5, y + 3)], fill=RED_DARK, width=2)
    sc.save("oka_clock", PAL_COLD)


def dining():
    """夕食：赤いスープ、サラダ、きれいに切られた肉、ご飯。向かいで微笑む母"""
    sc = Scene(0.0, seed=121)
    sc.set(sc.grad_y(0, 170, 0.3, 0.2))
    sc.rect(300, 30, 400, 120, 0.5, outline=0.18)                         # 夕焼けの窓
    sc.line([(350, 30), (350, 120)], 0.18); sc.line([(300, 75), (400, 75)], 0.18)
    sc.glow(240, 10, 60, 40, 0.5)                                         # ランプ
    sc.line([(240, 0), (240, 14)], 0.1); sc.poly([(225, 14), (255, 14), (248, 24), (232, 24)], 0.85)
    # 母（向かいに座る）
    m = mother_masks(240, 260, 210, view="front", hair_len=0.6)
    draw_mother(sc, m, kimono_v=0.7, smile=True)
    hy, hr = m["hy"], m["hr"]
    face = mask_of(lambda d: d.ellipse([240 - hr * 0.6, hy - hr * 0.3, 240 + hr * 0.6, hy + hr * 0.95], fill=255))
    sc.figure(face, fill=0.82, rim=0.9)
    sc.line([(240 - hr * 0.5, hy + hr * 0.15), (240 - hr * 0.3, hy + hr * 0.05), (240 - hr * 0.1, hy + hr * 0.15)], 0.15)  # 細めた目
    sc.line([(240 + hr * 0.1, hy + hr * 0.15), (240 + hr * 0.3, hy + hr * 0.05), (240 + hr * 0.5, hy + hr * 0.15)], 0.15)
    sc.line([(240 - hr * 0.2, hy + hr * 0.6), (240, hy + hr * 0.68), (240 + hr * 0.2, hy + hr * 0.6)], 0.3)
    for x in range(int(240 - hr * 1.0), int(240 + hr * 1.0), 2):          # 前髪
        if abs(x - 240) > hr * 0.6:
            sc.line([(x, hy - hr), (x, hy + hr * 1.2)], 0.02)
        else:
            sc.line([(x, hy - hr), (x, hy - hr * 0.3 + (x % 3))], 0.02)
    # テーブル
    sc.poly([(60, 168), (420, 168), (480, H), (0, H)], 0.5)
    sc.line([(60, 168), (420, 168)], 0.7)
    sc.ellipse(110, 196, 190, 226, 0.85); sc.ellipse(118, 200, 182, 220, 0.3)      # スープ皿
    sc.ad.ellipse([120, 202, 180, 218], fill=(150, 24, 22, 255))
    sc.ad.ellipse([132, 205, 150, 210], fill=(186, 40, 32, 255))
    sc.ellipse(200, 180, 260, 204, 0.8)                                            # サラダ
    for i in range(18):
        x = 208 + sc.rnd.randint(0, 44); y = 182 + sc.rnd.randint(0, 12)
        sc.ellipse(x - 3, y - 2, x + 3, y + 2, sc.rnd.choice([0.35, 0.45, 0.55]))
    sc.ellipse(270, 196, 370, 232, 0.88)                                           # 肉の皿
    for i in range(5):
        x = 286 + i * 15
        sc.poly([(x, 204), (x + 12, 204), (x + 10, 224), (x - 2, 224)], 0.6)
        sc.ad.line([(x + 1, 205), (x + 11, 205)], fill=(150, 40, 36, 255))
    sc.ellipse(380, 186, 420, 208, 0.9)                                            # ご飯
    sc.ellipse(384, 182, 416, 198, 0.97)
    # 手前に女の子の後ろ頭
    g = mask_of(lambda d: (d.ellipse([60, 196, 150, 290], fill=255), d.rectangle([58, 236, 152, 290], fill=255)))
    sc.figure(g, fill=0.05, rim=0.3)
    sc.light(240, 180, 220, 100, 0.5)
    sc.vignette(1.1)
    sc.grain(0.04)
    sc.save("oka_dining", PAL_DUSK)


def under_table():
    """テーブルの下：新聞にくるまれた腕と脚が、バケツに縦に入っている"""
    sc = Scene(0.0, seed=131)
    sc.rect(0, 0, W, 40, 0.1)                                             # テーブルの裏
    sc.rect(0, 40, W, 190, 0.16)                                          # 奥の壁
    sc.rect(0, 190, W, H, 0.3)                                            # 床
    for i in range(-10, 11):
        sc.line([(240 + i * 50, H), (240 + i * 30, 190)], 0.24)
    for x in (40, 440):
        sc.rect(x - 8, 40, x + 8, 250, 0.08)                              # テーブルの脚
    # 女の子のぶらぶらした脚（左）と、母の着物の裾（右）
    for lx, ly in [(110, 150), (138, 156)]:
        g = mask_of(lambda d, lx=lx, ly=ly: (d.rectangle([lx - 6, 40, lx + 6, ly], fill=255),
                                              d.ellipse([lx - 9, ly - 6, lx + 10, ly + 6], fill=255)))
        sc.figure(g, fill=0.06, rim=0.3)
        sc.rect(lx - 6, ly - 22, lx + 6, ly - 6, 0.85)                    # 白い靴下
    k = mask_of(lambda d: d.polygon([(340, 40), (430, 40), (440, 240), (330, 240)], fill=255))
    sc.figure(k, fill=0.7, rim=0.85, shade=1 - 0.4 * np.clip((sc.xx - 330) / 110, 0, 1))
    # バケツ
    sc.poly([(196, 170), (284, 170), (274, 250), (206, 250)], 0.45)
    sc.ellipse(196, 162, 284, 178, 0.6)
    sc.ellipse(204, 166, 276, 176, 0.08)
    for y in (190, 230):
        sc.line([(199, y), (281, y)], 0.35)
    # 新聞の包み（縦に二本）
    for (x0, top, w_) in [(214, 96, 26), (242, 110, 24)]:
        sc.poly([(x0, 172), (x0 + w_, 172), (x0 + w_ - 3, top), (x0 + 3, top + 6)], 0.72)
        for y in range(top + 8, 170, 5):
            sc.line([(x0 + 4, y), (x0 + w_ - 5, y)], 0.55)
        sc.ad.line([(x0 + 4, top + 30), (x0 + 10, top + 44)], fill=RED_DARK, width=3)
    # 片方から、青白い指がのぞく
    for i in range(4):
        fx = 220 + i * 5
        sc.line([(fx, 98), (fx + (i - 1.5), 84 - (i % 2) * 3)], 0.88, width=2)
    sc.light(240, 160, 140, 100, 0.9)
    sc.vignette(1.2)
    sc.grain(0.05)
    sc.save("oka_under", PAL_DUSK)


def all_scenes():
    classroom("oka_class_read", "down")
    classroom("oka_class_clap1", "apart")
    classroom("oka_class_clap2", "together")
    mansion_ext("oka_mansion_day", PAL_COLD, sky=(0.62, 0.4))
    mansion_ext("oka_mansion_dusk", PAL_DUSK, sky=(0.85, 0.45), lit_windows=(1, 4, 8))
    mother_feet()
    mother_hall()
    mother_drag()
    for p in ("down", "up", "turn90", "turn180"):
        mother_chop(f"oka_chop_{p}", p)
    window_lights()
    men_outside()
    lunge("oka_lunge_far", far=True)
    lunge("oka_lunge")
    entrance()
    clock_face()
    dining()
    under_table()


NAMES = ["oka_class_read", "oka_class_clap1", "oka_class_clap2", "oka_mansion_day", "oka_mansion_dusk", "oka_feet",
         "oka_hall_mother", "oka_drag", "oka_chop_down", "oka_chop_up", "oka_chop_turn90", "oka_chop_turn180",
         "oka_window", "oka_men", "oka_lunge_far", "oka_lunge", "oka_entrance", "oka_clock", "oka_dining", "oka_under"]


def sheet(names, out, cols=2):
    rows = (len(names) + cols - 1) // cols
    s = Image.new("RGB", (W * cols, H * rows), (40, 0, 40))
    for i, n in enumerate(names):
        s.paste(Image.open(os.path.join(BG_DIR, n + ".png")), ((i % cols) * W, (i // cols) * H))
    s.save(out)


if __name__ == "__main__":
    all_scenes()
    if len(sys.argv) > 2 and sys.argv[1] == "sheet":
        out = sys.argv[2]
        for k in range(0, len(NAMES), 4):
            sheet(NAMES[k:k + 4], f"{out}_{k // 4}.png")
    print("done")
