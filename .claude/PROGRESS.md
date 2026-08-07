# PROGRESS

## 目前狀態（2026-08-06 晚）
Redbubble + Pinterest 全自動管線穩定運作中。目前 69 個設計，全部有商品網址並發過 Pinterest（4 筆更早期的舊設計對不到網址，使用者說先不管，見下）。

新增一個 collection「Dad Jokes」（使用者自己在 Redbubble 後台建的）+ 對應 Pinterest board（我建的，選擇器記在 MEMORY.md），3 個 dad-joke 主題設計都補發進去了。

核心流程：`/meme` 收到新點子 → `quick_meme_remote.sh` 生 16 字型預覽（遠端算，見下）→ 使用者選字型 → 問 collection（查 `python rb_upload.py collections`，只能選現有的）→ `publish_design.py "<text>" <font> [collection]`（Redbubble 黑白兩版 + Pinterest 一次做完，metadata 寫回 `upload_metadata.json`）。字型與 collection 永遠問使用者，文案（標題/描述/tags/翻譯/pinterest_captions）由 Claude 判斷撰寫，**5 種 Pinterest 文案風格全部都要帶 tag 朋友的鉤子**（2026-08-06 補了 61 個設計漏掉這點的 180 句文案，之後新設計直接照這標準寫）。

**字型預覽改用遠端算**（2026-08-06 新增）：`quick_meme_remote.sh` 把算圖丟去 `root@cjs-dev`（8 core/15GB，已有 passwordless SSH，`fonts/` 638MB 已一次性同步過去），比本機 Pi 快 6-10 倍（本機 5-10 分鐘 → 遠端來回 ~1 分鐘）。連不上 cjs-dev 會自動退回本機跑 `quick_meme.py`。`/meme` skill 已改成預設呼叫這支。

三支本機 crontab（**都用本機 crontab，不是雲端 `/schedule`**，因為都要碰本機瀏覽器/display/或本機檔案）：
- `20 11 * * *` `pinterest_upload.py daily`：隨機挑 1-2 個設計重發 Pinterest（不管有沒有發過），log 在 `pinterest_daily.log`。
- `0 9 * * *` `rb_explore_like.py`：隨機愛心 explore 頁 3-5 個其他設計師的作品，log 在 `rb_explore_like.log`。
- `0 10 * * 1` `quote_weekly.py`：每週一搜語錄候選 + 用隔離的 `claude -p` 子行程挑選/排版建議 + 直接呼叫 Telegram Bot API 送出（**不透過 MCP plugin**，避免跟常駐 `--channels` session 搶 bot token 的 long-poll），log 在 `quote_weekly.log`。

主要腳本：
- `rb_upload.py`：`get_driver()` + `fill_design(meta, image_path, submit=True, target_url=<黑/白範本 duplicate 網址>, collection=...)`，送出後 return 商品網址。
- `pinterest_upload.py`：`list`/`batch`/`one <關鍵字>`/`daily [n]`，讀寫 `upload_metadata.json` 的 `uploaded`/`redbubble_url`/`pinned`/`pinterest_captions`。**寫入用 `update_metadata_field(text, **fields)`，即讀即寫單筆，不要整包陣列存檔**（2026-08-05 修的競態條件，見 DECISIONS.md）。`build_pin_copy()` 會自動濾掉 BMP 外字元（多數 emoji），寫文案不用刻意避開。
- `publish_design.py`：串 `rb_upload.py` + `pinterest_upload.py`，同樣用 `update_meta_field(text, **fields)` 安全寫入。
- `quote_search.py`：Tavily 搜語錄候選（毒舌/搞怪/正向/自嘲/roast/dad jokes），純搜尋不判斷，`.env` 存 `TRAVILY_API_KEY`。
- `quote_weekly.py`：串 `quote_search.py` + 隔離 `claude -p` 判斷 + Telegram Bot API 直送，給 cron 用。
- `rb_explore_like.py`：explore 頁隨機愛心其他設計師作品，濾掉自己的設計。
- `quick_meme_remote.sh`：字型預覽遠端算 + 自動 fallback 本機。

技術細節、選擇器、踩過的雷都記在 DECISIONS.md、MEMORY.md 和 `skills/meme-pinterest.md`。

## 下一步（下次會話上班打卡先看這）
1. 4 筆舊設計對不到 Redbubble 商品網址，使用者說先不管：Staff Adult Lv.99 Funny Gaming Meme、Orange Juice Sweat Zhongshan Qiang Abstract Chinese Tee、Cat Time Funny Cute Meme Tee、I Believe in Air Conditioner Funny Summer Meme Tee。
2. Pinterest 個人檔案簡介自動化失敗過（send_keys 漏字元 + JS setter 存不進去），使用者已手動貼過，之後不用再碰。
3. `design_generator.py` 的 `clean_text()` 白名單 2026-08-06 補了 `% = & # @ +`，如果之後又有符號被靜默濾掉（畫面上文字消失/跟預期不符），先檢查這個白名單，不用重新除錯半天。
4. `quote_weekly.py` 週一 10:00 才第一次真的透過 cron 跑，還沒看過真實排程觸發的結果，下次上班可以順便確認 `quote_weekly.log` 有沒有正常產生。
5. `upload_metadata.json` 已 commit 乾淨，69 筆全部同步。
