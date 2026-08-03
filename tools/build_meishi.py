# -*- coding: utf-8 -*-
"""ラクスル入稿用の名刺 PDF（両面 2 ページ）と QR コードを生成する。

    python tools/build_meishi.py

仕様
- 仕上がり 91 x 55mm、塗り足し 3mm → データサイズ 97 x 61mm
- 350dpi でラスタライズしてから PDF に配置（文字はアウトライン不要）
- 1 ページ目 = 表、2 ページ目 = 裏
"""
import math
from pathlib import Path

import segno
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "meishi"
PHOTOS = ROOT / "photos"

URL = "https://comacoma1130.github.io/"

# 表に載せる写真。印刷用なので、Web 用に圧縮する前の元画像を使う
CARD_PHOTO = Path(r"C:\Users\hm-miyashita\Desktop\宮下\実験\coma\IMG_8351.jpg")
# 円の中心を元画像のどこに置くか(0-1)と、切り出す正方形の大きさ(短辺に対する比率)
CARD_PHOTO_CX, CARD_PHOTO_CY, CARD_PHOTO_ZOOM = 0.469, 0.357, 0.95

# --- 寸法 ---
DPI = 350
TRIM_W, TRIM_H = 91.0, 55.0      # 仕上がり
BLEED = 3.0                       # 塗り足し
DATA_W, DATA_H = TRIM_W + BLEED * 2, TRIM_H + BLEED * 2
SAFE = 3.0                        # 仕上がり線から内側の安全余白


def px(mm_value: float) -> int:
    return int(round(mm_value / 25.4 * DPI))


W, H = px(DATA_W), px(DATA_H)
M = px(BLEED + SAFE)  # データ端から文字を置いてよい位置まで

# --- 色（かわいい系のクリーム＋ブラウン） ---
CREAM = (253, 245, 233)
CREAM_D = (245, 232, 212)
BROWN = (74, 52, 40)
BROWN_L = (139, 110, 92)
ACCENT = (74, 115, 55)        # 唐草の緑
ACCENT_INK = (244, 239, 219)  # 唐草の蔓の色
WHITE = (255, 255, 255)

BAND_MM = 8.0  # 帯の高さ（うち 3mm は塗り足しで切り落とされる）

# --- フォント（丸ゴシック優先） ---
FONT_DIR = Path(r"C:\Windows\Fonts")
JP_ROUND = FONT_DIR / "HGRSMP.TTF"     # HG丸ゴシックM-PRO
JP_BOLD = FONT_DIR / "YuGothB.ttc"
JP_MED = FONT_DIR / "YuGothM.ttc"


def font(path: Path, size_mm: float, index: int = 0) -> ImageFont.FreeTypeFont:
    size = max(1, int(round(size_mm / 25.4 * DPI)))
    try:
        return ImageFont.truetype(str(path), size, index=index)
    except OSError:
        return ImageFont.truetype(str(JP_MED), size, index=0)


def paw(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float, color) -> None:
    """肉球を描く（肉球 + 指 4 つ）。r は肉球全体のおおよその半径。"""
    # 大きい肉球（下側）
    d.ellipse([cx - r * 0.52, cy - r * 0.18, cx + r * 0.52, cy + r * 0.82], fill=color)
    # 指（上側に 4 つ、外側ほど下がる）
    toes = [(-0.66, -0.52, 0.23, 0.28), (-0.23, -0.86, 0.24, 0.30),
            (0.23, -0.86, 0.24, 0.30), (0.66, -0.52, 0.23, 0.28)]
    for tx, ty, rx, ry in toes:
        d.ellipse(
            [cx + (tx - rx) * r, cy + (ty - ry) * r, cx + (tx + rx) * r, cy + (ty + ry) * r],
            fill=color,
        )


