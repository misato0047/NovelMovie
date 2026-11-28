"""絵コンテのテンプレート（Krita で開ける .ora、1ページ5コマ）を作る

使い方:
  python tools/conte/make_conte.py scenario/台本.txt   台本の「#=」行から場面名入りで作る
  python tools/conte/make_conte.py --blank 10          場面名なしで10コマ分作る

台本での場面の書き方（再生には影響しないコメント行）:
  #= 1 廊下を歩いてくる母
  #= 2 二人を引きずる母 | 何をつかんでいるか（任意のメモ）

出力: conte/台本名_p1.ora, _p2.ora ...（レイヤー：メモ／ラフ／テンプレート）
"""
import io
import os
import sys
import zipfile

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONTS = ["C:/Windows/Fonts/YuGothM.ttc", "C:/Windows/Fonts/meiryo.ttc", "C:/Windows/Fonts/msgothic.ttc",
         "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc", "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"]
W, H = 2480, 3508          # A4縦・300dpi
ROWS = 5


def font(size):
    for f in FONTS:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def read_scenes(path):
    scenes = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("#="):
            body = line[2:].strip()
            memo = ""
            if "|" in body:
                body, memo = [x.strip() for x in body.split("|", 1)]
            no, _, title = body.partition(" ")
            scenes.append((no, title.strip(), memo))
    return scenes


def page(scenes, title, pno, pcount):
    im = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(im)
    M, head = 110, 230
    rh = (H - M * 2 - head) // ROWS
    fh = rh - 70
    fw = fh * 16 // 9
    fx = M + 150
    mx = fx + fw + 40
    mw = W - M - mx
    DARK, GRAY, LIGHT, BLUE = (40, 40, 40), (150, 150, 150), (215, 215, 215), (90, 130, 200)
    d.text((M, M), f"絵コンテ　{title}", font=font(64), fill=DARK)
    d.text((W - M, M + 14), f"p.{pno} / {pcount}", font=font(44), fill=GRAY, anchor="ra")
    d.text((M, M + 92), "枠の中に描く（16:9）。青い点線より下はテキスト枠が重なるので、大事なものは上に。"
                        "　描くのは「ラフ」レイヤー、文字は「メモ」レイヤーへ。", font=font(30), fill=GRAY)
    for i, (no, name, memo) in enumerate(scenes):
        y = M + head + i * rh
        d.text((M, y + 10), no, font=font(90), fill=DARK)
        d.rectangle([fx, y, fx + fw, y + fh], outline=DARK, width=5)
        for t in (1, 2):
            d.line([(fx + fw * t // 3, y), (fx + fw * t // 3, y + fh)], fill=LIGHT, width=2)
            d.line([(fx, y + fh * t // 3), (fx + fw, y + fh * t // 3)], fill=LIGHT, width=2)
        ty = y + int(fh * 0.70)
        for x in range(fx + 6, fx + fw - 6, 24):
            d.line([(x, ty), (x + 12, ty)], fill=BLUE, width=3)
        d.text((fx + fw - 12, ty + 8), "テキスト枠", font=font(26), fill=BLUE, anchor="ra")
        d.text((mx, y), name or "（場面名）", font=font(46), fill=DARK if name else LIGHT)
        if memo:
            d.text((mx, y + 66), memo, font=font(28), fill=GRAY)
        for j in range(6):
            ly = y + 150 + j * 62
            if ly < y + fh:
                d.line([(mx, ly), (mx + mw, ly)], fill=LIGHT, width=2)
        d.text((mx, y + fh - 40), "秒数・動き（矢印）・メモ", font=font(24), fill=LIGHT)
    return im


def png_bytes(img):
    b = io.BytesIO()
    img.save(b, "PNG")
    return b.getvalue()


def save_ora(path, base):
    blank = Image.new("RGBA", base.size, (0, 0, 0, 0))
    stack = f'''<?xml version="1.0" encoding="UTF-8"?>
<image version="0.0.3" w="{base.width}" h="{base.height}" xres="300" yres="300">
 <stack>
  <layer name="メモ" src="data/memo.png" x="0" y="0" opacity="1.0" visibility="visible"/>
  <layer name="ラフ" src="data/rough.png" x="0" y="0" opacity="1.0" visibility="visible"/>
  <layer name="テンプレート（触らない）" src="data/template.png" x="0" y="0" opacity="1.0" visibility="visible" edit-locked="true"/>
 </stack>
</image>'''
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "image/openraster", compress_type=zipfile.ZIP_STORED)
        z.writestr("stack.xml", stack, compress_type=zipfile.ZIP_DEFLATED)
        for n, img in (("data/template.png", base), ("data/rough.png", blank), ("data/memo.png", blank)):
            z.writestr(n, png_bytes(img), compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("mergedimage.png", png_bytes(base), compress_type=zipfile.ZIP_DEFLATED)
        th = base.copy()
        th.thumbnail((256, 256))
        z.writestr("Thumbnails/thumbnail.png", png_bytes(th), compress_type=zipfile.ZIP_DEFLATED)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    if args[0] == "--blank":
        n = int(args[1]) if len(args) > 1 else 5
        scenes = [(str(i + 1), "", "") for i in range(n)]
        name, title = "conte_blank", ""
    else:
        scenes = read_scenes(args[0])
        name = os.path.splitext(os.path.basename(args[0]))[0]
        title = f"「{name}」"
        if not scenes:
            print("台本に「#= 番号 場面名」の行がありません。--blank で空のテンプレートを作れます。")
            return
    out_dir = os.path.join(ROOT, "conte")
    os.makedirs(out_dir, exist_ok=True)
    pages = [scenes[i:i + ROWS] for i in range(0, len(scenes), ROWS)]
    for k, ss in enumerate(pages):
        path = os.path.join(out_dir, f"{name}_p{k + 1}.ora")
        save_ora(path, page(ss, title, k + 1, len(pages)))
        print("作成:", path)


if __name__ == "__main__":
    main()
