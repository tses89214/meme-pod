# PROGRESS

## 目前狀態（2026-08-04）
Redbubble duplicate 上傳全流程已實戰驗證成功：「My faith is beer」與「Universe Grant Me Power」兩個設計，各自黑/白字兩版（共 4 筆），全部真的 submit 送出並確認發布成功（Redbubble 回「Congratulations! Your design is published.」，mockup 截圖確認圖片大小比例正常）。`upload_metadata.json` 這兩筆已標 `uploaded: true`（還沒 commit，跟使用者原本那份未 commit 的修改混在一起，留給使用者自己 commit）。
換圖 selector 確認是 `#select-image-base`。詳見 DECISIONS.md 2026-08-04。單筆全流程（換圖+四語言填表+送出）耗時約 20 分鐘，主因是 Redbubble 換圖後端處理 mockup 慢，非程式問題。
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
- Redbubble 上傳管線已經可用（`rb_upload.py` 的 `get_driver()` + `fill_design(target_url=...)`），下次有新設計要上架可以直接照 `rb_batch_upload.py`（在 scratchpad，還沒搬進專案）那個模式跑：黑範本配白字圖、白範本配黑字圖，各 4 語言，submit=True。
- 目前只跑過 2 個設計驗證，還沒大量跑過（例如一次 10+ 件）的穩定性沒驗證，Cloudflare/處理時間累積起來要注意。
- Pinterest：等使用者自己抓好 10 支的商品網址+mockup 圖，串上 UTM 後手動貼上 Pinterest；3-4 週後回顧流量訊號。
- `upload_metadata.json` 有未 commit 的修改（使用者原本的 + 這次新增的 2 筆 uploaded:true），下次動這個檔案前先跟使用者確認要不要一起 commit。
