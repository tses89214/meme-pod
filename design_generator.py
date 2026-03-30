#!/usr/bin/env python3
"""
design_generator.py — 純文字 T 恤設計生成器
=============================================
輸入梗文字，輸出多種風格的印刷用 PNG（5000x5000px, 300dpi）。
每種風格同時輸出：實色版 + 透明背景版（適合各色 T 恤）。

使用方式：
  python design_generator.py "adult cheat code"
  python design_generator.py "AC levels: legend to lazy" --styles minimal retro
  python design_generator.py --from-trends     # 從今日熱搜批量生成
"""

import re
import sys
import json
import argparse
import datetime
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent
FONTS_DIR = BASE_DIR / "fonts"
OUTPUT_DIR = BASE_DIR / "output"
TRENDS_DIR = BASE_DIR / "trends"

# 印刷規格（Redbubble 建議：最小 5000x5000px）
CANVAS_W = 5000
CANVAS_H = 5000

# 安全邊距（12% = 600px，印刷不裁到文字）
MARGIN = 0.12

# ── 字體路徑 ──────────────────────────────────────────────
F = {
    "anton":    str(FONTS_DIR / "Anton-Regular.ttf"),
    "bebas":    str(FONTS_DIR / "BebasNeue-Regular.ttf"),
    "abril":    str(FONTS_DIR / "AbrilFatface-Regular.ttf"),
    "oswald":   str(FONTS_DIR / "Oswald.ttf"),
    "unifont":  str(FONTS_DIR / "UnifontJP.otf"),
    "fredoka":  str(FONTS_DIR / "FredokaOne-Regular.ttf"),
    "dancing":  str(FONTS_DIR / "DancingScript.ttf"),
    "pacifico": str(FONTS_DIR / "Pacifico-Regular.ttf"),
    "caveat":   str(FONTS_DIR / "Caveat.ttf"),
    "huninn":   str(FONTS_DIR / "jf-openhuninn.ttf"),
    "genyomin": str(FONTS_DIR / "GenYoMin2TW-R.otf"),
    "genyogot": str(FONTS_DIR / "GenYoGothic2TW-R.otf"),
    "notoserif":str(FONTS_DIR / "NotoSerifCJKtc-Regular.otf"),
    "notosans": str(FONTS_DIR / "NotoSansTC.ttf"),
    "cubic11":  str(FONTS_DIR / "Cubic11.ttf"),
    "trainone": str(FONTS_DIR / "TrainOne.ttf"),
    "fallback": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
}


def load_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(F.get(key, F["fallback"]), size)
    except Exception:
        return ImageFont.truetype(F["fallback"], size)


def clean_text(text: str) -> str:
    """清洗梗標題：去掉多餘符號、截短、適合 T 恤呈現。"""
    text = re.sub(r'\[.*?\]|\(.*?\)', '', text)
    text = re.sub(r'[^\w\s\'\"\-\!\?\:\,\.\*\/]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > 120:
        text = text[:117] + "..."
    return text


def parse_segments(text: str, max_chars_large: int = 14, max_chars_small: int = 20) -> list[dict]:
    """
    解析文字為帶有大小標記的段落。
    語法：
      *文字* → 大字（size="large"）
      /n     → 換行分隔
      其餘   → 小字（size="small"）

    回傳：[{"text": str, "size": "large"|"small"}, ...]
    """
    # 把 /n 轉成真正換行
    text = text.replace("/n", "\n")
    # 分割出 *...* 區塊
    raw_segments = re.split(r'(\*[^*]+\*)', text)

    segments = []
    for seg in raw_segments:
        seg = seg.strip()
        if not seg:
            continue
        if seg.startswith("*") and seg.endswith("*"):
            content = seg[1:-1].strip()
            size = "large"
            max_c = max_chars_large
        else:
            content = seg
            size = "small"
            max_c = max_chars_small

        # 依換行拆分，再 wrap
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue
            wrapped = textwrap.wrap(line, width=max_c) or [line]
            for w in wrapped:
                segments.append({"text": w, "size": size})

    return segments if segments else [{"text": text, "size": "large"}]


def auto_wrap(text: str, max_chars: int = 18) -> list[str]:
    """自動換行（用於無格式文字）。"""
    lines = []
    for para in text.replace("/n", "\n").split("\n"):
        wrapped = textwrap.wrap(para.strip(), width=max_chars) or [""]
        lines.extend(wrapped)
    return lines


def fit_font_size(draw, lines: list[str], font_key: str,
                  max_w: int, max_h: int,
                  size_start: int = 800, size_min: int = 60) -> tuple:
    """找出能填滿 max_w x max_h 的最大字型。"""
    size = size_start
    while size >= size_min:
        font = load_font(font_key, size)
        widths = [draw.textlength(l, font=font) for l in lines]
        bbox = font.getbbox("Ag")
        line_h = bbox[3] - bbox[1]
        gap = line_h * 0.25
        total_h = line_h * len(lines) + gap * max(0, len(lines) - 1)
        if max(widths, default=0) <= max_w and total_h <= max_h:
            return font, size, line_h, gap
        size -= 10
    font = load_font(font_key, size_min)
    bbox = font.getbbox("Ag")
    line_h = bbox[3] - bbox[1]
    return font, size_min, line_h, line_h * 0.25


def draw_text_block(draw, lines, font, line_h, gap,
                    canvas_w, y_center, text_color, stroke=0):
    """將多行文字水平置中、垂直置中繪製。"""
    n = len(lines)
    total_h = line_h * n + gap * max(0, n - 1)
    y = y_center - total_h / 2

    for line in lines:
        w = draw.textlength(line, font=font)
        x = (canvas_w - w) / 2
        if stroke > 0:
            # 描邊（對透明背景版很有用）
            for dx in range(-stroke, stroke + 1):
                for dy in range(-stroke, stroke + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), line, font=font,
                                  fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=text_color)
        y += line_h + gap


