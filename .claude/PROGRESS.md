# PROGRESS

## 目前狀態（2026-08-05）
Redbubble + Pinterest 全自動管線都打通並跑過真實資料。目前 48 個設計，44 個有商品網址並發過 Pinterest（4 筆對不到網址擱置，見下）。

這次還完成：5 個主題 board 拆分（+ 保留舊 board 當「所有商品」大 board）、全部 48 個設計各寫好 5 種 Pinterest 文案風格（隨機抽用，見 `pinterest_captions` 欄位）、本機 crontab 每天 11:20 自動發 1-2 篇（`pinterest_upload.py daily`，隨機從全部設計裡挑，不管有沒有發過）。

Pinterest 個人檔案簡介**沒有**自動化成功，踩了大坑（send_keys 確定性漏字元 + JS setter 存不進去），最後請使用者自己手動貼過。細節見 DECISIONS.md。

兩支主要腳本：
- `rb_upload.py`：`get_driver()` + `fill_design(meta, image_path, submit=True, target_url=<黑/白範本 duplicate 網址>)`，送出後會 return 商品網址。
- `pinterest_upload.py`：`list`/`batch`/`one <關鍵字>`，讀 `upload_metadata.json` 裡 `uploaded=true` 且有 `redbubble_url` 且 `pinned` 不是 true 的設計，自動抓 mockup 圖、發 pin、標記 `pinned=true`。

技術細節、選擇器、踩過的雷都記在 DECISIONS.md 和 `skills/meme-pinterest.md`。

## 已完成
- 掃過專案結構，確認 `.upload_queue.json` 為空（無待傳項目）。
- 建立進度／決策／記憶文件，並修正 .gitignore 讓三份文件可被 commit。
- CLAUDE.md 補上「TG 來的問題一律回 TG」規則。
- 用 grilling 拷問完 Pinterest 導流計畫，定案並寫成 `skills/meme-pinterest.md`，10 支種子清單的文案已交付使用者。
- 修好 Redbubble 自動化環境：apt 裝 `chromium`+`chromium-driver`（arm64 版本對齊，原本系統只有 chromium 沒有 chrome）、把系統 chromedriver 複製到使用者可寫路徑讓 undetected_chromedriver 能 patch、`rb_upload.py` 的 `get_driver()` 指定正確的 browser/driver 路徑。
- 實測確認：Redbubble 登入 session 靠 `.rb_chrome_profile` 持久化，重開全新瀏覽器實例不用重新登入；`/portfolio/images/new`、`/portfolio/images/<id>/duplicate` 這類頁面的 Cloudflare 驗證會自動過關（30-90 秒等待，不用人手動點），已把 `rb_upload.py` 的等待 timeout 從 20 秒拉到 150 秒、拿掉會卡死的 `input()`。
- 探索「Duplicate design」流程（決策見 DECISIONS.md）：找到黑/白範本 work id、duplicate 網址規則、title/description/checkbox/submit 的欄位 id（跟原 New Work 表單共用）。Tags 欄位是 React pill 元件還沒摸清楚怎麼操作。
- Pinterest 也用同一個 `.rb_chrome_profile` 手動登入過一次並實測持久化成功（全新瀏覽器實例直接進企業專區，不用重登）。
- `.gitignore` 補上 `.rb_chrome_profile/`（內含登入 session/cookie，不可進版控）。

## 下一步（下次會話上班打卡先看這）
- `/meme` flow：生成 → 選字型 → 選 collection → `publish_design.py "<text>" <font> [collection]`（Redbubble 黑白兩版 + Pinterest 一次做完）→ `drive_upload.py batch`。全部串好了。
- 每天 11:20 本機 crontab 會自動跑 `pinterest_upload.py daily`，log 在 `~/meme-pod/pinterest_daily.log`，要檢查有沒有正常執行可以看這個檔案或 `crontab -l`。
- 排隊中還沒生成/發布的 3 個新點子（使用者給的翻譯已確認）：
  1. "A Sip of Happiness and Joy"
  2. "Fat Otaku Happy Water"
  3. "Focus on What's in Front of You"
- 4 筆設計對不到 Redbubble 商品網址，使用者說先不管：Staff Adult Lv.99 Funny Gaming Meme、Orange Juice Sweat Zhongshan Qiang Abstract Chinese Tee、Cat Time Funny Cute Meme Tee、I Believe in Air Conditioner Funny Summer Meme Tee。可能當初沒真的上架成功，需要人工去後台核對。
- Pinterest 個人檔案簡介還是空的，自動化失敗，需要使用者自己去 `pinterest.com/settings/edit-profile/` 手動貼草稿文字（文字在 DECISIONS.md 2026-08-04 那則）。
- `upload_metadata.json` 已經 commit 乾淨。
