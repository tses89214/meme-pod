#!/usr/bin/env python3
"""
upload_session.py — 上傳上次 /meme 指令生成的設計（3個版本）
語法：
  python upload_session.py 1        # 上傳第 1 組（Anton）的 light+dark+transparent
  python upload_session.py 2        # 上傳第 2 組（Bebas）
"""

import sys
import json
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / ".last_meme_session.json"
LOG_FILE = BASE_DIR / "uploaded_log.json"

RB_EMAIL = os.environ.get("RB_EMAIL", "")
RB_PASSWORD = os.environ.get("RB_PASSWORD", "")

DEFAULT_TAGS = [
    "funny", "meme", "humor", "gift", "sarcastic",
    "relatable", "trending", "internet", "viral", "quote"
]


def load_session() -> dict:
    with open(SESSION_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_log() -> dict:
    if LOG_FILE.exists():
        with open(LOG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"uploaded": [], "details": []}


def mark_uploaded(filename: str, title: str):
    log = load_log()
    if filename not in log["uploaded"]:
        log["uploaded"].append(filename)
    if "details" not in log:
        log["details"] = []
    import datetime
    log["details"].append({
        "file": filename,
        "title": title,
        "uploaded_at": datetime.datetime.now().isoformat()
    })
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def login(page, email: str, password: str):
    print("🔐 登入 Redbubble...")
    page.goto("https://www.redbubble.com/auth/login", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    print(f"  頁面標題: {page.title()}")

    email_input = page.locator('input[name="usernameOrEmail"]')
    email_input.wait_for(timeout=10000)
    email_input.fill(email)

    page.locator('input[name="password"]').fill(password)
    page.wait_for_timeout(500)
    page.locator('input[type="submit"]').click()

    try:
        page.wait_for_url(lambda url: "auth/login" not in url, timeout=15000)
    except Exception:
        error_text = ""
        try:
            for sel in [".error", ".alert", "[class*='error']", "[class*='Error']"]:
                el = page.locator(sel).first
                if el.count() > 0:
                    error_text = el.inner_text()[:200]
                    break
        except Exception:
            pass
        raise RuntimeError(
            f"❌ 登入失敗（當前 URL: {page.url}）"
            + (f"\n   錯誤訊息: {error_text}" if error_text else "")
        )

    print(f"✅ 登入成功（跳轉到: {page.url}）")


def upload_one(page, image_path: Path, title: str, tags: list[str]):
    print(f"\n📤 上傳：{title}")
    print(f"   檔案：{image_path.name}")

    page.goto("https://www.redbubble.com/portfolio/images/new", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    print(f"  上傳頁面標題: {page.title()}")

    # 上傳圖檔
    print("  ⏳ 上傳圖片...")
    file_input = page.locator('input[type="file"]').first
    file_input.set_input_files(str(image_path))
    page.wait_for_timeout(12000)

    # 標題
    for sel in ['input[name="title"]', 'input[placeholder*="itle" i]', 'input[placeholder*="name" i]']:
        inp = page.locator(sel).first
        if inp.count() > 0:
            inp.fill(title[:60])
            break

    # 標籤
    for tag in tags:
        try:
            tag_field = page.locator('input[name="tag"], input[placeholder*="ag" i]').first
            tag_field.fill(tag)
            tag_field.press("Enter")
            page.wait_for_timeout(400)
        except Exception:
            pass

    # 儲存
    save_btn = page.locator(
        'button:has-text("Save Work"), button:has-text("Save"), input[type="submit"]'
    ).last
    save_btn.click()
    page.wait_for_load_state("networkidle", timeout=20000)
    page.wait_for_timeout(2000)
    print(f"  ✅ 完成：{title}")


def main():
    if not RB_EMAIL or not RB_PASSWORD:
        print("❌ 請設定環境變數：RB_EMAIL, RB_PASSWORD")
        sys.exit(1)

    if not SESSION_FILE.exists():
        print("❌ 找不到 .last_meme_session.json，請先執行 quick_meme.py")
        sys.exit(1)

    session = load_session()
    font_idx = int(sys.argv[1]) - 1 if len(sys.argv) > 1 else 0
    sets = session["sets"]

    if font_idx < 0 or font_idx >= len(sets):
        print(f"❌ 無效編號，可用 1~{len(sets)}")
        sys.exit(1)

    chosen = sets[font_idx]
    font_name = session["fonts"][font_idx].upper()
    text = session["text"].replace("*", "").replace("/n", "").strip()
    title_base = text[:50].title()

    # 準備 3 個版本
    uploads = [
        (Path(chosen["transparent"]), f"{title_base} — Transparent", DEFAULT_TAGS + ["tshirt"]),
        (Path(chosen["light"]),       f"{title_base} — White",       DEFAULT_TAGS + ["white shirt"]),
        (Path(chosen["dark"]),        f"{title_base} — Black",       DEFAULT_TAGS + ["black shirt"]),
    ]

    print(f"\n🎨 字體: {font_name}")
    print(f"📝 文字: {text}")
    print(f"📦 準備上傳 3 個版本...\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        SESSION_STATE = BASE_DIR / "rb_session.json"
        ctx_kwargs = dict(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        if SESSION_STATE.exists():
            print(f"🍪 使用已儲存的 session：{SESSION_STATE}")
            ctx_kwargs["storage_state"] = str(SESSION_STATE)

        context = browser.new_context(**ctx_kwargs)
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = context.new_page()

            if not SESSION_STATE.exists():
            try:
                login(page, RB_EMAIL, RB_PASSWORD)
            except RuntimeError as e:
                print(e)
                browser.close()
                sys.exit(1)
        else:
            # 驗證 session 是否有效
            page.goto("https://www.redbubble.com", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            if "login" in page.url or "auth" in page.url:
                print("⚠️  Session 已過期，改用帳號密碼登入...")
                try:
                    login(page, RB_EMAIL, RB_PASSWORD)
                except RuntimeError as e:
                    print(e)
                    browser.close()
                    sys.exit(1)
            else:
                print(f"✅ Session 有效（{page.url}）")

        success = 0
        for img_path, title, tags in uploads:
            if not img_path.exists():
                print(f"  ⚠️  找不到檔案：{img_path}")
                continue
            try:
                upload_one(page, img_path, title, tags)
                mark_uploaded(img_path.name, title)
                success += 1
                time.sleep(3)
            except Exception as e:
                print(f"  ⚠️  上傳失敗：{e}")

        browser.close()

    print(f"\n{'═'*50}")
    print(f"✅ 完成！成功上傳 {success}/3 個版本")
    print(f"{'═'*50}")


if __name__ == "__main__":
    main()
