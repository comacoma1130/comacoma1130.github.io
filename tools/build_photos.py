# -*- coding: utf-8 -*-
"""元写真を Web 用に一括変換して photos/ に出力する。

使い方:
    python tools/build_photos.py <元写真フォルダ>

- Exif の回転情報を反映してから破棄（iPhone 写真が横倒しになるのを防ぐ）
- 長辺 1600px に縮小、JPEG 品質 78 / プログレッシブ
- GPS を含む Exif は保存しない
- photos/ の中身は毎回作り直される
"""
import sys
from pathlib import Path

from PIL import Image, ImageOps

MAX_EDGE = 1600
QUALITY = 78
EXTS = (".jpg", ".jpeg", ".png", ".webp")

ROOT = Path(__file__).resolve().parent.parent
DST = ROOT / "photos"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src_dir = Path(sys.argv[1])
    if not src_dir.is_dir():
        print(f"フォルダが見つかりません: {src_dir}")
        return 1

    DST.mkdir(parents=True, exist_ok=True)
    for old in DST.glob("*.jpg"):
        old.unlink()

    files = sorted(
        (p for p in src_dir.iterdir() if p.suffix.lower() in EXTS),
        key=lambda p: p.name.lower(),
    )

    count = 0
    for i, src in enumerate(files, 1):
        try:
            im = Image.open(src)
        except Exception as e:  # noqa: BLE001
            print(f"SKIP {src.name}: {e}")
            continue
        im = ImageOps.exif_transpose(im)
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
        out = DST / f"coma-{i:02d}.jpg"
        im.save(out, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        count = i
        print(f"{src.name} -> {out.name}  {im.width}x{im.height}  {out.stat().st_size / 1024:.0f}KB")

    if count:
        base = Image.open(DST / "coma-01.jpg")
        og = ImageOps.fit(base, (1200, 630), Image.LANCZOS, centering=(0.5, 0.4))
        og.save(ROOT / "ogp.jpg", "JPEG", quality=80, optimize=True, progressive=True)

    print(f"\n{count} 枚を出力しました。script.js の PHOTO_COUNT を {count} にしてください。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
