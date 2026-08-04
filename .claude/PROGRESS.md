# PROGRESS

## 目前狀態（2026-08-04）
Redbubble + Pinterest 全自動管線都打通並跑過真實資料，端到端：生成設計 → Redbubble 上架（黑白兩版）→ 自動抓商品網址 → 抓真實 mockup 照 → 自動發 Pinterest pin → 標記完成。目前總共 42/46 個設計已經全部發到 Pinterest（4 筆對不到網址擱置）。

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
- 流程已經串成一個指令 `publish_design.py "<text>" <font> [collection]`：Redbubble 黑白兩版上架 + Pinterest 發 pin 一次做完。`/meme` skill 也更新成這套（選字型、選 collection 都問使用者，其餘全自動，包含 Drive 備份）。
- Collection 功能只做「選現有的」，沒做新增；`python rb_upload.py collections` 可查目前選項。
- **舊設計 Pinterest 補發已完成**：從 `manage_works` 分頁（2 頁）比對出 42 筆商品網址，扣掉 4 筆對不到（見下）全部批次發完 Pinterest（38 筆，一次重試）。`pinterest_upload.py list` 目前顯示「沒有待 pin 的設計」。批次量測試等於順便做了（38 筆一次跑完沒出大問題，只有 1 筆需要重試）。
- 4 筆設計對不到 Redbubble 商品網址，使用者說先不管：Staff Adult Lv.99 Funny Gaming Meme、Orange Juice Sweat Zhongshan Qiang Abstract Chinese Tee、Cat Time Funny Cute Meme Tee、I Believe in Air Conditioner Funny Summer Meme Tee。可能當初沒真的上架成功，需要人工去後台核對。
- `skills/meme-pinterest.md` 的 Open TODOs 裡「拆 board」那項還沒做，board 分類還是只有一個「Funny Meme Shirts」。
- `upload_metadata.json` 已經 commit 乾淨。
- 使用者要求：查 Pinterest best practice（多篇來源），整理摘要給使用者 review，包含個人檔案/簡介文案草稿，通過才實際去改 Pinterest 個人檔案——這件事還沒開始做。
