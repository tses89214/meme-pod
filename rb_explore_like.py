#!/usr/bin/env python3
"""
rb_explore_like.py — 每天隨機愛心幾個 Redbubble explore 頁面上其他設計師的作品
==============================================================================
單純增加跟其他創作者的互動，不篩類別、純隨機。跟現有 rb_upload.py 共用同一份
`.rb_chrome_profile` 登入 session。

用法：
  python rb_explore_like.py [n]   # n 沒給預設隨機 3-5 個
"""

import re
import sys
import time
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rb_upload import get_driver

EXPLORE_URL = "https://www.redbubble.com/explore/"
OWN_ARTIST_SLUG = "-by-tses89214/"


def collect_product_links(driver) -> list[str]:
    from selenium.webdriver.common.by import By
    driver.get(EXPLORE_URL)
    time.sleep(6)
    links = driver.find_elements(By.CSS_SELECTOR, 'a[class*="MediaCard-styles__link"]')
    urls = []
    for el in links:
        href = el.get_attribute("href")
        if href and "/i/" in href and OWN_ARTIST_SLUG not in href:
            urls.append(href.split("?")[0])
    return list(dict.fromkeys(urls))


def like_one(driver, url: str) -> str:
    from selenium.webdriver.common.by import By
    driver.get(url)
    time.sleep(4)
    btn = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="add-to-list-button"]')
    if btn.get_attribute("aria-label") == "Remove from list":
        return "already liked"
    btn.click()
    time.sleep(2)
    btn = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="add-to-list-button"]')
    return "liked" if btn.get_attribute("aria-label") == "Remove from list" else "click did not register"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    driver = get_driver()
    try:
        candidates = collect_product_links(driver)
        if not candidates:
            print("explore 頁面沒抓到任何商品連結")
            return
        picks = random.sample(candidates, min(n, len(candidates)))
        print(f"從 {len(candidates)} 個作品裡隨機挑 {len(picks)} 個", flush=True)
        for url in picks:
            status = like_one(driver, url)
            print(f"  {status}: {url}", flush=True)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