def _spiral(cx: float, cy: float, r0: float, turns: float, start: float,
            direction: int, steps: int = 72, shrink: float = 0.86):
    """渦巻き（唐草のカール）の座標列。"""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        ang = start + direction * turns * 2 * math.pi * t
        r = r0 * (1 - shrink * t)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def _leaf(size: int, color, angle: float) -> Image.Image:
    """唐草の葉（しずく型）を描いて回転させる。"""
    ss = 3
    s = size * ss
    sprite = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(sprite)
    d.ellipse([s * 0.10, s * 0.28, s * 0.95, s * 0.72], fill=color)
    d.polygon([(s * 0.02, s * 0.5), (s * 0.42, s * 0.30), (s * 0.42, s * 0.70)], fill=color)
    return sprite.resize((size, size), Image.LANCZOS).rotate(angle, resample=Image.BICUBIC)


def karakusa_band(w: int, h: int) -> Image.Image:
    """唐草模様の帯を作る（緑地に蔓と葉）。"""
    band = Image.new("RGBA", (w, h), ACCENT + (255,))
    ink = ACCENT_INK + (255,)
    lw = max(2, int(h * 0.085))
    tile = int(h * 2.3)
    cy = h * 0.5
    amp = h * 0.17

    d = ImageDraw.Draw(band)
    for ox in range(-tile, w + tile, tile):
        # 主となる蔓（ゆるやかな波）
        stem = [(ox + tile * t / 40, cy + amp * math.sin(2 * math.pi * (t / 40)))
                for t in range(41)]
        d.line(stem, fill=ink, width=lw, joint="curve")

        # 上に伸びるカール
        d.line(_spiral(ox + tile * 0.24, cy - h * 0.24, h * 0.30, 1.15, math.pi * 0.55, 1),
               fill=ink, width=lw, joint="curve")
        # 下に伸びるカール
        d.line(_spiral(ox + tile * 0.72, cy + h * 0.24, h * 0.27, 1.15, -math.pi * 0.45, -1),
               fill=ink, width=lw, joint="curve")

        # 葉
        for fx, fy, ang, sz in ((0.48, -0.30, 35, 0.34), (0.95, 0.30, -145, 0.30)):
            size = int(h * sz)
            lf = _leaf(size, ink, ang)
            band.alpha_composite(lf, (int(ox + tile * fx - size / 2), int(cy + h * fy - size / 2)))
    return band


