#!/usr/bin/env python3
"""
trend_monitor.py — 每日熱梗監控
=================================
抓取 Reddit + Google Trends 熱門話題，
篩選適合做成文字 T 恤的梗，存成報告。

使用方式：
  python trend_monitor.py              # 執行一次
  python trend_monitor.py --notify     # 完成後發 Telegram 通知
"""

import os
import json
import argparse
import datetime
import requests
from pathlib import Path

# ── 設定 ──────────────────────────────────────────────────
TRENDS_DIR = Path(__file__).parent / "trends"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "1210712482")

REDDIT_SOURCES = [
    ("memes",    "hot", 25),
    ("funny",    "hot", 25),
    ("antiwork", "hot", 15),
    ("gaming",   "hot", 15),
    ("AskReddit","hot", 15),
]

# 篩選關鍵字（標題含這些詞更可能是文字梗）
TEXT_MEME_SIGNALS = [
    "me when", "pov:", "nobody:", "me:", "that feeling when",
    "unpopular opinion", "hot take", "life is", "the type of",
    "my boss", "my brain", "normalize", "friendly reminder",
    "i don't know who needs to hear this", "you either",
    "not me", "we need to talk about", "just a reminder",
    "why is", "how it feels", "real ones", "raise your hand if",
    "anyone else", "it's giving", "no one:", "main character",
]

# 圖片依賴信號（這種標題脫離圖片就沒意義）
IMAGE_DEPENDENT_SIGNALS = [
    "every single time", "stumble upon", "one of us", "balkan",
    "their ticket", "low intelligence", "speakerphone",
    "look at", "see this", "found this", "check this",
    "this is", "these are", "that is", "what is this",
    "[oc]", "ft.", "via ", "pic ", "photo",
]

# 排除詞（政治、新聞、地區性）
EXCLUDE_SIGNALS = [
    "oc]", "[image]", "ukraine", "election", "trump", "biden",
    "breaking", "shooting", "war", "attack", "israel", "gaza",
    "literally me when i open",  # 太圖片依賴
]


# ═══════════════════════════════════════════════════════════
# Reddit 抓取
# ═══════════════════════════════════════════════════════════

def fetch_reddit(subreddit: str, sort: str = "hot", limit: int = 25) -> list[dict]:
    """抓取 subreddit 熱門貼文（無需 API key）。"""
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
    headers = {"User-Agent": "meme-pod-monitor/1.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        posts = resp.json()["data"]["children"]
        return [
            {
                "title": p["data"]["title"],
                "score": p["data"]["score"],
                "comments": p["data"]["num_comments"],
                "url": f"https://reddit.com{p['data']['permalink']}",
                "subreddit": subreddit,
                "created": p["data"]["created_utc"],
            }
            for p in posts
            if not p["data"].get("is_video") and p["data"]["score"] > 500
        ]
    except Exception as e:
        print(f"  ⚠️  Reddit r/{subreddit} 失敗：{e}")
        return []


def score_for_tshirt(title: str) -> int:
    """給標題打分：越適合做文字 T 恤分數越高。"""
    title_lower = title.lower()
    score = 0

    # 有文字梗信號 +2 each
    for signal in TEXT_MEME_SIGNALS:
        if signal in title_lower:
            score += 2

    # 圖片依賴信號 -5 each（脫離圖片就沒意義）
    for sig in IMAGE_DEPENDENT_SIGNALS:
        if sig in title_lower:
            score -= 5

    # 排除詞 -10
    for ex in EXCLUDE_SIGNALS:
        if ex in title_lower:
            score -= 10

    # 標題長度適中（適合 T 恤：4~12 字最佳）
    words = len(title.split())
    if 4 <= words <= 12:
        score += 3
    elif 3 <= words <= 15:
        score += 1
    else:
        score -= 3

    # 含問號或感嘆號（情緒性，好做梗）
    if "?" in title or "!" in title:
        score += 1

    # 第一人稱或直接呼喚讀者（更有共鳴）
    if title_lower.startswith(("i ", "me ", "my ", "we ", "you ", "your ")):
        score += 2

    return score


# ═══════════════════════════════════════════════════════════
# Google Trends（使用 pytrends 或直接 RSS）
# ═══════════════════════════════════════════════════════════

def fetch_google_trends_rss() -> list[str]:
    """抓取 Google Trends 美國每日熱搜（多重備援）。"""
    # 方法一：RSS
    try:
        url = "https://trends.google.com/trending/rss?geo=US"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200 and "<title>" in resp.text:
            import re
            titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", resp.text)
            titles = [t for t in titles if t != "Google Trends"]
            if titles:
                return titles[:20]
    except Exception:
        pass

    # 方法二：pytrends
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
        df = pt.trending_searches(pn="united_states")
        return df[0].tolist()[:20]
    except Exception as e:
        print(f"  ⚠️  Google Trends 全部失敗：{e}")
        return []


# ═══════════════════════════════════════════════════════════
# 主邏輯
# ═══════════════════════════════════════════════════════════

def run(notify: bool = False):
    today = datetime.date.today().isoformat()
    print(f"\n🔍 抓取熱梗中... ({today})\n")

    # 抓 Reddit
    all_posts = []
    for sub, sort, limit in REDDIT_SOURCES:
        print(f"  Reddit r/{sub}...")
        posts = fetch_reddit(sub, sort, limit)
        all_posts.extend(posts)

    # 打分 + 排序
    for p in all_posts:
        p["tshirt_score"] = score_for_tshirt(p["title"])

    candidates = [p for p in all_posts if p["tshirt_score"] > 0]
    candidates.sort(key=lambda x: (x["tshirt_score"], x["score"]), reverse=True)
    top = candidates[:15]

    # 抓 Google Trends
    print("  Google Trends US...")
    trends = fetch_google_trends_rss()

    # 組成報告
    report = {
        "date": today,
        "top_reddit_memes": top,
        "google_trends": trends,
    }

    # 存檔
    TRENDS_DIR.mkdir(exist_ok=True)
    report_path = TRENDS_DIR / f"{today}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 輸出摘要
    print(f"\n{'═'*50}")
    print(f"📊 今日熱梗 Top 10（適合文字 T 恤）")
    print(f"{'═'*50}")
    for i, p in enumerate(top[:10], 1):
        print(f"{i:2}. [{p['tshirt_score']:+d}] {p['title'][:70]}")
        print(f"     ↑{p['score']:,}  r/{p['subreddit']}")

    print(f"\n🔥 Google Trends 美國熱搜：")
    for t in trends[:10]:
        print(f"   • {t}")

    print(f"\n📄 完整報告：{report_path}")

    # Telegram 通知
    if notify and TELEGRAM_TOKEN:
        send_telegram_report(top[:10], trends[:10], today)

    return report


def send_telegram_report(top_memes: list, trends: list, date: str):
    """發送每日報告到 Telegram。"""
    lines = [f"📊 *梗圖熱搜日報* — {date}\n"]
    lines.append("*Top Reddit 文字梗（T 恤潛力）：*")
    for i, p in enumerate(top_memes[:8], 1):
        lines.append(f"{i}\\. {p['title'][:60]}")

    lines.append("\n*Google Trends 美國熱搜：*")
    for t in trends[:8]:
        lines.append(f"• {t}")

    lines.append("\n⚡ 快去 Ideogram 出設計！")

    text = "\n".join(lines)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "MarkdownV2"
    }, timeout=10)


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="每日梗圖熱搜監控")
    parser.add_argument("--notify", action="store_true",
                        help="完成後發 Telegram 通知")
    args = parser.parse_args()
    run(notify=args.notify)
