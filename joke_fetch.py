#!/usr/bin/env python3
"""
joke_fetch.py — 從 API 抓英文笑話/雙關語，篩選適合印 T 恤的
"""
import requests, json, re

HEADERS = {"User-Agent": "meme-pod/1.0", "Accept": "application/json"}

def fetch_dad_jokes(n=20):
    jokes = []
    for _ in range(n):
        try:
            r = requests.get("https://icanhazdadjoke.com/", headers=HEADERS, timeout=5)
            j = r.json().get("joke", "")
            if j:
                jokes.append(("dad", j))
        except:
            pass
    return jokes

def fetch_puns(n=10):
    jokes = []
    try:
        r = requests.get(f"https://v2.jokeapi.dev/joke/Pun?amount={n}&type=single", timeout=5)
        data = r.json()
        for item in data.get("jokes", []):
            jokes.append(("pun", item.get("joke", "")))
    except:
        pass
    return jokes

def score(joke: str) -> int:
    s = 0
    words = len(joke.split())
    if 4 <= words <= 15: s += 3
    if words > 20: s -= 2
    # 問答型笑話不適合 T 恤（需要上下文）
    if joke.count("?") == 1 and joke.count("\n") == 0: s += 1
    if joke.count("?") > 1: s -= 1
    # 有 pun/wordplay 信號
    for kw in ["never", "always", "every", "just", "only", "still", "already"]:
        if kw in joke.lower(): s += 1
    # 太依賴情境
    for bad in ["he said", "she said", "they said", "wife", "husband", "doctor"]:
        if bad in joke.lower(): s -= 1
    return s

def main():
    jokes = fetch_dad_jokes(15) + fetch_puns(10)
    scored = sorted(set([(score(j), t, j) for t, j in jokes if j]), reverse=True)
    print(f"\n🎭 英文笑話/雙關語 Top 10（適合 T 恤）\n{'='*50}")
    seen = set()
    count = 0
    for sc, kind, joke in scored:
        if joke in seen: continue
        seen.add(joke)
        print(f"\n{count+1}. [{sc:+d}] ({kind})\n   {joke}")
        count += 1
        if count >= 10: break

if __name__ == "__main__":
    main()
