#!/usr/bin/env python3
"""
save_rb_session.py — 手動登入 Redbubble 並儲存 session cookies
在有 GUI 的機器上執行，登入後把 rb_session.json 傳到 Pi。

使用方式：
  python save_rb_session.py
  # 瀏覽器會開啟，你手動登入，登入成功後按 Enter
  # 程式會儲存 rb_session.json
"""

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)   # 有視窗
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()

    page.goto("https://www.redbubble.com/auth/login")
    print("請在瀏覽器視窗中手動登入 Redbubble，登入成功後回到這裡按 Enter...")
    input("登入完成後按 Enter > ")

    # 儲存 session state（含 cookies + localStorage）
    ctx.storage_state(path="rb_session.json")
    print("✅ 已儲存 rb_session.json，請把這個檔案傳到 Pi 的 ~/meme-pod/ 目錄下")
    browser.close()
