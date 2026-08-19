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
# 複製範本：黑底範本配白字圖，白底範本配黑字圖（見 DECISIONS.md 2026-08-04 配對邏輯）
BLACK_TEMPLATE_DUP_URL = "https://www.redbubble.com/portfolio/images/179795066-tbd-totally-been-delayed-funny-work-meme-tee/duplicate"
WHITE_TEMPLATE_DUP_URL = "https://www.redbubble.com/portfolio/images/179795087-tbd-totally-been-delayed-funny-work-meme-tee/duplicate"


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
    driver = uc.Chrome(
        options=options,
        headless=False,
        browser_executable_path="/usr/bin/chromium",
        driver_executable_path=str(Path.home() / ".local/share/undetected_chromedriver/chromedriver_arm64"),
    )
    # Redbubble 換圖後頁面會忙很久，單一指令可能卡超過 selenium 預設 120 秒的 read timeout
    driver.command_executor.set_timeout(600)
    return driver


def wait_for(driver, selector, timeout=15):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )


LANGUAGE_TAB_XPATH = {
    "de": '//*[@id="add-new-work"]/div/div[2]/div/div/label[2]/h3',
    "fr": '//*[@id="add-new-work"]/div/div[2]/div/div/label[3]/h3',
    "es": '//*[@id="add-new-work"]/div/div[2]/div/div/label[4]/h3',
}


def clear_and_input(driver, el, text):
    """React 控制的欄位，plain .clear() 常常清不乾淨，用 JS 清空 + 全選刪除 + 硬送 30 次 Backspace 保底
    (清空這段用真的按鍵事件才可靠，不能省)。清完後用原生 setter + dispatch input/change 事件直接灌值，
    比一個字一個字 send_keys 快很多，且一樣會被 React 偵測到。"""
    from selenium.webdriver.common.keys import Keys
    el.click()
    driver.execute_script("arguments[0].value = ''", el)
    el.send_keys(Keys.CONTROL, "a")
    el.send_keys(Keys.BACKSPACE)
    for _ in range(30):
        el.send_keys(Keys.BACKSPACE)
    driver.execute_script("""
        const el = arguments[0], value = arguments[1];
        const proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
        Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value);
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
    """, el, text)


def click_language_tab(driver, lang: str):
    """點擊語言 tab（en 是預設 tab 不用點）。"""
    from selenium.webdriver.common.by import By
    if lang not in LANGUAGE_TAB_XPATH:
        return
    try:
        driver.find_element(By.XPATH, LANGUAGE_TAB_XPATH[lang]).click()
        time.sleep(0.5)
    except Exception as e:
        print(f"  ⚠️  Language tab {lang}: {e}")


def upload_image(driver, file_path: str, selector: str = "#select-image-single"):
    """上傳主圖片（不彈出 file dialog，直接 send_keys）。
    New Work 頁面用 #select-image-single；duplicate 頁面的「Replace all images」
    對應 #select-image-base（使用者實測 DOM 檢查器確認）。"""
    from selenium.webdriver.common.by import By
    inp = driver.find_element(By.CSS_SELECTOR, selector)
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


def list_collections(driver) -> list:
    """列出目前頁面上可選的 collections（name + checkbox id + 是否已勾選）。
    只能在 duplicate/New Work 表單頁面呼叫（collection 勾選框是這個表單的一部分）。"""
    return driver.execute_script("""
        return Array.from(document.querySelectorAll('input[id^="work_group_ids_"]')).map(el => {
            const label = el.closest('label');
            return {name: label ? label.getAttribute('title') : null, id: el.id, checked: el.checked};
        });
    """)


def select_collection(driver, collection_name: str):
    """勾選指定名稱的 collection，取消勾選其他所有 collection（不新增不存在的名稱，找不到就跳過）。
    部分舊 collection 建立時名稱裡的 & 被存成字面上的 &amp;，比對時要正規化避免漏配。"""
    from selenium.webdriver.common.by import By
    norm = lambda s: s.replace("&amp;", "&") if s else s
    collections = list_collections(driver)
    match = next((c for c in collections if norm(c["name"]) == norm(collection_name)), None)
    if not match:
        names = [c["name"] for c in collections]
        print(f"  ⚠️  找不到 collection「{collection_name}」，現有：{names}，略過")
        return
    for c in collections:
        el = driver.find_element(By.ID, c["id"])
        should_check = norm(c["name"]) == norm(collection_name)
        if el.is_selected() != should_check:
            el.click()
    print(f"  📁 Collection: {collection_name}")


