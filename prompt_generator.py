#!/usr/bin/env python3
"""
prompt_generator.py — Ideogram T 恤設計 Prompt 生成器
======================================================
輸入梗概念（文字），輸出可直接貼入 Ideogram 的 prompt，
並存成設計記錄。

使用方式：
  python prompt_generator.py "my brain at 3am"
  python prompt_generator.py --interactive        # 互動模式
  python prompt_generator.py --from-trends        # 從今日熱搜自動生成
"""

import os
import sys
import json
import argparse
import datetime
import random
from pathlib import Path

DESIGNS_DIR = Path(__file__).parent / "designs"
TRENDS_DIR = Path(__file__).parent / "trends"

# ── 風格模板庫 ────────────────────────────────────────────
STYLES = [
    {
        "name": "bold_minimal",
        "desc": "粗體極簡黑白",
        "template": (
            'Text-only t-shirt design, "{text}", '
            "bold sans-serif font, black text on white background, "
            "minimalist, centered layout, no illustrations, "
            "clean typography, print-ready, high contrast"
        ),
    },
    {
        "name": "retro_stamp",
        "desc": "復古印章風",
        "template": (
            'Vintage stamp style t-shirt, text "{text}", '
            "distressed retro typography, circular or badge layout, "
            "worn texture, 1970s aesthetic, single color, "
            "no photos, print-ready"
        ),
    },
    {
        "name": "handwritten",
        "desc": "手寫塗鴉風",
        "template": (
            'Handwritten grunge t-shirt design, "{text}", '
            "casual marker font, slightly messy, authentic feel, "
            "black ink on white, street art vibe, "
            "no complex illustrations, print-ready"
        ),
    },
    {
        "name": "varsity",
        "desc": "大學運動隊風",
        "template": (
            'Varsity college t-shirt typography, "{text}", '
            "athletic block letters, arched text layout, "
            "bold outline, retro sports aesthetic, "
            "2-3 colors max, no photos, print-ready"
        ),
    },
    {
        "name": "corporate_parody",
        "desc": "企業惡搞風",
        "template": (
            'Corporate parody t-shirt, "{text}", '
            "fake professional logo style, clean sans-serif, "
            "mockingly formal layout, office humor aesthetic, "
            "black and white, no real logos, print-ready"
        ),
    },
]

NEGATIVE_PROMPT = (
    "no photos, no people, no faces, no complex illustrations, "
    "no gradients, no watermark, no background pattern, "
    "simple and clean only"
)


def generate_prompts(concept: str, styles: list = None) -> list[dict]:
    """為一個梗概念生成多種風格的 Ideogram prompts。"""
    if styles is None:
        styles = STYLES

    results = []
    for style in styles:
        prompt = style["template"].format(text=concept)
        results.append({
            "concept": concept,
            "style": style["name"],
            "style_desc": style["desc"],
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "ideogram_settings": {
                "aspect_ratio": "ASPECT_1_1",      # 正方形，最適合 T 恤印刷
                "model": "V_2_TURBO",
                "magic_prompt_option": "OFF",       # 關掉 magic prompt，保持精確
                "style_type": "DESIGN",
            },
        })
    return results


def save_design_session(concept: str, prompts: list[dict]) -> Path:
    """儲存設計記錄。"""
    DESIGNS_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = concept[:30].replace(" ", "_").replace("/", "-")
    path = DESIGNS_DIR / f"{ts}_{safe_name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "concept": concept,
            "generated_at": ts,
            "prompts": prompts,
        }, f, ensure_ascii=False, indent=2)
    return path


def print_prompts(concept: str, prompts: list[dict]):
    print(f"\n{'═'*60}")
    print(f"🎨 梗概念：{concept}")
    print(f"{'═'*60}")
    print(f"⚠️  Ideogram 設定：Aspect Ratio = 1:1，Style = Design，Magic Prompt = OFF\n")

    for i, p in enumerate(prompts, 1):
        print(f"── 風格 {i}：{p['style_desc']} ──")
        print(f"PROMPT：")
        print(f"  {p['prompt']}")
        print(f"NEGATIVE：")
        print(f"  {p['negative_prompt']}")
        print()


def from_trends_mode():
    """從今日熱搜 JSON 挑出前幾名，生成 prompts。"""
    today = datetime.date.today().isoformat()
    trend_file = TRENDS_DIR / f"{today}.json"

    if not trend_file.exists():
        print(f"❌ 找不到今日趨勢報告：{trend_file}")
        print("   請先執行：python trend_monitor.py")
        return

    with open(trend_file, encoding="utf-8") as f:
        data = json.load(f)

    top = data.get("top_reddit_memes", [])[:5]
    print(f"\n📊 從今日熱搜自動生成 prompts（{today}）\n")

    for post in top:
        title = post["title"]
        # 簡化標題為 T 恤文字（截短）
        concept = title[:50]
        print(f"\n🔥 原始梗：{title[:80]}")
        print(f"   r/{post['subreddit']} ↑{post['score']:,}")

        # 只選 2 個風格避免輸出太長
        selected_styles = random.sample(STYLES, 2)
        prompts = generate_prompts(concept, selected_styles)
        print_prompts(concept, prompts)
        save_design_session(concept, prompts)


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ideogram T 恤設計 Prompt 生成器")
    parser.add_argument("concept", nargs="?", help="梗概念文字")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="互動模式，持續輸入概念")
    parser.add_argument("--from-trends", action="store_true",
                        help="從今日熱搜自動生成")
    parser.add_argument("--styles", nargs="+",
                        choices=[s["name"] for s in STYLES],
                        help="指定風格（預設全部）")
    args = parser.parse_args()

    # 篩選風格
    selected_styles = STYLES
    if args.styles:
        selected_styles = [s for s in STYLES if s["name"] in args.styles]

    if args.from_trends:
        from_trends_mode()

    elif args.interactive:
        print("🎨 互動模式 — 輸入梗概念，按 Enter 生成，輸入 q 離開\n")
        while True:
            concept = input("梗概念：").strip()
            if concept.lower() in ("q", "quit", "exit", ""):
                break
            prompts = generate_prompts(concept, selected_styles)
            print_prompts(concept, prompts)
            path = save_design_session(concept, prompts)
            print(f"💾 已儲存：{path.name}\n")

    elif args.concept:
        prompts = generate_prompts(args.concept, selected_styles)
        print_prompts(args.concept, prompts)
        path = save_design_session(args.concept, prompts)
        print(f"💾 已儲存：{path.name}")

    else:
        parser.print_help()
