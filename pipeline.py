#!/usr/bin/env python3
"""
pipeline.py — 全自動梗圖 T 恤流水線
=====================================
一鍵執行：抓趨勢 → 生成設計 → 上架 Redbubble → Telegram 通知

使用方式：
  python pipeline.py                    # 全流程
  python pipeline.py --no-upload        # 只生成不上傳
  python pipeline.py --top 3 --styles minimal dark
"""

import os
import argparse
import datetime
import requests
from pathlib import Path

from trend_monitor import run as fetch_trends
from design_generator import from_trends as generate_designs, STYLES
from uploader import batch_upload, load_log

OUTPUT_DIR = Path(__file__).parent / "output"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1210712482")

DEFAULT_TAGS = [
    "funny", "meme", "humor", "gift", "sarcastic",
    "relatable", "trending", "internet", "viral", "quote"
]


def notify_telegram(uploaded: int, top_memes: list, date: str):
    """發 Telegram 通知：今日成果。"""
    if not TELEGRAM_TOKEN:
        return
    lines = [
        f"🎉 梗圖流水線完成 — {date}",
        f"✅ 今日上架：{uploaded} 件",
        "",
        "🔥 今日梗文字："
    ]
    for m in top_memes[:5]:
        lines.append(f"• {m['title'][:50]}")

    lines += ["", "👉 前往 Redbubble 查看上架結果"]
    text = "\n".join(lines)

    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10
        )
    except Exception as e:
        print(f"  ⚠️  Telegram 通知失敗：{e}")


def main():
    parser = argparse.ArgumentParser(description="梗圖 T 恤全自動流水線")
    parser.add_argument("--top", type=int, default=5, help="取熱搜前幾筆（預設 5）")
    parser.add_argument("--styles", nargs="+", choices=list(STYLES.keys()),
                        default=["minimal", "dark"],
                        help="生成哪些風格（預設 minimal + dark）")
    parser.add_argument("--no-upload", action="store_true", help="只生成不上傳")
    args = parser.parse_args()

    date = datetime.date.today().isoformat()
    print(f"\n{'═'*55}")
    print(f"🚀 梗圖 T 恤流水線 — {date}")
    print(f"{'═'*55}\n")

    # Step 1: 抓趨勢
    print("【Step 1】抓取今日熱梗...")
    report = fetch_trends()
    top_memes = report.get("top_reddit_memes", [])[:args.top]

    # Step 2: 生成設計
    print(f"\n【Step 2】生成設計（Top {args.top}，風格：{args.styles}）...")
    generate_designs(top_n=args.top, styles=args.styles)

    # Step 3: 上傳
    uploaded = 0
    if not args.no_upload:
        print("\n【Step 3】上架至 Redbubble...")
        uploaded = batch_upload(OUTPUT_DIR, DEFAULT_TAGS)
    else:
        print(f"\n⏭️  略過上傳。設計圖位於：{OUTPUT_DIR}")

    # Step 4: Telegram 通知
    if uploaded > 0:
        notify_telegram(uploaded, top_memes, date)

    # 統計
    log = load_log()
    total = len(log.get("uploaded", []))
    print(f"\n{'═'*55}")
    print(f"✅ 完成！今日上架 {uploaded} 件，累計 {total} 件")
    print(f"{'═'*55}\n")


if __name__ == "__main__":
    main()
