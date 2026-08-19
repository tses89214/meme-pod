#!/usr/bin/env python3
"""
pinterest_trends_check.py — 每天看 Pinterest Trends，把趨勢主題轉成梗圖 T 恤點子
======================================================================
給 cron 用，全程不用互動：
  1. Selenium（跟 rb_upload.py 共用登入 profile）開 Pinterest Trends 頁面，抓頁面文字（deterministic）
  2. 丟給一個獨立、跟本機常駐 TG bot session 隔離的 `claude -p` 子行程做「趨勢 -> 設計點子」判斷
     （隔離做法跟 quote_weekly.py 一樣，避免搶同一個 bot token 的 long-poll）
  3. 直接呼叫 Telegram Bot API 的 sendMessage（不透過 MCP plugin）把結果傳給使用者

用法：
  python pinterest_trends_check.py
"""

import subprocess
import time
import urllib.request
import urllib.parse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
TELEGRAM_ENV = Path.home() / ".claude/channels/telegram/.env"
CHAT_ID = "1210712482"
TRENDS_URL = "https://trends.pinterest.com/?advertiserId=549770656829&topicInterestIds=948967005229%7C924581335376%7C903733943146"

sys.path.insert(0, str(BASE_DIR))

CURATION_PROMPT = """以下是今天從 Pinterest Trends 頁面抓到的美國趨勢原始文字（焦點趨勢、購物趨勢、搜尋趨勢、編輯精選）。
我們賣的是搞笑/毒舌梗圖 T 恤（Redbubble），主題涵蓋上班族吐槽、遊戲人生等級、寵物雙關語、中文雙語設計、
健身勵志、生活小確幸等。這些 Pinterest 趨勢大多是時尚/美妝/居家類，不會直接對應，
你的工作是找出「能不能從這個趨勢延伸出一句適合印 T 恤的搞笑/雙關/自嘲文案」，不要硬套。

規則：
- 只挑真的有梗可以延伸的趨勢，找不到就跳過，不用湊數
- 最多給 5 個點子，每個附一句話說明是從哪個趨勢延伸的
- 每個點子給一句 T 恤文案草稿（英文，短，適合印胸口）
- 如果 5 個趨勢裡完全沒有能用的，就明講「今天沒有適合的」，不要硬掰

只輸出結果，不要前言。

=== 趨勢原始資料 ===
{trends_text}
"""


def scrape_trends() -> str:
    from rb_upload import get_driver
    driver = get_driver()
    try:
        driver.get(TRENDS_URL)
        time.sleep(8)
        return driver.execute_script("return document.body.innerText;")
    finally:
        driver.quit()


def run_curation(trends_text: str) -> str:
    prompt = CURATION_PROMPT.format(trends_text=trends_text[:4000])
    result = subprocess.run(
        ["/home/tses89214/.local/bin/claude", "-p", prompt,
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
    trends_text = scrape_trends()
    ideas = run_curation(trends_text)
    send_telegram(f"今日 Pinterest Trends 點子：\n\n{ideas}")
    print(ideas)
    print("已送出")


if __name__ == "__main__":
    main()