def paw_pattern(img: Image.Image, color, step_mm: float = 15.0, r_mm: float = 1.25) -> None:
    """背景にうっすら肉球を散らす。"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    step = px(step_mm)
    r = px(r_mm)
    row = 0
    y = -step // 2
    while y < img.height + step:
        x = -step // 2 + (step // 2 if row % 2 else 0)
        while x < img.width + step:
            paw(d, x, y, r, color + (255,))
            x += step
        y += step
        row += 1
    img.alpha_composite(layer)


def circle_photo(src: Path, size: int, cx: float, cy: float, zoom: float) -> Image.Image:
    """写真を正方形に切り出して円形にする。cx/cy は元画像に対する中心位置(0-1)。"""
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    side = int(min(im.width, im.height) * zoom)
    left = int(im.width * cx - side / 2)
    top = int(im.height * cy - side / 2)
    left = max(0, min(left, im.width - side))
    top = max(0, min(top, im.height - side))
    im = im.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)

    ss = 4
    mask = Image.new("L", (size * ss, size * ss), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size * ss, size * ss], fill=255)
    im.putalpha(mask.resize((size, size), Image.LANCZOS))
    return im


def drop_shadow(base: Image.Image, sprite: Image.Image, x: int, y: int, blur_mm: float = 0.9) -> None:
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", sprite.size, (120, 92, 72, 90))
    sh.putalpha(sprite.getchannel("A").point(lambda v: int(v * 0.42)))
    shadow.paste(sh, (x, y + px(0.6)), sh)
    base.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(px(blur_mm))))
    base.alpha_composite(sprite.convert("RGBA"), (x, y))


def text_center(d, cx, y, s, f, fill, spacing_mm=0.0):
    """中央揃えでテキストを描く（字間指定つき）。戻り値は描画後の下端 y。"""
    sp = px(spacing_mm)
    widths = [d.textlength(ch, font=f) for ch in s]
    total = sum(widths) + sp * (len(s) - 1)
    x = cx - total / 2
    top = y
    for ch, w in zip(s, widths):
        d.text((x, top), ch, font=f, fill=fill)
        x += w + sp
    bbox = f.getbbox(s)
    return top + (bbox[3] - bbox[1]) + bbox[1]


def fit_font(d, text: str, max_mm: float, start_mm: float, path: Path = JP_ROUND):
    """max_mm の幅に収まるまでフォントサイズを少しずつ下げる。"""
    size = start_mm
    while size > 1.0:
        f = font(path, size)
        if d.textlength(text, font=f) <= px(max_mm):
            return f
        size -= 0.1
    return font(path, 1.0)


def draw_bands(img: Image.Image) -> None:
    """上下に唐草模様の帯を敷く。"""
    bh = px(BAND_MM)
    band = karakusa_band(W, bh)
    img.alpha_composite(band, (0, 0))
    img.alpha_composite(band.transpose(Image.FLIP_TOP_BOTTOM), (0, H - bh))


# ============================== 表 ==============================
def build_front() -> Image.Image:
    img = Image.new("RGBA", (W, H), CREAM + (255,))
    paw_pattern(img, CREAM_D)
    draw_bands(img)
    d = ImageDraw.Draw(img)

    # 円形写真（左）
    photo_d = px(31)
    ph = circle_photo(CARD_PHOTO, photo_d, CARD_PHOTO_CX, CARD_PHOTO_CY, CARD_PHOTO_ZOOM)
    ring = Image.new("RGBA", (photo_d + px(2.4), photo_d + px(2.4)), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([0, 0, ring.width - 1, ring.height - 1], fill=WHITE + (255,))
    ring.alpha_composite(ph, (px(1.2), px(1.2)))
    photo_x = M + px(1.5)
    photo_y = (H - ring.height) // 2
    drop_shadow(img, ring, photo_x, photo_y)

    # 右側のテキスト
    tx = photo_x + ring.width + px(6.5)
    f_name = font(JP_ROUND, 11.0)
    f_kana = font(JP_ROUND, 3.0)
    f_sub = font(JP_ROUND, 3.4)

    # 「こまの日常」と「こま」は、実際の字形の下端を測ってから間隔を取る
    kana_y = photo_y + px(2.6)
    d.text((tx, kana_y), "こまの日常", font=f_kana, fill=BROWN_L + (255,))

    name_y = kana_y + f_kana.getbbox("こまの日常")[3] + px(2.4)
    d.text((tx, name_y), "こま", font=f_name, fill=BROWN + (255,))

    line_y = name_y + f_name.getbbox("こま")[3] + px(2.2)
    d.rounded_rectangle(
        [tx, line_y, tx + px(30), line_y + px(0.5)], radius=px(0.25), fill=ACCENT + (255,)
    )

    d.text((tx, line_y + px(2.6)), "なかよくしてね", font=f_sub, fill=BROWN_L + (255,))
    d.text((tx, line_y + px(7.0)), "@coma__days", font=f_sub, fill=BROWN + (255,))
    return img


# ============================== 裏 ==============================
def build_back() -> Image.Image:
    img = Image.new("RGBA", (W, H), CREAM + (255,))
    paw_pattern(img, CREAM_D)
    draw_bands(img)
    d = ImageDraw.Draw(img)

    # QR（右側）
    qr_mm = 25.0
    qr_px = px(qr_mm)
    qr = segno.make(URL, error="m")
    tmp = OUT / "qr-raw.png"
    qr.save(str(tmp), scale=20, border=0, dark="#4a3428", light="#ffffff")
    qr_img = Image.open(tmp).convert("RGBA").resize((qr_px, qr_px), Image.NEAREST)

    pad = px(2.6)
    plate = Image.new("RGBA", (qr_px + pad * 2, qr_px + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle(
        [0, 0, plate.width - 1, plate.height - 1], radius=px(3.0), fill=WHITE + (255,)
    )
    plate.alpha_composite(qr_img, (pad, pad))
    qr_x = W - M - plate.width
    qr_y = (H - plate.height) // 2
    drop_shadow(img, plate, qr_x, qr_y)

    # 左側の案内
    tx = M + px(1.5)
    col_mm = (qr_x - tx) / (DPI / 25.4) - 3.0  # QR までの空き幅
    f_lead = fit_font(d, "お友達になってください！", col_mm, 4.6)
    f_small = font(JP_ROUND, 2.8)

    items = ["Instagram", "TikTok", "LINEスタンプ"]
    block_h = px(6.6) + px(4.4) * len(items)
    top = (H - block_h) // 2

    d.text((tx, top), "お友達になってください！", font=f_lead, fill=BROWN + (255,))

    iy = top + px(6.6)
    for label in items:
        paw(d, tx + px(1.3), iy + px(1.6), px(1.4), ACCENT + (255,))
        d.text((tx + px(3.8), iy), label, font=f_small, fill=BROWN + (255,))
        iy += px(4.4)
    return img


# ============================== 出力 ==============================
def with_guides(img: Image.Image, label: str) -> Image.Image:
    """確認用に 仕上がり線(91x55) と 安全領域(85x49) を重ねた画像を作る。入稿には使わない。"""
    g = img.convert("RGB").copy()
    d = ImageDraw.Draw(g)
    f = font(JP_MED, 2.2)

    trim = px(BLEED)
    d.rectangle([trim, trim, W - trim - 1, H - trim - 1], outline=(220, 60, 60), width=px(0.25))
    safe = px(BLEED + SAFE)
    d.rectangle([safe, safe, W - safe - 1, H - safe - 1], outline=(60, 130, 220), width=px(0.25))
    d.text((px(1.0), px(0.6)), f"{label}  赤=仕上がり(91x55)  青=安全領域(85x49)",
           font=f, fill=(40, 40, 40))
    return g


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    front = build_front().convert("RGB")
    back = build_back().convert("RGB")
    with_guides(front, "表").save(OUT / "preview-omote.png", dpi=(DPI, DPI))
    with_guides(back, "裏").save(OUT / "preview-ura.png", dpi=(DPI, DPI))
    front.save(OUT / "meishi-omote.png", dpi=(DPI, DPI))
    back.save(OUT / "meishi-ura.png", dpi=(DPI, DPI))

    # 単体の QR（他の用途にも使えるように）
    segno.make(URL, error="m").save(str(OUT / "qr-coma.png"), scale=24, border=4,
                                    dark="#4a3428", light="#ffffff")
    segno.make(URL, error="m").save(str(OUT / "qr-coma.svg"), border=4, dark="#4a3428")

    pdf = OUT / "meishi-coma.pdf"
    c = canvas.Canvas(str(pdf), pagesize=(DATA_W * mm, DATA_H * mm))
    for im in (front, back):
        c.drawImage(ImageReader(im), 0, 0, width=DATA_W * mm, height=DATA_H * mm)
        c.showPage()
    c.setTitle("こま 名刺")
    c.save()

    (OUT / "qr-raw.png").unlink(missing_ok=True)
    print(f"データサイズ {DATA_W} x {DATA_H} mm / {W} x {H} px @ {DPI}dpi")
    print(f"出力: {pdf}")

    # --- 検品: 実際に書き出した PDF から QR を読み取れるか確かめる ---
    qr_sym = segno.make(URL, error="m")
    modules = qr_sym.symbol_size(border=0)[0]
    print(f"QR: version {qr_sym.version} / {modules}x{modules} モジュール "
          f"/ 25.0mm 印刷時 1モジュール {25.0 / modules:.2f}mm")
    try:
        import cv2
        import fitz
        import numpy as np

        page = fitz.open(str(pdf))[1]
        pix = page.get_pixmap(dpi=350)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        gray = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2GRAY)
        decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(gray)
        print("PDF から読み取った URL:", decoded or "(読み取り失敗)")
        assert decoded == URL, f"QR の内容が一致しません: {decoded!r}"
        print("検品 OK")
    except ImportError:
        print("検品スキップ (cv2 / fitz なし)")


if __name__ == "__main__":
    main()