def fill_design(driver, meta: dict, image_path: str, submit: bool = False, target_url: str = None, collection: str = None):
    """主填表流程。target_url 預設是空白 New Work，但依規定新品要從既有設計 duplicate 出來，
    呼叫時應該傳 black/white 範本的 /duplicate 網址。collection 給的話會取代範本原本的 collection 勾選。"""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys

    driver.get(target_url or UPLOAD_URL)
    print(f"URL: {driver.current_url}")

    # 等表單載入（Cloudflare 驗證可能要等 1-2 分鐘，會自動過，不用手動介入）
    try:
        wait_for(driver, "#work_title_en", timeout=150)
    except Exception:
        raise RuntimeError("表單沒載入（Cloudflare 驗證超過 150 秒仍未過），請確認 profile 是否過期")

    # 1. 上傳圖片（duplicate 頁用 base 的換圖 input，New Work 頁用 single）
    image_selector = "#select-image-base" if target_url else "#select-image-single"
    upload_image(driver, image_path, selector=image_selector)

    # 2. 填寫各語言
    translations = meta.get("translations", {})
    for lang in ("en", "de", "fr", "es"):
        t = translations.get(lang, {})
        if not t:
            continue

        click_language_tab(driver, lang)

        # Title
        try:
            el = driver.find_element(By.CSS_SELECTOR, f"#work_title_{lang}")
            clear_and_input(driver, el, t.get("title", ""))
            print(f"  ✏️  [{lang}] title: {t.get('title', '')}")
        except Exception as e:
            print(f"  ⚠️  title_{lang}: {e}")

        # Main tag
        try:
            el = driver.find_element(By.CSS_SELECTOR, f"#main-tag-{lang}")
            el.click()
            for _ in range(30):
                el.send_keys(Keys.BACKSPACE)
            el.send_keys(t.get("main_tag", ""))
            el.send_keys(Keys.ENTER)
            print(f"  🏷️  [{lang}] main_tag: {t.get('main_tag', '')}")
        except Exception as e:
            print(f"  ⚠️  main_tag_{lang}: {e}")

        # Supporting tags
        try:
            tags = t.get("tags", [])
            el = driver.find_element(By.CSS_SELECTOR, f"#supporting-tags-{lang}")
            el.click()
            for _ in range(30):
                el.send_keys(Keys.BACKSPACE)
            el.send_keys(",".join(tags))
            el.send_keys(Keys.ENTER)
            el.send_keys(Keys.ESCAPE)
            print(f"  🏷️  [{lang}] tags: {', '.join(tags)}")
        except Exception as e:
            print(f"  ⚠️  supporting_tags_{lang}: {e}")

        # Description
        try:
            el = driver.find_element(By.CSS_SELECTOR, f"#work_description_{lang}")
            clear_and_input(driver, el, t.get("description", ""))
            print(f"  ✏️  [{lang}] description: OK")
        except Exception as e:
            print(f"  ⚠️  description_{lang}: {e}")

    # 2b. Collection（給了才動，不給就保留範本原本勾的）
    if collection:
        try:
            select_collection(driver, collection)
        except Exception as e:
            print(f"  ⚠️  collection: {e}")

    # 3. Enable all products
    enable_all_products(driver)

    # 3b. 版權確認框（Save Work 送出前必須勾）
    try:
        checkbox = driver.find_element(By.CSS_SELECTOR, "#rightsDeclaration")
        if not checkbox.is_selected():
            checkbox.click()
        print("  ☑️  已勾選版權確認")
    except Exception as e:
        print(f"  ⚠️  rightsDeclaration: {e}")

    # 4. 截圖確認
    screenshot = BASE_DIR / "_rb_preview.png"
    driver.save_screenshot(str(screenshot))
    print(f"  📸 截圖: {screenshot}")

    # 5. 送出
    product_url = None
    if submit:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "#submit-work")
            btn.click()
            print("  🚀 已送出！等待結果...")
            time.sleep(5)
            print(f"  URL: {driver.current_url}")
            driver.save_screenshot(str(screenshot))
            # 送出後會落在 /studio/promote/<id> 確認頁，"View" 連結的 href 是公開商品網址
            try:
                view_links = driver.execute_script("""
                    return Array.from(document.querySelectorAll('a')).filter(a => a.innerText.trim() === 'View').map(a => a.href);
                """)
                if view_links:
                    product_url = view_links[0].split("?")[0]
                    print(f"  🔗 商品網址: {product_url}")
            except Exception as e:
                print(f"  ⚠️  抓不到商品網址: {e}")
        except Exception as e:
            print(f"  ❌ 送出失敗: {e}")
    else:
        print("\n  ℹ️  未自動送出。確認內容後，加 --submit 重跑，或手動點按鈕。")
    return product_url


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

    sub.add_parser("collections", help="列出目前可選的 collections（開一次範本頁查詢）")

    args = parser.parse_args()

    if args.cmd == "list":
        cmd_list()
    elif args.cmd == "upload":
        cmd_upload(args.idx, args.submit)
    elif args.cmd == "collections":
        driver = get_driver()
        try:
            driver.get(BLACK_TEMPLATE_DUP_URL)
            wait_for(driver, "#work_title_en", timeout=150)
            for c in list_collections(driver):
                mark = "✅" if c["checked"] else "  "
                print(f"{mark} {c['name']}")
        finally:
            driver.quit()
    else:
        parser.print_help()
