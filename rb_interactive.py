#!/usr/bin/env python3
"""
rb_interactive.py — 人機協作 Redbubble 上傳工具

使用方式：
  python rb_interactive.py screenshot       # 截圖當前狀態
  python rb_interactive.py goto <url>       # 導航到 URL
  python rb_interactive.py login <email> <password>  # 登入
  python rb_interactive.py click <selector> # 點擊元素
  python rb_interactive.py fill <selector> <text>    # 填寫輸入框
  python rb_interactive.py eval <js>        # 執行 JS
  python rb_interactive.py status           # 截圖 + 顯示當前 URL
"""

import sys
import json
import time
from pathlib import Path

STATE_FILE = Path("/tmp/.rb_state.json")
SCREENSHOT_FILE = Path("/tmp/rb_screenshot.png")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state))


def get_page():
    """啟動或恢復 Playwright session（使用持久 context）。"""
    from playwright.sync_api import sync_playwright
    return sync_playwright()


PERSISTENT_DIR = Path("/tmp/.rb_browser_data")

def run_cmd(cmd, args):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            str(PERSISTENT_DIR),
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
            viewport={"width": 1280, "height": 900},
        )
        page = browser.pages[0] if browser.pages else browser.new_page()

        if cmd == "goto":
            page.goto(args[0], wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            page.screenshot(path=str(SCREENSHOT_FILE), full_page=False)
            print(f"URL: {page.url}")
            print(f"Screenshot: {SCREENSHOT_FILE}")

        elif cmd in ("screenshot", "status"):
            page.screenshot(path=str(SCREENSHOT_FILE), full_page=False)
            print(f"URL: {page.url}")
            print(f"Screenshot: {SCREENSHOT_FILE}")

        elif cmd == "login":
            email, password = args[0], args[1]
            page.goto("https://www.redbubble.com/auth/login", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            page.screenshot(path=str(SCREENSHOT_FILE))
            print(f"Before login: {page.url}")

            # Try to fill login form
            try:
                page.fill('input[name="usernameOrEmail"]', email, timeout=5000)
                page.fill('input[name="password"]', password, timeout=5000)
                page.screenshot(path=str(SCREENSHOT_FILE))
                print("Filled credentials, screenshot saved")
                print(f"Screenshot: {SCREENSHOT_FILE}")
                print("WAIT_FOR_USER: 請確認截圖後告訴我是否要提交")
            except Exception as e:
                print(f"Error filling form: {e}")
                page.screenshot(path=str(SCREENSHOT_FILE))
                print(f"Screenshot: {SCREENSHOT_FILE}")

        elif cmd == "submit":
            try:
                page.click('input[type="submit"]', timeout=5000)
                time.sleep(4)
                page.screenshot(path=str(SCREENSHOT_FILE))
                print(f"URL: {page.url}")
                print(f"Screenshot: {SCREENSHOT_FILE}")
            except Exception as e:
                print(f"Error: {e}")
                page.screenshot(path=str(SCREENSHOT_FILE))
                print(f"Screenshot: {SCREENSHOT_FILE}")

        elif cmd == "click":
            try:
                page.click(args[0], timeout=5000)
                time.sleep(2)
                page.screenshot(path=str(SCREENSHOT_FILE))
                print(f"Clicked: {args[0]}")
                print(f"URL: {page.url}")
                print(f"Screenshot: {SCREENSHOT_FILE}")
            except Exception as e:
                print(f"Error clicking {args[0]}: {e}")
                page.screenshot(path=str(SCREENSHOT_FILE))
                print(f"Screenshot: {SCREENSHOT_FILE}")

        elif cmd == "fill":
            try:
                page.fill(args[0], args[1], timeout=5000)
                page.screenshot(path=str(SCREENSHOT_FILE))
                print(f"Filled {args[0]}")
                print(f"Screenshot: {SCREENSHOT_FILE}")
            except Exception as e:
                print(f"Error: {e}")
                page.screenshot(path=str(SCREENSHOT_FILE))

        elif cmd == "eval":
            result = page.evaluate(args[0])
            print(f"Result: {result}")
            page.screenshot(path=str(SCREENSHOT_FILE))
            print(f"Screenshot: {SCREENSHOT_FILE}")

        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]
    run_cmd(cmd, args)
