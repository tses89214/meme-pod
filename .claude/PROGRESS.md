# PROGRESS

## 目前狀態（2026-08-04）
Redbubble duplicate 上傳全流程已跑通並實測成功（黑範本 + My faith is beer 設計，submit=False）：換圖、四語言 title/tags/description、版權框都正確。換圖 selector 修正為 `#select-image-base`。詳見 DECISIONS.md 2026-08-04。
發現換圖後 Redbubble 重算 mockup 很吃時間（實測近 20 分鐘），研判是後端固有成本非程式問題，排程時間要抓寬一點。
還沒做：實際 submit 送出測試、白範本那邊沒測過、大量批次跑的穩定性沒驗證。
Pinterest 導流計畫 Phase 1（手動測水溫）規格已定案，寫成 `skills/meme-pinterest.md`，10 支素材已備好文案交給使用者，網址/mockup 圖使用者手動處理中。

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
- `fill_design()` 還缺換圖那段（duplicate 頁面的 `select-image-large_clothing`，目前 `upload_image()` 用的是 `#select-image-single`，那是原本 New Work 頁的，duplicate 頁可能不適用，要重新確認）。
- 補完後要在 duplicate 頁面實際跑一次全流程（黑範本或白範本各一次），submit=False 先截圖人工檢查排版比例對不對，過了才試 --submit。
- Pinterest：等使用者自己抓好 10 支的商品網址+mockup 圖，串上 UTM 後手動貼上 Pinterest；3-4 週後回顧流量訊號。
- `upload_metadata.json` 目前有未 commit 的修改（session 開始前就存在，非本次會話所改），不是本次工作範圍，下次動它前先跟使用者確認內容。
