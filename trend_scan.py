#!/usr/bin/env python3
"""
trend_scan.py — 合併 Pinterest Trends 掃描 + 語錄搜尋，一次 curation、一則 Telegram 通知
======================================================================
取代原本分開的 pinterest_trends_check.py + quote_weekly.py，理由：
兩支都是「抓素材 -> claude -p 判斷 -> 發一則 TG」的同一套流程，分兩支只是
重複 run_curation/send_telegram，且使用者一天收兩則類似通知沒必要。

給 cron 用，全程不用互動：
  1. Selenium 開 Pinterest Trends 頁面抓文字 + quote_search.py 用 Tavily 抓語錄候選
  2. 兩份素材一起丟給隔離的 `claude -p` 子行程做「趨勢/語錄 -> 設計點子」判斷
  3. 直接呼叫 Telegram Bot API 的 sendMessage 把結果傳給使用者

用法：
  python trend_scan.py
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

CURATION_PROMPT = """以下是今天的兩份原始素材，給梗圖 T 恤（Redbubble）選題材用。
我們賣的是搞笑/毒舌梗圖 T 恤，主題涵蓋上班族吐槽、遊戲人生等級、寵物雙關語、
中文雙語設計、健身勵志、生活小確幸等。

=== 素材一：Pinterest Trends 頁面原始文字（焦點趨勢、購物趨勢、搜尋趨勢、編輯精選）===
{trends_text}

=== 素材二：Tavily 搜到的英文語錄候選（跨搞怪/毒舌/正向/自嘲等類別）===
{quote_candidates}

規則：
- Pinterest 趨勢大多是時尚/美妝/居家類，不會直接對應，找出「能不能延伸出一句適合印
  T 恤的搞笑/雙關/自嘲文案」，找不到就跳過，不用湊數，最多給 5 個
- 語錄候選挑 5-8 句最適合印在 T 恤上的：要短、有記憶點、好笑或有共鳴，跳過老套陳腔
  濫調（例如 "Dream Big Work Hard" 這種到處都是的），每句給排版建議，格式是
  "*加粗字* /n 其餘文字"，用 /n 斷行（2-4 短行，把最有記憶點的字/詞加粗）
- 兩份素材分開列，各自標題，只輸出結果，不要前言

只輸出結果，不要前言。
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


def search_quote_candidates() -> str:
    import quote_search
    api_key = quote_search.load_api_key()
    parts = []
    for q in quote_search.pick_queries():
        parts.append(f"=== {q} ===\n{quote_search.search_quotes(q, api_key)}")
    return "\n\n".join(parts)


def run_curation(trends_text: str, quote_candidates: str) -> str:
    prompt = CURATION_PROMPT.format(
        trends_text=trends_text[:4000], quote_candidates=quote_candidates,
    )
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
    quote_candidates = search_quote_candidates()
    ideas = run_curation(trends_text, quote_candidates)
    send_telegram(f"今日 Pinterest Trends + 語錄搜尋點子：\n\n{ideas}")
    print(ideas)
    print("已送出")


if __name__ == "__main__":
    main()
