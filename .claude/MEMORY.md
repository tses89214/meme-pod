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
- crontab 執行環境的 PATH 很陽春（不含 `~/.local/bin`），任何腳本裡用 `subprocess.run(["claude", ...])` 靠 PATH 找 `claude` 執行檔的，排程跑起來都會 `FileNotFoundError`，互動式 shell 測試看不出來（因為互動 shell 的 PATH 完整）。`pinterest_trends_check.py`、`quote_weekly.py` 都踩過（2026-08-19 修好，改寫死絕對路徑 `/home/tses89214/.local/bin/claude`）。以後任何新腳本要在 crontab 下跑且會呼叫 `claude` CLI 的，一律用絕對路徑，不要靠 PATH。要驗證排程環境行不行，用 `env -i HOME=... PATH=/usr/bin:/bin python3 ...` 模擬陽春 PATH 測，不要只在互動 shell 跑一次就当過。
- `pgrep -f <pattern>` 等待迴圈有自我誤判風險：如果 `<pattern>` 這個字串本身也出現在等待迴圈那行指令的完整 command line 裡（例如 `while pgrep -f pinterest_explore_like.py > /dev/null; do sleep 15; done`，這行指令自己就含有 `pinterest_explore_like.py` 字串），`pgrep -f` 會連自己這個 bash process 都算進去，導致條件永遠是 true、迴圈以為排程一直在跑，2026-08-19 因此卡等超過 8 小時（排程其實幾小時前就結束、Chrome 早就閒置）。之後這種等待迴圈要嘛用更精確的 pattern（如 `pgrep -f 'python3.*pinterest_explore_like\.py'`，排除掉自己那行沒有 `python3` 開頭的 bash wrapper），要嘛改成先跑一次 `ps aux | grep` 直接看有沒有真的 python process，不要把要找的字串原封不動放進迴圈本身的指令列。
- 這台機器的 `crontab` 指令有個怪 bug：`crontab <file>` 如果檔案路徑太長／太多層目錄（例如 `/tmp/claude-.../scratchpad/xxx.txt`），會直接吃到一半報 "No such file or directory"（檔案明明存在，`ls`/`cat` 都正常）。解法：先把檔案複製到短路徑（例如 `/tmp/xxx.txt`）再 `crontab` 那個短路徑檔案，成功後可以刪掉。之後要修改 crontab 都用這招，別再花時間除錯同一個問題。
- `/schedule` skill（`RemoteTrigger`）建立的是 **雲端** Claude 代理排程，跑在 Anthropic 雲端隔離環境，完全碰不到這台 Pi 的本機檔案／瀏覽器 session／display。任何依賴本機瀏覽器自動化（Redbubble/Pinterest 這類）的排程都不能用這個，要用本機 `crontab` 才行。
- 手動在互動 shell 跑 `publish_design.py`／`rb_upload.py` 忘記帶 `DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000` 時，Selenium 會報 `SessionNotCreatedException: cannot connect to chrome at 127.0.0.1:xxxxx` / `chrome not reachable`，這個錯誤訊息長得很像 Chrome 啟動當機或 profile lock 卡住（2026-08-20 第一時間誤判成 `.rb_chrome_profile/SingletonLock` 殘留，清掉重跑一樣失敗），實際上是純粹 `headless=False` 連不到 X。先確認 `echo $DISPLAY` 有值，沒有的話直接補 `DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000` 前綴再跑，比先猜 lock 檔案快。
- `rb_upload.py` 的 `fill_design()` 每次送出後都把截圖存到同一個固定路徑 `_rb_preview.png`，`upload_to_redbubble()` 依序跑 white_template 再 black_template，兩步共用這張截圖。如果 white_template 那步送出失敗（沒建立成功），但接著 black_template 那步成功了，`_rb_preview.png` 會被 black_template 的「Congratulations 已發布」畫面蓋掉——事後只看這張截圖會誤判 white_template 也成功了（2026-08-21 踩過）。要確認某一個 variant 到底有沒有真的建立，去 `https://www.redbubble.com/portfolio/manage_works` 數一下該設計標題出現幾次（正常應該 2 個 work），不要只看 `_rb_preview.png`。
- `publish_design.py` 的 Redbubble variant 回傳 `None`（`fill_design()` 抓不到 View 連結網址）或 Pinterest pin 回傳 `False`（`fill_and_publish_pin()` 沒有 traceback、靜默失敗）目前遇到的都是偶發的頁面延遲/loading race condition，不是程式邏輯 bug：直接手動重跑同一步驟（`fill_design(...)` 或 `publish_design.publish_pinterest(meta, meta['redbubble_url'])`）通常就過了，不用先急著改代碼。

