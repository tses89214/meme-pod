#!/usr/bin/env python3
"""
rb_upload.py — 自動填寫 Redbubble 上傳表單

使用方式：
  python rb_upload.py list                  # 列出所有待上傳設計
  python rb_upload.py upload <design_idx>   # 上傳第 N 個設計（從 1 開始）
  python rb_upload.py upload <design_idx> --submit   # 填完後自動送出

注意：
  - 需要在你自己的電腦上執行（需要有顯示器 / Chrome）
  - 使用 undetected-chromedriver 繞過 Cloudflare
  - 第一次執行會要求你手動登入 Redbubble（之後會記住 session）
  - 設計圖片在 ~/meme-pod/output/<name>/

依賴：
  pip install undetected-chromedriver selenium
"""

import sys
import json
import time
import re
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent
META_FILE = BASE_DIR / "upload_metadata.json"
OUTPUT_DIR = BASE_DIR / "output"
QUEUE_FILE = BASE_DIR / ".upload_queue.json"
PROFILE_DIR = BASE_DIR / ".rb_chrome_profile"

UPLOAD_URL = "https://www.redbubble.com/portfolio/images/new"


def load_queue():
    if not QUEUE_FILE.exists():
        return []
    return json.loads(QUEUE_FILE.read_text())


def load_metadata():
    if not META_FILE.exists():
        return []
    return json.loads(META_FILE.read_text())


def find_meta(text: str, metadata: list) -> dict:
    """依文字找 metadata 條目。"""
    for m in metadata:
        if m.get("text") == text:
            return m
    return None


def find_design_images(text: str) -> dict:
    """在 output/ 資料夾找設計圖片，回傳 {black: path, white: path}。"""
    clean = re.sub(r"[^\w\s\-]", "", text.replace("*", "").replace("/n", " ")).strip()[:40].strip()
    folder = OUTPUT_DIR / clean
    if not folder.exists():
        # 嘗試模糊比對
        candidates = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]
        for c in candidates:
            if clean[:10].lower() in c.name.lower():
                folder = c
                break
        else:
            return {}

    result = {}
    for f in folder.iterdir():
        n = f.name.lower()
        if "black" in n or "light" in n:
            result["black"] = str(f)
        elif "white" in n or "dark" in n:
            result["white"] = str(f)
    return result


def get_driver():
    import undetected_chromedriver as uc
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--window-size=1280,900")
    driver = uc.Chrome(options=options, headless=False)
    return driver


def wait_for(driver, selector, timeout=15):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )


def fill_field(driver, selector, text, clear=True):
    from selenium.webdriver.common.by import By
    el = driver.find_element(By.CSS_SELECTOR, selector)
    if clear:
        el.clear()
    el.send_keys(text)


def add_tags(driver, field_selector, tags: list):
    """在 React tag input 輸入標籤（每個按 Enter）。"""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    try:
        el = driver.find_element(By.CSS_SELECTOR, field_selector)
        el.click()
        for tag in tags:
            el.send_keys(tag)
            time.sleep(0.3)
            el.send_keys(Keys.RETURN)
            time.sleep(0.3)
    except Exception as e:
        print(f"  ⚠️  Tags {field_selector}: {e}")


def click_language_tab(driver, lang: str):
    """點擊語言 tab（en/de/fr/es）。"""
    from selenium.webdriver.common.by import By
    try:
        tab = driver.find_element(By.CSS_SELECTOR, f"label[for='language-tab-{lang}']")
        tab.click()
        time.sleep(0.5)
    except Exception as e:
        print(f"  ⚠️  Language tab {lang}: {e}")


def upload_image(driver, file_path: str):
    """上傳主圖片（不彈出 file dialog，直接 send_keys）。"""
    from selenium.webdriver.common.by import By
    inp = driver.find_element(By.CSS_SELECTOR, "#select-image-single")
    driver.execute_script("arguments[0].style.display = 'block';", inp)
    inp.send_keys(file_path)
    print(f"  ⬆️  上傳圖片: {Path(file_path).name}")
    # 等圖片處理
    time.sleep(5)


def enable_all_products(driver):
    """點擊 Enable All 按鈕。"""
    from selenium.webdriver.common.by import By
    try:
        btn = driver.find_element(By.CSS_SELECTOR, ".rb-button.enable-all")
        btn.click()
        time.sleep(1)
        print("  ✅  Enable All products")
    except Exception:
        print("  ℹ️  Enable All 按鈕找不到（可能已全啟用）")


