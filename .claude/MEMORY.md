# MEMORY

跨會話值得記住的細節（非決策、非進度，屬於「知識」）。

## Redbubble 上傳
- `rb_interactive.py` 用 Playwright 持久 context（`/tmp/.rb_browser_data`），登入流程需人工確認截圖後才送出（`WAIT_FOR_USER`），不是全自動。
- `uploader.py` 的 batch 上傳結果寫回 `upload_metadata.json`（每筆設計標 `"uploaded": true`）。

## 字型測試流程
- `quick_meme.py <句子>` 會用固定 16 款字型（`PREVIEW_FONTS`）各出黑/白透明 PNG，存進 `.last_meme_session.json` 供後續「上架」指令挑選。
- 預覽格圖 `output/_preview_grid_latest.png` 是暫存，不會保留在版控／長期存在，重開機或清過就要重新產生。

## 資料流
- `.upload_queue.json` 存待傳項目，目前恆為空代表沒有卡住的上傳。
- 雙上傳管道：Redbubble（`rb_upload.py`/`rb_interactive.py`/`uploader.py`）與 Google Drive（`drive_upload.py`，用 `.drive_token.pickle` 存 OAuth token）。
