# PROGRESS

## 目前狀態（2026-08-05 收工）
Redbubble + Pinterest 全自動管線穩定運作中。目前 56 個設計，其中 50 個有商品網址並發過 Pinterest。

核心流程：`/meme` 收到新點子 → `quick_meme.py` 生 16 字型預覽 → 使用者選字型 → 問 collection（查 `python rb_upload.py collections`，只能選現有的）→ `publish_design.py "<text>" <font> [collection]`（Redbubble 黑白兩版 + Pinterest 一次做完，metadata 寫回 `upload_metadata.json`）。字型與 collection 永遠問使用者，文案（標題/描述/tags/翻譯/pinterest_captions）由 Claude 判斷撰寫。

三支每日/每週本機 crontab（**都用本機 crontab，不是雲端 `/schedule`**，因為都要碰本機瀏覽器/display）：
- `20 11 * * *` `pinterest_upload.py daily`：隨機挑 1-2 個設計重發 Pinterest（不管有沒有發過），log 在 `pinterest_daily.log`。
- `0 9 * * *` `rb_explore_like.py`：隨機愛心 explore 頁 3-5 個其他設計師的作品，log 在 `rb_explore_like.log`。
- 每週語錄搜尋排程**還沒裝**，見下方待辦。

主要腳本：
- `rb_upload.py`：`get_driver()` + `fill_design(meta, image_path, submit=True, target_url=<黑/白範本 duplicate 網址>, collection=...)`，送出後 return 商品網址。
- `pinterest_upload.py`：`list`/`batch`/`one <關鍵字>`/`daily [n]`，讀寫 `upload_metadata.json` 的 `uploaded`/`redbubble_url`/`pinned`/`pinterest_captions`。**寫入用 `update_metadata_field(text, **fields)`，即讀即寫單筆，不要整包陣列存檔**（2026-08-05 修的競態條件，見 DECISIONS.md）。
- `publish_design.py`：串 `rb_upload.py` + `pinterest_upload.py`，同樣用 `update_meta_field(text, **fields)` 安全寫入。
- `quote_search.py`：Tavily 搜語錄候選（毒舌/搞笑/正向/自嘲），純搜尋不判斷，`.env` 存 `TRAVILY_API_KEY`。
- `rb_explore_like.py`：explore 頁隨機愛心其他設計師作品，濾掉自己的設計。

技術細節、選擇器、踩過的雷都記在 DECISIONS.md、MEMORY.md 和 `skills/meme-pinterest.md`。

## 下一步（下次會話上班打卡先看這）
1. **每週語錄搜尋排程還沒接上 cron**：`quote_search.py` 本身測過沒問題，但「挑選+排版建議」需要 Claude 判斷，純腳本做不到。要先測 `claude -p` 非互動模式能不能正常用 telegram plugin reply（**絕對不要跑 `claude mcp list`**，會弄斷自己的 TG 連線，教訓見 MEMORY.md），測成再裝進本機 crontab。
2. 4 筆舊設計對不到 Redbubble 商品網址，使用者說先不管：Staff Adult Lv.99 Funny Gaming Meme、Orange Juice Sweat Zhongshan Qiang Abstract Chinese Tee、Cat Time Funny Cute Meme Tee、I Believe in Air Conditioner Funny Summer Meme Tee。
3. Pinterest 個人檔案簡介自動化失敗過（send_keys 漏字元 + JS setter 存不進去），使用者已手動貼過，之後不用再碰。
4. `upload_metadata.json` 已 commit 乾淨，56 筆全部同步。
