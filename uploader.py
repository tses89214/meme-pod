#!/usr/bin/env python3
"""
uploader.py — Redbubble 自動上架
==================================
用 Playwright 自動登入 Redbubble 並上傳 T 恤設計（透明背景版）。
內建去重機制，不會重複上傳已上架設計。

使用方式：
  python uploader.py output/xxx_transparent.png --title "AC Levels" --tags "funny,meme"
  python uploader.py --batch output/          # 批量上傳整個資料夾
"""

import os
import sys
import json
import time
import argparse
import datetime
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

RB_EMAIL = os.environ.get("RB_EMAIL", "")
RB_PASSWORD = os.environ.get("RB_PASSWORD", "")

BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "uploaded_log.json"

DEFAULT_TAGS = [
    "funny", "meme", "humor", "gift", "sarcastic",
    "relatable", "trending", "internet", "viral", "quote"
]


# ═══════════════════════════════════════════════════════════
# 去重 Log
# ═══════════════════════════════════════════════════════════

def load_log() -> dict:
    if LOG_FILE.exists():
        with open(LOG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"uploaded": []}


def save_log(log: dict):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def is_uploaded(filename: str) -> bool:
    log = load_log()
    return filename in log["uploaded"]


def mark_uploaded(filename: str, title: str):
    log = load_log()
    log["uploaded"].append(filename)
    if "details" not in log:
        log["details"] = []
    log["details"].append({
        "file": filename,
        "title": title,
        "uploaded_at": datetime.datetime.now().isoformat()
    })
    save_log(log)


# ═══════════════════════════════════════════════════════════
# 標題/標籤生成
# ═══════════════════════════════════════════════════════════

def infer_title(image_path: Path) -> str:
    """從檔名推斷標題。格式：20260323_123538_some_concept_minimal.png"""
    name = image_path.stem
    # 去掉透明版後綴
    name = name.replace("_transparent", "")
    parts = name.split("_")
    # 去掉時間戳（前2段）和風格名（最後1段）
    if len(parts) > 3:
        parts = parts[2:-1]
    return " ".join(parts).title()


def smart_tags(title: str, base_tags: list[str]) -> list[str]:
    """根據標題內容動態補充標籤。"""
    tags = list(base_tags)
    t = title.lower()
    if any(w in t for w in ["work", "boss", "office", "job", "meeting"]):
        tags += ["work humor", "office", "coworker gift"]
    if any(w in t for w in ["brain", "sleep", "3am", "tired", "monday"]):
        tags += ["sleep humor", "introvert", "monday mood"]
    if any(w in t for w in ["mom", "dad", "parent", "family", "kid"]):
        tags += ["parenting", "parent humor", "family"]
    if any(w in t for w in ["gaming", "gamer", "game", "level"]):
        tags += ["gamer", "gaming humor", "geek"]
    if any(w in t for w in ["ac", "temperature", "cold", "hot", "weather"]):
        tags += ["summer", "weather humor", "temperature"]
    # 去重，最多 10 個
    seen = set()
    unique = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique.append(tag)
    return unique[:10]


# ═══════════════════════════════════════════════════════════
# Playwright 操作
# ═══════════════════════════════════════════════════════════

