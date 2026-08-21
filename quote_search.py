#!/usr/bin/env python3
"""
quote_search.py — 用 Tavily 搜短句語錄候選（給梗圖 T 恤選題材用）
====================================================================
只做搜尋這一步（deterministic，不用模型判斷）。挑選哪些適合印上衣服、
怎麼排版（斷行/強調哪個字），是需要判斷的工作，交給呼叫這支腳本的人
或 Claude 做，不在這支腳本裡自動決定。

用法：
  python quote_search.py                          # 跑預設關鍵字組合
  python quote_search.py "自訂關鍵字" "另一個關鍵字"
"""

import random
import sys
import json
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"

# 依現有 7 個 Redbubble collection ＋ 客群輪廓分類，每類都給搜尋跟論壇來源兩種
# query，pick_queries() 會跨類別抽，比單一大池子隨機抽更不容易同類題材抽到重複。
QUERY_THEMES = {
    "漢字/Bilingual": [
        "funny chinese english bilingual pun quotes short",
        "site:reddit.com funny chinese english wordplay jokes",
    ],
    "Adult Class System / adulting": [
        "short funny adulting struggles quotes",
        "site:reddit.com adulting is hard funny quotes",
    ],
    "Life.exe Has Stopped Working / tech-life crash": [
        "funny brain.exe crashed life glitch quotes short",
        "site:reddit.com funny short quotes about burnout tired life",
    ],
    "Train Hard. Repeat. / gym": [
        "short gym fitness motivational sarcastic quotes",
        "site:reddit.com r/gym funny short motivational quotes",
    ],
    "Dark Tech humor / programmer": [
        "short programmer developer tech humor quotes",
        "site:reddit.com r/ProgrammerHumor short funny quotes",
    ],
    "Dad Jokes": [
        "short dad jokes puns funny for t-shirts",
        "site:reddit.com r/dadjokes short funny puns",
    ],
    "Paw Prints & Puns / pets": [
        "short funny pet owner dog cat puns quotes for t-shirts",
        "site:reddit.com funny dog cat owner puns short",
    ],
    "上班族/辦公室": [
        "short witty office work humor quotes",
        "site:reddit.com r/antiwork funny short quotes",
    ],
    "自嘲/毒舌通用": [
        "short savage sarcastic one-liner quotes for t-shirts",
        "creative witty roast insult comebacks short and clever not vulgar",
    ],
    "咖啡/沒睡飽": [
        "short coffee tired sarcastic quotes",
        "site:reddit.com funny short quotes about needing coffee",
    ],
    "遊戲玩家": [
        "short funny gamer quotes one-liner",
        "site:reddit.com r/gaming funny short quotes",
    ],
    "內向/社恐": [
        "short introvert relatable funny quotes",
        "site:reddit.com introvert funny short quotes",
    ],
    "正向/勵志": [
        "short positive motivational one-liner quotes for t-shirts",
        "underrated inspirational quotes short forum discussion",
    ],
}

# 舊名保留給其他程式相容用（例如手動 `python quote_search.py` 不帶參數時）
QUERY_POOL = [q for qs in QUERY_THEMES.values() for q in qs]
DEFAULT_QUERIES = QUERY_POOL


def pick_queries(n: int = 8) -> list[str]:
    """跨主題抽，每個主題最多抽 1 句，確保多樣性、不會同一主題重複問。"""
    themes = list(QUERY_THEMES.keys())
    random.shuffle(themes)
    picks = [random.choice(QUERY_THEMES[t]) for t in themes[:n]]
    random.shuffle(picks)
    return picks


def load_api_key() -> str:
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("TRAVILY_API_KEY="):
            return line.split("=", 1)[1]
    raise RuntimeError(f"{ENV_FILE} 裡沒有 TRAVILY_API_KEY")


def search_quotes(query: str, api_key: str) -> str:
    payload = json.dumps({
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": 6,
        "include_answer": "advanced",
    }).encode()
    req = urllib.request.Request(
        "https://api.tavily.com/search", data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data.get("answer", "")


def main():
    queries = sys.argv[1:] or pick_queries()
    api_key = load_api_key()
    for q in queries:
        print(f"=== {q} ===")
        print(search_quotes(q, api_key))
        print()


if __name__ == "__main__":
    main()
