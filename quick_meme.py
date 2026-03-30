#!/usr/bin/env python3
"""
quick_meme.py — 快速從一句話生成設計並回傳預覽
供 Telegram /meme 指令呼叫。

語法：
  python quick_meme.py "句子"
  python quick_meme.py "*大字* /n 小字"
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
FONTS_DIR = BASE_DIR / "fonts"
OUTPUT_DIR = BASE_DIR / "output"
PREVIEW_FONTS = ["anton", "bebas", "abril", "oswald", "unifont", "fredoka",
                 "dancing", "pacifico", "caveat", "huninn", "genyomin", "genyogot",
                 "notoserif", "notosans", "cubic11", "trainone"]
SESSION_FILE = BASE_DIR / ".last_meme_session.json"


def make_preview_grid(font_sets: list[dict], font_names: list[str]) -> Path:
    """合成 2x2 預覽網格，每格顯示白底版，標註編號。"""
    from PIL import Image, ImageDraw, ImageFont

    n = len(font_sets)
    THUMB = 900
    LABEL_H = 120
    COLS = 2
    ROWS = (n + COLS - 1) // COLS

    grid = Image.new("RGB", (THUMB * COLS, (THUMB + LABEL_H) * ROWS), (40, 40, 40))
    draw = ImageDraw.Draw(grid)

    try:
        label_font = ImageFont.truetype(str(FONTS_DIR / "Anton-Regular.ttf"), 60)
    except Exception:
        label_font = ImageFont.load_default()

    for i, (fset, fname) in enumerate(zip(font_sets, font_names)):
        col = i % COLS
        row = i // COLS
        x = col * THUMB
        y = row * (THUMB + LABEL_H)

        # 預覽用白底顯示黑字透明版
        preview_rgba = Image.open(fset["black"]).convert("RGBA")
        bg = Image.new("RGB", preview_rgba.size, (255, 255, 255))
        bg.paste(preview_rgba, mask=preview_rgba.split()[3])
        img = bg
        img.thumbnail((THUMB, THUMB))
        px = x + (THUMB - img.width) // 2
        py = y + (THUMB - img.height) // 2
        grid.paste(img, (px, py))

        ly = y + THUMB
        draw.rectangle([x, ly, x + THUMB, ly + LABEL_H], fill=(20, 20, 20))
        label = f"  {i+1}. {fname.upper()}"
        draw.text((x + 15, ly + 20), label, font=label_font, fill=(255, 220, 50))

    out = OUTPUT_DIR / "_preview_grid_latest.png"
    grid.save(out, "PNG")
    return out


def run(text: str):
    from design_generator import generate_font_set

    fonts = PREVIEW_FONTS

    font_sets = []
    for font in fonts:
        print(f"  ✅ {font}")
        fset = generate_font_set(text, font)
        font_sets.append(fset)

    # 儲存 session（讓後續「上架」指令知道要上傳哪些檔案）
    session = {
        "text": text,
        "fonts": fonts,
        "sets": [{k: str(v) for k, v in fs.items()} for fs in font_sets]
    }
    with open(SESSION_FILE, "w") as f:
        json.dump(session, f, indent=2)

    grid = make_preview_grid(font_sets, fonts)
    print(str(grid))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_meme.py '你的句子'")
        sys.exit(1)
    text = " ".join(sys.argv[1:])
    print(f"🎨 生成：{text}")
    run(text)
