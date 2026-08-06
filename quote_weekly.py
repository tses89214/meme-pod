#!/usr/bin/env python3
"""
quote_weekly.py — 每週語錄搜尋 + 挑選 + 排版建議，自動回報 Telegram
======================================================================
給 cron 用，全程不用互動：
  1. quote_search.py 抓 Tavily 候選（純搜尋，deterministic）
  2. 丟給一個獨立、跟本機常駐 TG bot session 隔離的 `claude -p` 子行程做「挑選 + 排版建議」
     （用 --strict-mcp-config --mcp-config '{}' 確保不會碰 telegram plugin，
     不會跟常駐的 --channels session 搶同一個 bot token 的 long-poll，
     這是 2026-08-05 `claude mcp list` 弄斷自己 TG 連線那次事故學到的教訓）
  3. 直接呼叫 Telegram Bot API 的 sendMessage（不透過 MCP plugin）把結果傳給使用者

用法：
  python quote_weekly.py
"""

import subprocess
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).parent
TELEGRAM_ENV = Path.home() / ".claude/channels/telegram/.env"
CHAT_ID = "1210712482"

CURATION_PROMPT = """以下是從 Tavily 搜到的英文語錄候選（跨搞怪/毒舌/正向/自嘲等類別）。
從中挑 5-8 句最適合印在梗圖 T 恤上的：要短（塞得下衣服）、有記憶點、
好笑或有共鳴，跳過老套陳腔濫調（例如 "Dream Big Work Hard" 這種到處都是的）。
每句都給排版建議，格式是 "*加粗字* /n 其餘文字"，用 /n 斷行（2-4 短行，
把最有記憶點的字/詞加粗）。只輸出編號列表，不要任何前言或說明。

{candidates}
"""


def run_curation(candidates: str) -> str:
    prompt = CURATION_PROMPT.format(candidates=candidates)
    result = subprocess.run(
        ["claude", "-p", prompt,
         "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
         "--dangerously-skip-permissions"],
        cwd=BASE_DIR, capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude -p 失敗: {result.stderr[:500]}")
    return result.stdout.strip()


def send_telegram(text: str):
    token = None
    for line in TELEGRAM_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            token = line.split("=", 1)[1]
    if not token:
        raise RuntimeError(f"{TELEGRAM_ENV} 裡沒有 TELEGRAM_BOT_TOKEN")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=20) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Telegram sendMessage 失敗: {resp.status}")


def main():
    import quote_search
    api_key = quote_search.load_api_key()
    parts = []
    for q in quote_search.DEFAULT_QUERIES:
        parts.append(f"=== {q} ===\n{quote_search.search_quotes(q, api_key)}")
    candidates = "\n\n".join(parts)

    picks = run_curation(candidates)
    send_telegram(f"本週語錄搜尋結果：\n\n{picks}")
    print(picks)
    print("已送出")


if __name__ == "__main__":
    main()
