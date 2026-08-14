#!/usr/bin/env python3
"""
pinterest_explore_like.py — 每天隨機愛心幾個 Pinterest 首頁上其他人的 pin
==========================================================================
單純增加互動，不篩類別、純隨機。跟現有 rb_upload.py 共用同一份
`.rb_chrome_profile` 登入 session（同時也是 Pinterest 登入 session）。

用法：
  python pinterest_explore_like.py [n]   # n 沒給預設隨機 45-55 個
"""

import sys
import time
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rb_upload import get_driver

HOMEFEED_URL = "https://www.pinterest.com/homefeed/"
REACT_LABEL = "回應"


def collect_pin_links(driver) -> list[str]:
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import StaleElementReferenceException
    driver.get(HOMEFEED_URL)
    time.sleep(6)
    links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/pin/"]')
    urls = []
    for el in links:
        try:
            href = el.get_attribute("href")
        except StaleElementReferenceException:
            continue
        if href and "/pin/" in href:
            urls.append(href.split("?")[0])
    return list(dict.fromkeys(urls))


def react_one(driver, url: str) -> str:
    from selenium.webdriver.common.by import By
    driver.get(url)
    time.sleep(4)
    try:
        btn = driver.find_element(By.CSS_SELECTOR, f'button[aria-label="{REACT_LABEL}"]')
    except Exception:
        return "找不到回應按鈕"
    before = btn.get_attribute("aria-pressed")
    if before == "true":
        return "already reacted"
    btn.click()
    time.sleep(2)
    try:
        btn = driver.find_element(By.CSS_SELECTOR, f'button[aria-label="{REACT_LABEL}"]')
    except Exception:
        return "reacted (無法重新確認狀態)"
    after = btn.get_attribute("aria-pressed")
    return "reacted" if after == "true" else "click did not register"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else random.randint(45, 55)
    driver = get_driver()
    try:
        candidates = collect_pin_links(driver)
        if not candidates:
            print("homefeed 沒抓到任何 pin 連結")
            return
        picks = random.sample(candidates, min(n, len(candidates)))
        print(f"從 {len(candidates)} 個 pin 裡隨機挑 {len(picks)} 個", flush=True)
        for url in picks:
            status = react_one(driver, url)
            print(f"  {status}: {url}", flush=True)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