# ═══════════════════════════════════════════════════════════
# 風格定義
# ═══════════════════════════════════════════════════════════

# 4 fonts × 2 colors = 8 variants
# name format: {font}_{light|dark}
STYLES = {
    "anton_light":  {"desc": "Anton 白底黑字",        "font": "anton",  "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 16, "uppercase": True},
    "anton_dark":   {"desc": "Anton 黑底白字",        "font": "anton",  "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 16, "uppercase": True},
    "bebas_light":  {"desc": "Bebas Neue 白底黑字",   "font": "bebas",  "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 20, "uppercase": True},
    "bebas_dark":   {"desc": "Bebas Neue 黑底白字",   "font": "bebas",  "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 20, "uppercase": True},
    "abril_light":  {"desc": "Abril Fatface 白底黑字","font": "abril",  "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 18, "uppercase": False},
    "abril_dark":   {"desc": "Abril Fatface 黑底白字","font": "abril",  "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 18, "uppercase": False},
    "oswald_light":  {"desc": "Oswald 白底黑字",       "font": "oswald",  "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 18, "uppercase": True},
    "oswald_dark":   {"desc": "Oswald 黑底白字",       "font": "oswald",  "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 18, "uppercase": True},
    "unifont_light":  {"desc": "Unifont 白底黑字",      "font": "unifont", "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 20, "uppercase": False},
    "unifont_dark":   {"desc": "Unifont 黑底白字",      "font": "unifont", "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 20, "uppercase": False},
    "fredoka_light":  {"desc": "Fredoka One 白底黑字",  "font": "fredoka", "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 18, "uppercase": False},
    "fredoka_dark":   {"desc": "Fredoka One 黑底白字",  "font": "fredoka", "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 18, "uppercase": False},
    "dancing_light":  {"desc": "Dancing Script 白底黑字","font": "dancing", "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 20, "uppercase": False},
    "dancing_dark":   {"desc": "Dancing Script 黑底白字","font": "dancing", "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 20, "uppercase": False},
    "pacifico_light": {"desc": "Pacifico 白底黑字",     "font": "pacifico","bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 18, "uppercase": False},
    "pacifico_dark":  {"desc": "Pacifico 黑底白字",     "font": "pacifico","bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 18, "uppercase": False},
    "caveat_light":   {"desc": "Caveat 白底黑字",        "font": "caveat",  "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 22, "uppercase": False},
    "caveat_dark":    {"desc": "Caveat 黑底白字",        "font": "caveat",  "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 22, "uppercase": False},
    "huninn_light":   {"desc": "jf 粉圓 白底黑字",      "font": "huninn",  "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 20, "uppercase": False},
    "huninn_dark":    {"desc": "jf 粉圓 黑底白字",      "font": "huninn",  "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 20, "uppercase": False},
    "genyomin_light": {"desc": "源様明朝 TW 白底黑字",  "font": "genyomin","bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 20, "uppercase": False},
    "genyomin_dark":  {"desc": "源様明朝 TW 黑底白字",  "font": "genyomin","bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 20, "uppercase": False},
    "genyogot_light": {"desc": "源様圓體 TW 白底黑字",  "font": "genyogot", "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 20, "uppercase": False},
    "genyogot_dark":  {"desc": "源様圓體 TW 黑底白字",  "font": "genyogot", "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 20, "uppercase": False},
    "notoserif_light":{"desc": "思源宋體 TC 白底黑字",  "font": "notoserif","bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 20, "uppercase": False},
    "notoserif_dark": {"desc": "思源宋體 TC 黑底白字",  "font": "notoserif","bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 20, "uppercase": False},
    "notosans_light": {"desc": "思源黑體 TC 白底黑字",  "font": "notosans", "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 20, "uppercase": False},
    "notosans_dark":  {"desc": "思源黑體 TC 黑底白字",  "font": "notosans", "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 20, "uppercase": False},
    "cubic11_light":  {"desc": "Cubic 11 白底黑字",     "font": "cubic11",  "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 20, "uppercase": False},
    "cubic11_dark":   {"desc": "Cubic 11 黑底白字",     "font": "cubic11",  "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 20, "uppercase": False},
    "trainone_light": {"desc": "Train One 白底黑字",    "font": "trainone", "bg": (255,255,255), "text_color": (10,10,10),   "max_chars": 20, "uppercase": False},
    "trainone_dark":  {"desc": "Train One 黑底白字",    "font": "trainone", "bg": (15,15,15),    "text_color": (245,245,245),"max_chars": 20, "uppercase": False},
}


def render_segments(draw, segments: list[dict], font_key: str,
                    area_w: int, area_h: int, canvas_w: int, y_center: int,
                    text_color, stroke: int = 0, uppercase: bool = True):
    """
    渲染多尺寸段落，保留順序（A small / B large / C small 等結構）。
    large 字大，small 約 52%，間距依相鄰行高動態調整。
    """
    if not segments:
        return

    SMALL_RATIO = 0.52   # small 字相對 large 的比例
    GAP_RATIO   = 0.30   # 相鄰段落間距相對於較大那行的比例

    # 迭代找最大可用字型大小
    font_l = font_s = None
    lh_l = lh_s = 0
    large_size = 800

    while large_size >= 60:
        font_l = load_font(font_key, large_size)
        lh_l = font_l.getbbox("Ag")[3] - font_l.getbbox("Ag")[1]

        small_size = max(40, int(large_size * SMALL_RATIO))
        font_s = load_font(font_key, small_size)
        lh_s = font_s.getbbox("Ag")[3] - font_s.getbbox("Ag")[1]

        # 檢查所有行寬度是否符合
        fits_w = all(
            draw.textlength(
                s["text"].upper() if uppercase else s["text"],
                font=font_l if s["size"] == "large" else font_s
            ) <= area_w
            for s in segments
        )
        if not fits_w:
            large_size -= 20
            continue

        # 計算總高度（按順序，含段落間距）
        heights = [lh_l if s["size"] == "large" else lh_s for s in segments]
        total_h = sum(heights)
        for i in range(1, len(segments)):
            total_h += max(heights[i - 1], heights[i]) * GAP_RATIO

        if total_h <= area_h:
            break
        large_size -= 20

    # 計算各行 y 起始位置
    heights = [lh_l if s["size"] == "large" else lh_s for s in segments]
    total_h = sum(heights)
    for i in range(1, len(segments)):
        total_h += max(heights[i - 1], heights[i]) * GAP_RATIO

    y = y_center - total_h / 2

    # 按順序渲染
    for i, (s, lh) in enumerate(zip(segments, heights)):
        if i > 0:
            y += max(heights[i - 1], heights[i]) * GAP_RATIO

        line = s["text"].upper() if uppercase else s["text"]
        f = font_l if s["size"] == "large" else font_s
        w = draw.textlength(line, font=f)
        x = (canvas_w - w) / 2

        if stroke:
            for dx in range(-stroke, stroke + 1):
                for dy in range(-stroke, stroke + 1):
                    if dx or dy:
                        draw.text((x + dx, y + dy), line, font=f, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=f, fill=text_color)
        y += lh


def _render_solid(segments, font_key, uppercase, bg, text_color,
                   area_w, area_h, ts, safe, suffix) -> Path:
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), color=bg)
    draw = ImageDraw.Draw(img)
    render_segments(draw, segments, font_key, area_w, area_h,
                    CANVAS_W, CANVAS_H // 2, text_color,
                    stroke=0, uppercase=uppercase)
    path = OUTPUT_DIR / f"{ts}_{safe}_{suffix}.png"
    img.save(path, "PNG", dpi=(300, 300))
    return path


def _render_transparent(segments, font_key, uppercase, text_color,
                         area_w, area_h, ts, safe, suffix) -> Path:
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    tc = text_color
    render_segments(draw, segments, font_key, area_w, area_h,
                    CANVAS_W, CANVAS_H // 2, (*tc, 255),
                    stroke=3, uppercase=uppercase)
    path = OUTPUT_DIR / f"{ts}_{safe}_{suffix}_transparent.png"
    img.save(path, "PNG", dpi=(300, 300))
    return path


def generate_font_set(text: str, font_key: str) -> dict:
    """
    為一個字體生成兩個透明版本：
    - black: 透明底黑字（適合淺色衣服）
    - white: 透明底白字（適合深色衣服）
    回傳 {"black": Path, "white": Path}
    """
    font_style = STYLES[f"{font_key}_light"]  # 取 max_chars / uppercase 設定
    clean = clean_text(text)
    segments = parse_segments(clean,
                              max_chars_large=font_style["max_chars"],
                              max_chars_small=font_style["max_chars"] + 4)

    area_w = int(CANVAS_W * (1 - 2 * MARGIN))
    area_h = int(CANVAS_H * (1 - 2 * MARGIN))

    OUTPUT_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = re.sub(r'[^\w]', '_', re.sub(r'\*', '', text)[:25])
    uppercase = font_style["uppercase"]

    black = _render_transparent(segments, font_key, uppercase,
                                (10, 10, 10),
                                area_w, area_h, ts, safe, f"{font_key}_black")
    white = _render_transparent(segments, font_key, uppercase,
                                (245, 245, 245),
                                area_w, area_h, ts, safe, f"{font_key}_white")
    return {"black": black, "white": white}


# Keep old interface for compatibility
def generate_design(text: str, style_name: str = "anton_light") -> tuple[Path, Path]:
    font_key = style_name.replace("_light", "").replace("_dark", "")
    result = generate_font_set(text, font_key)
    return result["black"], result["white"]


def batch_generate(text: str, styles: list = None) -> list[tuple]:
    if styles is None:
        styles = list(STYLES.keys())
    results = []
    for s in styles:
        solid, trans = generate_design(text, s)
        print(f"  ✅ {s:10s} → {solid.name}")
        results.append((solid, trans))
    return results


def from_trends(top_n: int = 5, styles: list = None) -> list:
    today = datetime.date.today().isoformat()
    trend_file = TRENDS_DIR / f"{today}.json"
    if not trend_file.exists():
        print("❌ 找不到今日趨勢，請先執行 trend_monitor.py")
        return []
    with open(trend_file, encoding="utf-8") as f:
        data = json.load(f)
    top = data.get("top_reddit_memes", [])[:top_n]
    all_results = []
    for post in top:
        text = post["title"]
        print(f"\n🎨 生成：{clean_text(text)[:50]}")
        results = batch_generate(text, styles)
        all_results.extend(results)
    return all_results


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="純文字 T 恤設計生成器")
    parser.add_argument("text", nargs="?", help="T 恤文字")
    parser.add_argument("--styles", nargs="+", choices=list(STYLES.keys()),
                        help=f"風格（預設全部）")
    parser.add_argument("--from-trends", action="store_true")
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    styles = args.styles or list(STYLES.keys())

    if args.from_trends:
        from_trends(top_n=args.top, styles=styles)
    elif args.text:
        print(f"\n🎨 生成設計：{args.text}")
        batch_generate(args.text, styles)
        print(f"\n✅ 完成！輸出：{OUTPUT_DIR}")
    else:
        parser.print_help()
