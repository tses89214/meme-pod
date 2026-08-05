# PROGRESS

## 上班打卡先看這（2026-08-05 晚，session 重啟後）
這個 session 的 Telegram plugin 連線斷了（跑 `claude mcp list` 誤觸的，細節見 MEMORY.md「這台機器跑多個 Telegram bot session」），沒工具能自己重連，靠 `~/start_all_claude_bots.sh`（每 5 分鐘 cron 跑一次）偵測 `claude_bg_memepod` tmux session 不在了才會自動用 `--continue` 重開一個新 session（會接續這個對話，TG 連線是新的、健康的）。若你正在讀這段，代表已經重啟過了。

**立刻要做的事（使用者已確認、按順序）：**
1. Focus 的 `publish_design.py` 是使用者主動要求砍掉重跑的（跑到「Redbubble: white_template」那步、mockup 還在重算，還沒按下 submit，所以沒有重複刊登風險，安全可以整個重跑）。PRAF 這次還沒開始跑。重啟後兩個都要從頭跑一次：
   - Focus：`.last_meme_session.json` 先復原成 `/tmp/claude-1000/-home-tses89214-meme-pod/ca9f4b2a-45cd-42e2-952d-937f266ffbe2/scratchpad/focus_session.json`（這個 scratchpad 路徑是舊 session 的，新 session 可能換了 conversation id 路徑跑掉，找不到就重跑 `quick_meme.py "*Focus* /n on what's in front of you"` 重新生成字型預覽，選字型時挑 CAVEAT 對應那個字型 caveat）→ `python publish_design.py "*Focus* /n on what's in front of you" caveat "Life.exe Has Stopped Working"`
   - PRAF：同理，`.last_meme_session.json` 復原成 `.../scratchpad/praf_session.json`（一樣路徑可能失效，失效就重跑 `quick_meme.py "My MBTI is /n *PRAF* /n poor as f*ck"`，選 FREDOKA ONE 對應的 fredoka）→ `python publish_design.py "My MBTI is /n *PRAF* /n poor as f*ck" fredoka "Life.exe Has Stopped Working"`
   - metadata（title/description/tags/translations/pinterest_captions）都已經寫好存在 `upload_metadata.json` 裡了，不用重寫，直接跑 publish_design.py 即可。
2. 使用者選定 4 句新語錄要開工，照 `/meme` 流程（quick_meme.py 生 16 字型 → 問使用者選字型 → 問 collection → `publish_design.py`）：
   - `Error 404 /n *Motivation* /n not found`
   - `Sarcasm: because /n physical violence is /n *frowned upon*`
   - `I'm *paw*-sitive`
   - `*Silence* is golden. /n Duct tape is silver.`
   （這幾句文案/tags/translations 都還沒寫，需要先幫每句寫好 metadata 才能上架，跟平常 /meme 流程一樣）
   - 已經跑過一次 `quick_meme.py "Error 404 /n *Motivation* /n not found"`（背景 ID bkba1alty，重啟後這個背景工作大概率已經死了，要重跑）。
3. 這 3 步做完後，回頭看下面「每週語錄搜尋排程」的設計，測試 `claude -p` 非互動模式能不能正常用 telegram plugin reply（**絕對不要跑 `claude mcp list`**，會弄斷自己的連線，教訓見 MEMORY.md），測成再裝 crontab。

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
