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

import sys
import json
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"

DEFAULT_QUERIES = [
    "short savage sarcastic one-liner quotes for t-shirts",
    "short funny quirky english quotes for t-shirts",
    "short positive motivational one-liner quotes for t-shirts",
    "funny self-deprecating relatable quotes short",
    "creative witty roast insult comebacks short and clever not vulgar",
    "short dad jokes puns funny for t-shirts",
    "short funny pet owner dog cat puns quotes for t-shirts",
]


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
    queries = sys.argv[1:] or DEFAULT_QUERIES
    api_key = load_api_key()
    for q in queries:
        print(f"=== {q} ===")
        print(search_quotes(q, api_key))
        print()


if __name__ == "__main__":
    main()
