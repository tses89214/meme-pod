#!/usr/bin/env python3
"""
bot_mailbox_check.py — 讀 bot-mailbox 新訊息
==============================================
規則更新 2026-09-07（見 ~/.claude/bot-mailbox/README.md）：
meme-pod 不是交易類專案，沒有「真錢下單」這條線要顧，所以放寬到底：
點名 meme-pod 的訊息（純問資訊或要求做有副作用的事，例如改自己專案的
資料檔/cron/設定/寫筆記）都交給隔離的 `claude -p`（明確排除 telegram
MCP plugin，理由同 quote_weekly.py，2026-08-05 `claude mcp list` 弄斷
TG 連線的教訓；`--dangerously-skip-permissions` 讓它能真的動手做，
cwd 固定在本專案目錄）自主判斷並執行，完成後把做了什麼回報進
chat.jsonl。只有「看不懂/不是在問 meme-pod 自己的事」才不回覆
（NO_REPLY），一律轉發通知給使用者確認做了什麼。

轉發 Telegram 通知這步維持純腳本轉發（不需要模型判斷）。
用法（給 cron 用）：python3 bot_mailbox_check.py
"""

import json
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).parent
TELEGRAM_ENV = Path.home() / ".claude/channels/telegram/.env"
CHAT_ID = "1210712482"
MAILBOX_SCRIPT = BASE_DIR / "scripts/bot_mailbox.sh"
SELF = "meme-pod"

PROJECT_CONTEXT = (BASE_DIR / ".claude/PROGRESS.md").read_text(encoding="utf-8")

CLASSIFY_PROMPT = """你是 meme-pod 專案的 bot，收到 bot-mailbox 上別的 bot 傳來的訊息（點名給你）。
你有這個專案目錄（cwd）的完整檔案/指令權限，可以自主判斷並實際執行：
- 純資訊性問題（狀態/路徑/頻率/有沒有做某件事）→ 直接回答。
- 要求做有副作用的事，只要是「meme-pod 自己專案」範圍內的（更新自己的資料檔、裝/改
  自己的 cron、改自己的設定、寫筆記等）→ 可以自主動手做，不用等人在終端機確認。
- meme-pod 沒有任何會動用真錢的操作，不適用「真錢下單」那條限制，這裡不用考慮。
- 如果訊息看不懂、答不出來、或根本不是在問/要求 meme-pod 自己的事 → 只回覆恰好這個字串：NO_REPLY

專案背景（PROGRESS.md）：
{context}

收到的訊息：
{message}

如果你回答了問題或執行了動作，輸出一句簡短的結果摘要（做了什麼/答案是什麼，不要加前綴/引號），
讓對方跟轉發給使用者的通知都看得懂結果。不行就只輸出 NO_REPLY。"""


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


def mailbox_send(to: str, message: str):
    subprocess.run([str(MAILBOX_SCRIPT), "send", to, message], check=True)


def try_autoreply(from_bot: str, message: str) -> str | None:
    prompt = CLASSIFY_PROMPT.format(context=PROJECT_CONTEXT, message=message)
    result = subprocess.run(
        [
            str(Path.home() / ".local/bin/claude"), "-p", prompt,
            "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
            "--dangerously-skip-permissions",
        ],
        capture_output=True, text=True, timeout=300, cwd=BASE_DIR,
    )
    reply = result.stdout.strip()
    if not reply or reply == "NO_REPLY":
        return None
    return reply


def main():
    result = subprocess.run(
        [str(MAILBOX_SCRIPT), "read"],
        capture_output=True, text=True, check=True,
    )
    lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
    if not lines or lines == ["(no messages yet)"]:
        return

    notify_lines = []
    for line in lines:
        notify_lines.append(line)
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("to") == SELF:  # 只自主回直接點名的訊息，broadcast 不回
            reply = try_autoreply(msg.get("from", "?"), msg.get("message", ""))
            if reply:
                mailbox_send(msg["from"], reply)
                notify_lines.append(f"  -> 已自動回覆: {reply}")

    send_telegram("bot-mailbox 有新訊息：\n\n" + "\n".join(notify_lines))


if __name__ == "__main__":
    main()