## 這台機器跑多個 Telegram bot session（多支 claude --channels）
- `ps aux` 可看到同時有 4 個 `claude --dangerously-skip-permissions --channels plugin:telegram@claude-plugins-official`，各自用不同 `TELEGRAM_STATE_DIR`（`telegram`＝這個 meme-pod 專案、`telegram-invest`、`telegram-dinner`、`telegram-usstock`），每個各自跑在自己的 tmux session 裡（meme-pod 是 `claude_bg_memepod`），各自有獨立的 `bun run .../telegram/0.0.6 --shell=bun --silent start` 子行程負責維持 MCP 連線。
- **絕對不要在 Bash 工具裡跑 `claude mcp list`（或任何裸的 `claude` 子行程）**：2026-08-05 實測跑了一次 `claude mcp list` 之後，這個 session（929226）自己的 telegram plugin 子行程整個消失（`ps` 找不到），`mcp__plugin_telegram_telegram__reply` 從此在對話裡完全叫不出來（`ToolSearch` 找不到），導致沒辦法回 TG——踩雷當下完全不知道會有這個副作用，光是查健康狀態就把自己這條線弄斷了。沒有工具能從 session 內部重新接上，只能等外部（使用者重啟那個 tmux session）救。之後要查 MCP 狀態，用 `ToolSearch` 或看 `ps aux` 找 bun 行程，不要呼叫 `claude` 指令本身。
- Inbound（使用者傳訊息進來）跟 outbound（`reply` 工具送出去）是兩條不同機制：plugin 斷線後使用者的訊息還是收得到（透過 `<channel>` tag），但送不出去，容易誤判「使用者已讀不回」——其實是我方回不去。
- 復原機制：`~/start_all_claude_bots.sh` 每 5 分鐘跑一次（crontab），偵測對應 tmux session（`claude_bg_memepod` 等）不存在就用 `claude --continue --dangerously-skip-permissions --channels plugin:telegram@claude-plugins-official` 重開，`--continue` 會接上同一個對話。plugin 斷線且無法自救時，`tmux kill-session -t claude_bg_memepod` 是安全的復原手段（會被使用者授權時才做），5 分鐘內自動重開且對話不丟失。
- 副作用：強制砍 tmux session 會讓 Chrome 留下沒清乾淨的 `.rb_chrome_profile/SingletonLock`（`SingletonCookie`/`SingletonSocket` 也會殘留），對應的行程其實已經不在了。下次啟動瀏覽器如果卡在 Cloudflare 表單一直載入不出來（`wait_for` 150 秒 timeout），先檢查是不是這三個鎖檔還在，`rm` 掉就好，不用懷疑帳號或 Cloudflare 本身出問題。

## Redbubble explore 頁面結構（給 rb_explore_like.py 用）
- 「愛心」在 UI 上是心型圖示，但 DOM 裡的按鈕是 `button[data-testid="add-to-list-button"]`，Redbubble 內部把這個動作叫 "Add to list"，不是字面上的 favourite/like。`aria-label` 會在 "Add to list"（未愛心）/ "Remove from list"（已愛心）間切換，拿這個判斷點擊有沒有成功，也拿來避免對已經愛心過的作品重複點擊而誤取消。
- 商品連結來源是 explore 首頁（`/explore/`）的推薦輪播，選擇器 `a[class*="MediaCard-styles__link"]`，href 格式 `/i/<product_type>/<slug>/<work_id>/<variant>`。這頁面會混進使用者自己的設計（explore 個人化推薦的關係），要用 URL 裡的 `-by-<自己的 Redbubble 使用者名稱>/` 濾掉。
- 這頁面本身不擋 Cloudflare（跟已知的 `/shop/ap/<id>` 商品頁一樣），但點愛心是要登入的動作，還是要用 Selenium + `.rb_chrome_profile` 而非 `requests`。