def login(page, email: str, password: str):
    print("🔐 登入 Redbubble...")
    page.goto("https://www.redbubble.com/auth/login", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    print(f"  頁面標題: {page.title()}")

    # 填入帳號（使用正確的 name 屬性）
    email_input = page.locator('input[name="usernameOrEmail"]')
    email_input.wait_for(timeout=10000)
    email_input.fill(email)

    page.locator('input[name="password"]').fill(password)
    page.wait_for_timeout(500)

    # 點擊送出
    page.locator('input[type="submit"]').click()

    # 等待頁面跳轉
    try:
        page.wait_for_url(lambda url: "auth/login" not in url, timeout=15000)
    except Exception:
        # 取得錯誤訊息
        error_text = ""
        try:
            error_el = page.locator(".error, .alert, [class*='error'], [class*='alert']").first
            if error_el.count() > 0:
                error_text = error_el.inner_text()
        except Exception:
            pass
        raise RuntimeError(f"❌ 登入失敗（URL: {page.url}）{' — ' + error_text if error_text else ''}")

    print("✅ 登入成功")


def upload_design(page, image_path: Path, title: str, tags: list[str]):
    print(f"\n📤 上傳：{title}")
    page.goto("https://www.redbubble.com/portfolio/images/new",
              wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # 上傳圖檔
    print("  ⏳ 上傳圖片...")
    file_input = page.locator('input[type="file"]').first
    file_input.set_input_files(str(image_path))
    page.wait_for_timeout(10000)  # 等待圖片處理

    # 標題
    title_input = page.locator('input[name="title"]').first
    if title_input.count() == 0:
        title_input = page.locator('input[placeholder*="itle" i]').first
    title_input.fill(title[:60])

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
    save_btn = page.locator('button:has-text("Save Work"), button:has-text("Save"),  input[type="submit"]').last
    save_btn.click()
    page.wait_for_load_state("networkidle", timeout=20000)
    page.wait_for_timeout(2000)
    print(f"  ✅ 上架完成：{title}")


# ═══════════════════════════════════════════════════════════
# 批量上傳
# ═══════════════════════════════════════════════════════════

def pick_files_to_upload(folder: Path) -> list[Path]:
    """
    從 output 資料夾挑選要上傳的檔案：
    - 優先選透明背景版（_transparent.png）
    - 跳過已上傳的
    - 每個概念只上傳一個風格（避免洗版）
    """
    all_pngs = sorted(folder.glob("*_transparent.png"))
    seen_concepts = set()
    to_upload = []

    for p in all_pngs:
        if is_uploaded(p.name):
            continue
        # 取概念 key（去掉時間戳+風格）
        parts = p.stem.replace("_transparent", "").split("_")
        concept = "_".join(parts[2:-1]) if len(parts) > 3 else p.stem
        if concept not in seen_concepts:
            seen_concepts.add(concept)
            to_upload.append(p)

    return to_upload


def batch_upload(folder: Path, base_tags: list[str] = DEFAULT_TAGS) -> int:
    to_upload = pick_files_to_upload(folder)
    if not to_upload:
        print("✅ 沒有新設計需要上傳")
        return 0

    print(f"📦 準備上架 {len(to_upload)} 件新商品")

    success = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()

        try:
            login(page, RB_EMAIL, RB_PASSWORD)
        except RuntimeError as e:
            print(e)
            browser.close()
            return 0

        for img in to_upload:
            title = infer_title(img)
            tags = smart_tags(title, base_tags)
            try:
                upload_design(page, img, title, tags)
                mark_uploaded(img.name, title)
                success += 1
                time.sleep(3)
            except Exception as e:
                print(f"  ⚠️  失敗：{e}")

        browser.close()

    print(f"\n✅ 成功上架 {success}/{len(to_upload)} 件")
    return success


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not RB_EMAIL or not RB_PASSWORD:
        print("❌ 請設定環境變數：RB_EMAIL, RB_PASSWORD")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Redbubble 自動上架")
    parser.add_argument("image", nargs="?", type=Path, help="單一 PNG 路徑")
    parser.add_argument("--title", help="商品標題")
    parser.add_argument("--tags", help="標籤，逗號分隔")
    parser.add_argument("--batch", type=Path, metavar="FOLDER", help="批量上傳資料夾")
    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else DEFAULT_TAGS

    if args.batch:
        batch_upload(args.batch, tags)
    elif args.image:
        title = args.title or infer_title(args.image)
        tags = smart_tags(title, tags)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_context().new_page()
            login(page, RB_EMAIL, RB_PASSWORD)
            upload_design(page, args.image, title, tags)
            mark_uploaded(args.image.name, title)
            browser.close()
    else:
        parser.print_help()
