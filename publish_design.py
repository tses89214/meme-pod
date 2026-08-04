#!/usr/bin/env python3
"""
publish_design.py — 字型選好之後，一路發到 Redbubble + Pinterest，不用人再盯著跑
=================================================================================
前提（呼叫這支之前要先做完的事，這些仍然需要人判斷，不自動化）：
  1. quick_meme.py 已經跑過，.last_meme_session.json 裡有這個 text 的 16 字型結果
  2. 使用者已經選好字型
  3. upload_metadata.json 裡已經有這個 text 的 metadata 條目（title/description/tags/
     main_tag/translations，這段需要人或 Claude 寫文案，不是這支腳本的工作）

這支腳本做的事（全自動，不需要再確認）：
  1. 從 .last_meme_session.json 找出選定字型的黑字/白字圖
  2. 黑字圖 duplicate 自白底範本、白字圖 duplicate 自黑底範本，上架 Redbubble（各自四語言）
  3. 把送出後拿到的商品網址、uploaded=true 存回 upload_metadata.json
  4. 用商品網址抓真實 mockup 照，發 Pinterest pin，標 pinned=true
  5. 印出最終結果（兩個 Redbubble 商品網址 + Pinterest 發布狀態）

用法：
  python publish_design.py "<text>" <font>

例：
  python publish_design.py "*Actions* /n speak louder than words." dancing
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
SESSION_FILE = BASE_DIR / ".last_meme_session.json"
META_FILE = BASE_DIR / "upload_metadata.json"

sys.path.insert(0, str(BASE_DIR))
from rb_upload import get_driver, fill_design, BLACK_TEMPLATE_DUP_URL, WHITE_TEMPLATE_DUP_URL
from pinterest_upload import get_mockup_image, fill_and_publish_pin


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_image_paths(text: str, font: str) -> dict:
    session = load_json(SESSION_FILE)
    if session.get("text") != text:
        raise RuntimeError(
            f".last_meme_session.json 裡的 text 是 {session.get('text')!r}，"
            f"跟要求的 {text!r} 不一樣，先跑 quick_meme.py 產生這句的字型"
        )
    fonts = session["fonts"]
    if font not in fonts:
        raise RuntimeError(f"字型 {font!r} 不在這次 session 裡：{fonts}")
    return session["sets"][fonts.index(font)]


def find_meta(metadata: list, text: str) -> dict:
    meta = next((m for m in metadata if m.get("text") == text), None)
    if not meta:
        raise RuntimeError(f"upload_metadata.json 裡找不到 text={text!r} 的條目，metadata 要先寫好")
    return meta


def upload_to_redbubble(meta: dict, images: dict) -> dict:
    """回傳 {'black_template_url':..., 'white_template_url':...}（都是同一設計的商品網址，理論上其實是同一個 work 兩個版本各自的網址）。"""
    urls = {}
    for variant_name, image_path, target_url in [
        ("white_template", images["black"], WHITE_TEMPLATE_DUP_URL),
        ("black_template", images["white"], BLACK_TEMPLATE_DUP_URL),
    ]:
        print(f"-- Redbubble: {variant_name} --", flush=True)
        driver = get_driver()
        try:
            product_url = fill_design(driver, meta, image_path, submit=True, target_url=target_url)
            urls[variant_name] = product_url
            print(f"   -> {product_url}", flush=True)
        finally:
            driver.quit()
    return urls


def publish_pinterest(meta: dict, product_url: str) -> bool:
    print("-- Pinterest --", flush=True)
    tmp_dir = BASE_DIR / "_pinterest_tmp"
    image_path = get_mockup_image(product_url, tmp_dir)
    driver = get_driver()
    try:
        ok = fill_and_publish_pin(driver, meta, image_path, product_url)
        return ok
    finally:
        driver.quit()
        try:
            image_path.unlink()
        except Exception:
            pass


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    text, font = sys.argv[1], sys.argv[2]

    images = get_image_paths(text, font)
    metadata = load_json(META_FILE)
    meta = find_meta(metadata, text)
    print(f"發布：{meta['title']}", flush=True)

    urls = upload_to_redbubble(meta, images)
    meta["uploaded"] = True
    if urls.get("white_template"):
        meta["redbubble_url"] = urls["white_template"]
    save_json(META_FILE, metadata)

    pin_ok = False
    if meta.get("redbubble_url"):
        pin_ok = publish_pinterest(meta, meta["redbubble_url"])
        meta["pinned"] = pin_ok
        save_json(META_FILE, metadata)

    print("\n=== 完成 ===")
    print(f"Redbubble (white template): {urls.get('white_template')}")
    print(f"Redbubble (black template): {urls.get('black_template')}")
    print(f"Pinterest: {'成功' if pin_ok else '失敗，需要人檢查'}")


if __name__ == "__main__":
    main()
