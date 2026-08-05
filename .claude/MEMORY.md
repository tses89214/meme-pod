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

## 這台 Pi 的桌面/瀏覽器環境
- 這台機器有真實 Wayland 桌面 session（非純無頭），透過 RPi Connect 的 `wayvnc` 讓使用者遠端看/操作，`DISPLAY=:0`、`WAYLAND_DISPLAY=wayland-0`、`XDG_RUNTIME_DIR=/run/user/1000`（Claude 的 Bash 工具預設沒帶這些環境變數，要手動加在指令前面）。
- 系統只有 `chromium`（arm64），沒有 Google Chrome；`undetected_chromedriver` 預設會抓 x86_64 版 chromedriver 導致 arm64 上直接 Exec format error。已裝 `chromium-driver` apt 套件（版本要跟 `chromium` 對齊，兩個一起裝/升級）。
- `undetected_chromedriver` 需要對 chromedriver 執行檔做 in-place patch（去掉自動化特徵），所以不能直接指向系統唯讀的 `/usr/bin/chromedriver`（PermissionError），要複製一份到使用者可寫路徑（例如 `~/.local/share/undetected_chromedriver/chromedriver_arm64`）再指定 `driver_executable_path`。
- Redbubble 的 Cloudflare 驗證在 `/portfolio/images/new`、`/portfolio/images/<id>/duplicate` 這類頁面會自動過關，不需要人手動點任何框，純粹是等（實測 30-90 秒內都過了），登入 session 透過 `rb_upload.py` 的 `--user-data-dir`（`.rb_chrome_profile`）持久化，重開全新瀏覽器也記得登入。
- 同一個 `.rb_chrome_profile` 也拿來登入 Pinterest（2026-08-03 手動登入過一次，跳到 `pinterest.com/business/hub/`），cookie 是分網域存的，Redbubble 和 Pinterest 共用同一份 profile 不會互相干擾。
- 系統時區是 `Asia/Taipei`，cron 用的是這個本地時區，不是 UTC。
- 這台機器的 `crontab` 指令有個怪 bug：`crontab <file>` 如果檔案路徑太長／太多層目錄（例如 `/tmp/claude-.../scratchpad/xxx.txt`），會直接吃到一半報 "No such file or directory"（檔案明明存在，`ls`/`cat` 都正常）。解法：先把檔案複製到短路徑（例如 `/tmp/xxx.txt`）再 `crontab` 那個短路徑檔案，成功後可以刪掉。之後要修改 crontab 都用這招，別再花時間除錯同一個問題。
- `/schedule` skill（`RemoteTrigger`）建立的是 **雲端** Claude 代理排程，跑在 Anthropic 雲端隔離環境，完全碰不到這台 Pi 的本機檔案／瀏覽器 session／display。任何依賴本機瀏覽器自動化（Redbubble/Pinterest 這類）的排程都不能用這個，要用本機 `crontab` 才行。