## Pinterest board 建立流程
- 在 pin-builder 頁面（`https://www.pinterest.com/pin-builder/`）點開 board 下拉選單（`[data-test-id="board-dropdown-select-button"]`）後，選單裡會有一個 `[data-test-id="create-board-button"]`，點下去彈出新增表單：`#boardEditName` 填名稱、`[data-test-id="board-form-submit-button"]` 送出。不勾 `#secret` 就是公開 board（跟 2026-08-03 建第一個 board 時的欄位一致）。
- 用 `fill_and_publish_pin(..., board='<board 名稱>')` 把已有設計發去指定 board 時，`board-row-<名稱>` 這個選擇器偶爾會抓不到元素（`NoSuchElementException`，不是每次都會，原因不明，可能是下拉選單渲染時機問題），單獨重跑那一筆通常就過了，不用大改邏輯。
- 一次性腳本（不透過 `pinterest_upload.py` 既有函式）要注意 `tmp_dir` 一定要用絕對路徑：Selenium 的檔案上傳欄位 `send_keys()` 不接受相對路徑，會丟 `WebDriverException: path is not absolute`。
- Board 改名流程（2026-08-17 確認）：進 board 頁面（`https://www.pinterest.com/<username>/<board-slug>/`，board 清單可在 `https://www.pinterest.com/<username>/_saved/` 頁面的 body innerText 抓到，每個 board 連結格式是 `/tses892140613/<slug>/`）→ 點右上角「...」按鈕（無固定 test-id，用座標配合 `elementFromPoint` 往上找 `role=button` 的祖先元素）→ 選單裡「編輯資訊和設定」是個 `<button role="menuitem">`，文字在裡面的 `<span>`，一樣要往上找到 BUTTON 標籤才能點（不是 role=button）→ 彈出的 modal 裡名稱欄位是純 `<input>`（無穩定 id/data-test-id），用 `value` 屬性比對現有名稱去抓，抓到後 `Ctrl+A` + `Delete` 清空再打新名稱 → 按「完成」送出。
- 帳號（tses892140613）目前實際有 10 個 board，除了程式碼知道的幾個，還有 5 個之前建好但沒接進自動化流程的：Gym & Motivation Tees、Wholesome & Fun Lifestyle Tees、Gamer Life Level-Up Tees、Funny Work & Office Meme Tees、Bilingual Chinese Design Tees。2026-08-17 已經把全部 100 個設計的 `collection` 欄位配到對應 board（含這 5 個），`pinterest_upload.py` 發文時已支援依 `meta["collection"]` 自動選 board。
- 2026-08-19 再補建 2 個 board（`Adult Class System`、`Life.exe Has Stopped Working`），帳號共 11 個 board。查目前 board 清單最快的方法：開 `https://www.pinterest.com/pin-builder/`，點 `[data-test-id="board-dropdown-select-button"]` 展開下拉選單，`document.body.innerText` 裡就有完整清單（比爬 `_saved`/`_created` 頁面可靠，那兩頁的 board 連結不是簡單 `<a>` 標籤，抓不到）。
- Pinterest mockup 選圖有對比度風險：`pinterest_upload.py` 的 `get_mockup_image()` 從商品頁隨機挑一張真實照片當 pin 圖，26 種商品款式裡少數款式（如 active_tee）預設深色，黑字設計疊上去會看不到字。2026-08-19 修成依印花顏色過濾掉撞色的底色（解析 mockup URL 裡的 hex 色碼或顏色名稱，算亮度或比對關鍵字判斷深淺）。系統目前只會 pin 黑字版（白T listing，`redbubble_url` 固定存這個），所以目前只有黑字避深色底這條路徑會被用到。

## 字型預覽遠端算圖（cjs-dev）
- `root@cjs-dev` 已有 passwordless SSH（8 core / 15GB RAM，Debian 13 trixie），比這台 Pi 快很多，拿來跑 `quick_meme.py` 純 PIL 算圖（不需要瀏覽器/display，適合丟遠端）。
- 遠端目錄故意用跟本機一模一樣的絕對路徑 `/home/tses89214/meme-pod/`，這樣 `.last_meme_session.json` 裡存的絕對路徑同步回本機後不用做任何轉換就能直接用（quick_meme.py 存的都是絕對路徑，見 `.last_meme_session.json` 的 `sets[].black/white`）。
- `fonts/`（638MB）已一次性 rsync 過去，之後 `quick_meme_remote.sh` 每次只同步小檔（`design_generator.py`/`quick_meme.py` 本身）過去、跑完再把 `output/` 和 `.last_meme_session.json` 同步回來。
- cjs-dev 一開始沒裝 `rsync`，`apt-get update && apt-get install -y rsync` 裝好了（trixie 的套件庫快取需要先 update 才抓得到新版本）。
- 連不上（`ssh -o BatchMode=yes -o ConnectTimeout=5` 檢查）會自動 fallback 本機 `python3 quick_meme.py`。