def fill_design(driver, meta: dict, image_path: str, submit: bool = False):
    """主填表流程。"""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys

    driver.get(UPLOAD_URL)
    print(f"URL: {driver.current_url}")

    # 等表單載入
    try:
        wait_for(driver, "#work_title_en", timeout=20)
    except Exception:
        print("  ❌ 表單沒載入（可能被 Cloudflare 擋住），請先手動通過驗證")
        input("通過後按 Enter 繼續...")

    # 1. 上傳圖片
    upload_image(driver, image_path)

    # 2. 填寫各語言
    translations = meta.get("translations", {})
    for lang in ("en", "de", "fr", "es"):
        t = translations.get(lang, {})
        if not t:
            continue

        click_language_tab(driver, lang)

        # Title
        try:
            fill_field(driver, f"#work_title_{lang}", t.get("title", ""))
            print(f"  ✏️  [{lang}] title: {t.get('title', '')}")
        except Exception as e:
            print(f"  ⚠️  title_{lang}: {e}")

        # Description
        try:
            fill_field(driver, f"#work_description_{lang}", t.get("description", ""))
            print(f"  ✏️  [{lang}] description: OK")
        except Exception as e:
            print(f"  ⚠️  description_{lang}: {e}")

        # Tags
        tags = t.get("tags", [])
        if tags:
            add_tags(driver, f"#work_tag_field_{lang}", tags)
            print(f"  🏷️  [{lang}] tags: {', '.join(tags)}")

    # 3. Enable all products
    enable_all_products(driver)

    # 4. 截圖確認
    screenshot = BASE_DIR / "_rb_preview.png"
    driver.save_screenshot(str(screenshot))
    print(f"  📸 截圖: {screenshot}")

    # 5. 送出
    if submit:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "#submit-work")
            btn.click()
            print("  🚀 已送出！等待結果...")
            time.sleep(5)
            print(f"  URL: {driver.current_url}")
            driver.save_screenshot(str(screenshot))
        except Exception as e:
            print(f"  ❌ 送出失敗: {e}")
    else:
        print("\n  ℹ️  未自動送出。確認內容後，加 --submit 重跑，或手動點按鈕。")


def cmd_list():
    queue = load_queue()
    metadata = load_metadata()
    print(f"{'#':>3}  {'Text':<35} {'Font':<8} {'Images'}")
    print("-" * 70)
    for i, item in enumerate(queue, 1):
        text = item["text"]
        font = item["font"]
        imgs = find_design_images(text)
        img_status = "✅" if imgs else "❌ (run organize_designs.py)"
        display = text.replace("/n", "↵")[:33]
        print(f"{i:>3}  {display:<35} {font:<8} {img_status}")


def cmd_upload(idx: int, submit: bool):
    queue = load_queue()
    metadata = load_metadata()

    if idx < 1 or idx > len(queue):
        print(f"❌ 無效的索引 {idx}，範圍 1-{len(queue)}")
        sys.exit(1)

    item = queue[idx - 1]
    text = item["text"]
    meta = find_meta(text, metadata)

    if not meta:
        print(f"❌ 找不到 metadata: {text}")
        sys.exit(1)

    imgs = find_design_images(text)
    if not imgs:
        print(f"❌ 找不到設計圖片，請先執行 python organize_designs.py")
        sys.exit(1)

    # 優先用 black（for light shirts）
    image_path = imgs.get("black") or list(imgs.values())[0]

    print(f"\n🎨 設計: {text}")
    print(f"🖼️  圖片: {Path(image_path).name}")
    print(f"🔤 字體: {meta.get('font', '').upper()}\n")

    driver = get_driver()
    try:
        # 先導向首頁，讓使用者確認已登入
        driver.get("https://www.redbubble.com")
        time.sleep(2)
        print("請確認已登入 Redbubble（瀏覽器視窗已開啟）")
        print("如果未登入，請手動登入後按 Enter...")
        input("按 Enter 開始填表...")

        fill_design(driver, meta, image_path, submit=submit)

        if not submit:
            input("\n確認表單後按 Enter 關閉瀏覽器...")
    finally:
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Redbubble 自動填表工具")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list", help="列出所有待上傳設計")

    up = sub.add_parser("upload", help="填寫上傳表單")
    up.add_argument("idx", type=int, help="設計編號（從 list 查詢）")
    up.add_argument("--submit", action="store_true", help="自動送出表單")

    args = parser.parse_args()

    if args.cmd == "list":
        cmd_list()
    elif args.cmd == "upload":
        cmd_upload(args.idx, args.submit)
    else:
        parser.print_help()
