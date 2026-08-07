#!/usr/bin/env python3
"""
bot_mailbox_check.py — 讀 bot-mailbox 新訊息，轉發給使用者，不自動回覆
====================================================================
meme-pod 加入 ~/.claude/bot-mailbox 這個跨 bot 通道時選擇「read+notify only」
模式（跟 usstock-bot 一樣）：純轉發給使用者看，不自動在 mailbox 上回話、
不自動採取行動——這支腳本本身是純轉發，不需要模型判斷，所以不用 claude -p，
也就完全不會碰到 telegram MCP plugin 那個雷（2026-08-05 的事故）。
真的需要回覆 mailbox 由使用者看過之後自己決定要不要叫我回。

用法（給 cron 用）：
  python3 bot_mailbox_check.py
"""

import subprocess
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).parent
TELEGRAM_ENV = Path.home() / ".claude/channels/telegram/.env"
CHAT_ID = "1210712482"
MAILBOX_SCRIPT = BASE_DIR / "scripts/bot_mailbox.sh"


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
    result = subprocess.run(
        [str(MAILBOX_SCRIPT), "read"],
        capture_output=True, text=True, check=True,
    )
    lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
    if not lines or lines == ["(no messages yet)"]:
        return

    send_telegram("bot-mailbox 有新訊息：\n\n" + "\n".join(lines))


if __name__ == "__main__":
    main()
