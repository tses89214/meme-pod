#!/usr/bin/env python3
"""
pinterest_upload.py — 自動發 Pinterest pin
=============================================
從已上架 Redbubble 的設計（upload_metadata.json 裡 uploaded=true 且有 redbubble_url、
pinned 不是 true 的），抓真實商品 mockup 照，自動建立並發布 Pinterest pin。

使用方式：
  python pinterest_upload.py list      # 列出還沒 pin 的設計
  python pinterest_upload.py batch     # 批次全部發完
  python pinterest_upload.py one <title 關鍵字>   # 只發一筆

依賴：跟 rb_upload.py 共用瀏覽器 profile/登入，見該檔案開頭說明。
"""

import sys
import json
import re
import time
import random
import argparse
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rb_upload import get_driver

BASE_DIR = Path(__file__).parent
META_FILE = BASE_DIR / "upload_metadata.json"
BOARD_NAME = "Funny Sarcastic Meme T-Shirts"
PIN_BUILDER_URL = "https://www.pinterest.com/pin-builder/"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def load_metadata() -> list:
    with open(META_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_metadata(metadata: list):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
        f.write("\n")


def update_metadata_field(text: str, **fields):
    """安全更新單一欄位：即用即讀最新檔案，只改這筆，立刻存檔。
    不要把整份 metadata 記在記憶體裡放好幾分鐘才存——這支腳本（尤其 daily 排程）
    跟其他同時在跑的流程（例如互動中新增設計）搶著存檔會互相蓋掉對方剛加的東西
    （2026-08-05 真的發生過，Focus 設計整條資料被排程跑的時候蓋掉，靠 git 救回來）。"""
    metadata = load_metadata()
    for item in metadata:
        if item.get("text") == text:
            item.update(fields)
            break
    save_metadata(metadata)


def pending_designs(metadata: list) -> list:
    return [
        m for m in metadata
        if m.get("uploaded") and m.get("redbubble_url") and not m.get("pinned")
    ]


MOCKUP_URL_RE = re.compile(
    r'"url":"(https:(?:\{\{%2F\}\}){2}[^"]*square_close_portrait[^"]*x1000[^"]*\.jpg)"'
)
OG_IMAGE_RE = re.compile(r'<meta[^>]*(?:property|name)="og:image"[^>]*content="([^"]+)"')
MOCKUP_HEX_RE = re.compile(r'([0-9a-fA-F]{6})(?::[0-9a-fA-F]+)?,front')
MOCKUP_DARK_NAME_RE = re.compile(r'(black|dark|charcoal|onyx|navy|graphite)', re.I)
MOCKUP_LIGHT_NAME_RE = re.compile(r'(white|light|cream|ivory|oatmeal|sand|natural)', re.I)


def _mockup_brightness(url: str) -> str:
    """回傳這張 mockup 底色是 'dark'、'light' 還是 'unknown'（無法判斷就保留，不篩掉）。"""
    m = MOCKUP_HEX_RE.search(url)
    if m:
        r, g, b = (int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        if lum < 100:
            return "dark"
        if lum > 180:
            return "light"
        return "unknown"
    if MOCKUP_DARK_NAME_RE.search(url):
        return "dark"
    if MOCKUP_LIGHT_NAME_RE.search(url):
        return "light"
    return "unknown"


def get_mockup_image(product_url: str, dest_dir: Path, ink: str = "black") -> Path:
    """公開商品頁不擋 Cloudflare，純 requests 就能抓，不用開瀏覽器。
    圖片網址藏在頁面內嵌的 JSON 裡（不是 <img> 標籤，是 client-side hydrate 用的資料），
    斜線被跳脫成 {{%2F}}，要還原。"""
    resp = requests.get(product_url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    html = resp.text

    matches = MOCKUP_URL_RE.findall(html)
    if matches:
        # 去重後隨機挑一張，不要每次都拿同一件（findall 順序在同一頁是固定的）
        candidates = list(dict.fromkeys(m.replace("{{%2F}}", "/") for m in matches))
        # 黑字要避開深色底（看不到黑字），白字要避開淺色底（看不到白字）
        avoid = "dark" if ink == "black" else "light"
        safe_candidates = [c for c in candidates if _mockup_brightness(c) != avoid]
        candidates = safe_candidates or candidates
    else:
        # 沒找到 mockup 就退回 og:image（純設計平面圖，比較差但至少有圖）
        og_match = OG_IMAGE_RE.search(html)
        if not og_match:
            raise RuntimeError(f"找不到任何圖片：{product_url}")
        candidates = [og_match.group(1)]

    img_url = random.choice(candidates)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / (img_url.split("/")[-1].split("?")[0])
    img_resp = requests.get(img_url, headers={"User-Agent": USER_AGENT}, timeout=30)
    img_resp.raise_for_status()
    dest.write_bytes(img_resp.content)
    return dest


def build_pin_copy(meta: dict) -> tuple[str, str]:
    """標題/描述，description 不能含 https://（Pinterest 會整篇拒絕）。
    有 pinterest_captions（5 種風格：搞笑/日記/直白/tag朋友/瘋癲）就隨機抽一個，
    這樣同一設計重複發文每次口吻都不同；沒有就退回舊的商品描述當備案。"""
    title = meta.get("title", "")[:100]
    captions = meta.get("pinterest_captions")
    caption = random.choice(captions) if captions else ""
    blurb = meta.get("description", "")
    description = " ".join(part for part in (caption, blurb) if part) or blurb
    tags = meta.get("tags") or []
    if tags:
        hashtags = " ".join(f"#{t.replace(' ', '')}" for t in tags[:5])
        description = f"{description} {hashtags}"
    description = description.replace("https://", "").replace("http://", "")
    # ChromeDriver send_keys 不支援 BMP 外字元（多數 emoji），會直接丟 WebDriverException
    description = "".join(ch for ch in description if ord(ch) <= 0xFFFF).rstrip()[:500]
    return title, description


def fill_and_publish_pin(driver, meta: dict, image_path: Path, product_url: str, board: str = None) -> bool:
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import NoSuchElementException

    board = board or meta.get("collection") or BOARD_NAME

    title, description = build_pin_copy(meta)
    link = f"{product_url}?utm_source=pinterest&utm_medium=social&utm_campaign=auto"

    driver.get(PIN_BUILDER_URL)
    time.sleep(5)

    file_input = driver.find_element(By.CSS_SELECTOR, 'input[type="file"][aria-label="上傳檔案"]')
    driver.execute_script("arguments[0].style.display = 'block';", file_input)
    file_input.send_keys(str(image_path))
    time.sleep(6)

    title_el = driver.find_element(By.CSS_SELECTOR, 'textarea[placeholder="新增標題"]')
    title_el.click()
    title_el.send_keys(title)

    desc_el = driver.find_element(By.CSS_SELECTOR, 'div[aria-label="讓所有人知道你的 Pin 內容"]')
    desc_el.click()
    desc_el.send_keys(description)

    link_el = driver.find_element(By.CSS_SELECTOR, 'textarea[placeholder="新增目的地連結"]')
    link_el.click()
    link_el.send_keys(link)

    driver.find_element(By.CSS_SELECTOR, '[data-test-id="board-dropdown-select-button"]').click()
    time.sleep(1.5)
    try:
        driver.find_element(By.CSS_SELECTOR, f'[data-test-id="board-row-{board}"]').click()
    except NoSuchElementException:
        print(f"  ⚠️  找不到 board「{board}」，改發預設 board「{BOARD_NAME}」", flush=True)
        driver.find_element(By.CSS_SELECTOR, f'[data-test-id="board-row-{BOARD_NAME}"]').click()
    time.sleep(1)

    driver.find_element(By.CSS_SELECTOR, '[data-test-id="board-dropdown-save-button"]').click()
    time.sleep(8)

    html = driver.page_source
    return "已建立一個 Pin" in html or "儲存到" in html


def cmd_list():
    metadata = load_metadata()
    pending = pending_designs(metadata)
    print(f"{'#':>3}  {'Title':<50} {'Redbubble URL'}")
    print("-" * 100)
    for i, m in enumerate(pending, 1):
        print(f"{i:>3}  {m['title'][:48]:<50} {m['redbubble_url']}")
    if not pending:
        print("沒有待 pin 的設計")


def cmd_batch():
    metadata = load_metadata()
    pending = pending_designs(metadata)
    if not pending:
        print("沒有待 pin 的設計")
        return

    print(f"準備發 {len(pending)} 支 pin")
    for meta in pending:
        _run_one(metadata, meta)


def cmd_daily(count: int = None):
    """每天固定發 N 支：從『全部有商品網址的設計』隨機挑（不管有沒有 pin 過），
    每次都用隨機 caption + 隨機 mockup，讓同一設計重複曝光時長得不一樣。
    這是給排程用的，跟 batch/one（只發還沒 pin 過的）不同，batch/one 還是拿來處理新設計。
    count 沒給就隨機 1-2 支（使用者要求的節奏）。"""
    if count is None:
        count = random.randint(1, 2)
    metadata = load_metadata()
    pool = [m for m in metadata if m.get("redbubble_url")]
    if not pool:
        print("沒有任何設計有商品網址，無法發文")
        return
    picks = random.sample(pool, min(count, len(pool)))
    print(f"今日排程：從 {len(pool)} 個設計裡隨機挑 {len(picks)} 個", flush=True)
    for meta in picks:
        _run_one(metadata, meta)


def cmd_one(keyword: str):
    metadata = load_metadata()
    meta = next((m for m in metadata if keyword.lower() in m.get("title", "").lower()), None)
    if not meta:
        print(f"❌ 找不到標題含「{keyword}」的設計")
        return
    if not meta.get("uploaded") or not meta.get("redbubble_url"):
        print(f"❌ {meta['title']} 還沒有 redbubble_url 或還沒上架")
        return
    _run_one(metadata, meta)


def _run_one(metadata: list, meta: dict):
    print(f"\n📌 {meta['title']}", flush=True)
    tmp_dir = BASE_DIR / "_pinterest_tmp"
    try:
        image_path = get_mockup_image(meta["redbubble_url"], tmp_dir)
        print(f"  🖼️  mockup: {image_path.name}", flush=True)
    except Exception as e:
        print(f"  ❌ 抓圖失敗: {e}", flush=True)
        return

    driver = get_driver()
    try:
        ok = fill_and_publish_pin(driver, meta, image_path, meta["redbubble_url"])
        if ok:
            print("  ✅ 發布成功", flush=True)
            meta["pinned"] = True
            update_metadata_field(meta["text"], pinned=True)
        else:
            print("  ⚠️  沒看到成功訊息，人工確認一下", flush=True)
    except Exception as e:
        print(f"  ❌ 發布失敗: {e}", flush=True)
    finally:
        driver.quit()
        try:
            image_path.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pinterest 自動發文")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("list", help="列出待 pin 的設計")
    sub.add_parser("batch", help="批次發布全部待 pin 的設計")
    one = sub.add_parser("one", help="只發一筆")
    one.add_argument("keyword", help="標題關鍵字")
    daily = sub.add_parser("daily", help="每日排程用：隨機挑 N 個設計重新發文（不管有沒有 pin 過）")
    daily.add_argument("count", type=int, nargs="?", default=None, help="要發幾支（不給就隨機 1-2 支）")

    args = parser.parse_args()
    if args.cmd == "list":
        cmd_list()
    elif args.cmd == "batch":
        cmd_batch()
    elif args.cmd == "one":
        cmd_one(args.keyword)
    elif args.cmd == "daily":
        cmd_daily(args.count)
    else:
        parser.print_help()
