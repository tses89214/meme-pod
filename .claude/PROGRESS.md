# PROGRESS

## 目前狀態（2026-08-20）
延續 2026-08-19「3,4,6,7,9」點子批次跑完最後一批 `/meme` 全流程，其中「Please Restart Monday and Try Again」被使用者取消（"這個不要了"），其餘全發：

1. It's Not a Bug, It's an Undocumented Feature（font caveat, collection Dark Tech humor）
2. Sweat Now, Shine Later（font caveat, collection Train Hard. Repeat.）：白 https://www.redbubble.com/shop/ap/183154201 / 黑 https://www.redbubble.com/shop/ap/183154390
3. low Battery need coffee to recharge（font huninn, collection Life.exe Has Stopped Working）：白 https://www.redbubble.com/shop/ap/183154914 / 黑 https://www.redbubble.com/shop/ap/183155186
4. Not late just in my own time zone（font caveat, collection Life.exe Has Stopped Working）：白 https://www.redbubble.com/shop/ap/183155700 / 黑 https://www.redbubble.com/shop/ap/183155937
5. I paused my game to be here（font oswald, collection Life.exe Has Stopped Working）：白 https://www.redbubble.com/shop/ap/183156333 / 黑 https://www.redbubble.com/shop/ap/183156556

全站累計 115 個設計（`upload_metadata.json`）。

**新踩雷**：第一個 publish（Sweat Now）連續兩次失敗在 `get_driver()`，Selenium 拋 `SessionNotCreatedException: cannot connect to chrome`。第一次以為是舊 session 殘留的 `.rb_chrome_profile/SingletonLock` 檔卡住，清掉重跑還是失敗；真正原因是這次互動式 shell 沒繼承 `DISPLAY` 環境變數（`rb_upload.py` 的 `get_driver()` 用 `headless=False`，需要真的連上 X），`echo $DISPLAY` 是空的。補上 `DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/1000` 前綴後正常啟動 Chrome。之後手動在互動 shell 跑 `publish_design.py` 都要記得帶這兩個環境變數（crontab 排程的 `pinterest_upload.py daily` 那條已經有帶，只有手動跑 `/meme` 流程時容易漏）。

## 目前狀態（2026-08-19，續）
Pinterest 趨勢點子（Battery 1%/Attitude 100%、My only paparazzi is my dog）走完 `/meme` 全流程：
- Battery 1% Attitude 100%（font anton, collection Life.exe Has Stopped Working）：白 https://www.redbubble.com/shop/ap/183119136 / 黑 https://www.redbubble.com/shop/ap/183119344，Pinterest 成功
- My Only Paparazzi Is My Dog（font pacifico, collection Paw Prints & Puns）：白 https://www.redbubble.com/shop/ap/183119699 / 黑 https://www.redbubble.com/shop/ap/183119921，Pinterest 成功，但 **Redbubble collection 沒對到**

發現並修一個新 bug：`rb_upload.py` 的 `select_collection()` 純字串比對 collection 名稱，但「Paw Prints & Puns」這個 collection 在 Redbubble 後端存的名稱字面上是「Paw Prints &amp; Puns」（建立時 & 被存成 HTML entity），比對失去等於永遠找不到、直接跳過分類。已修成比對前正規化（`&amp;` → `&`），commit 了，之後新設計會正確分類。

**未解決**：上面 dog 設計那兩個商品因為建立當下踩到這個 bug，被 Redbubble 預設繼承了複製範本原本的 collection「Dark Tech humor」（誤標）。事後想用 `/portfolio/images/<id>/edit` 頁面手動改成正確 collection 再按 `#submit-work` 送出，checkbox 當下有勾對、但重新整理頁面後又跳回「Dark Tech humor」——`#submit-work` 送出似乎不會真的儲存 collection 欄位，Redbubble 的編輯頁存 collection 可能是另一套獨立機制（可能是 checkbox onChange 直接觸發 AJAX，但點擊沒觸發到，或需要別的儲存按鈕），還沒找到正確存法。目前建議使用者手動上網站改，這兩個商品的分類還是錯的（其他都正常）。

## 目前狀態（2026-08-19）
修好 `pinterest_trends_check.py` 跟 `quote_weekly.py` 共用的一個 bug：兩支都用 `subprocess.run(["claude", "-p", ...])` 呼叫獨立 claude 子行程，但 crontab 環境 PATH 很陽春，找不到 `claude`（`FileNotFoundError: [Errno 2] No such file or directory: 'claude'`），08-19 早上 08:30 的趨勢排程因此沒送出。改成寫死絕對路徑 `/home/tses89214/.local/bin/claude`，用 `env -i` 模擬陽春 PATH 測過會過。手動補跑當天的趨勢點子成功送出。順便把 `quote_weekly.py` 排程從每週一改成每天 10:00（使用者要求）。

補建 2 個 Pinterest board（`Adult Class System`、`Life.exe Has Stopped Working`），這兩個 Redbubble collection 之前沒有對應 board，發文都退回預設 board，現在帳號共 11 個 board、都對上了。

修 mockup 選圖對比度 bug：`pinterest_upload.py` 的 `get_mockup_image()` 從商品頁隨機挑一張真實照片當 pin 圖，同一 listing 的 26 種商品款式裡少數（如 active_tee）預設是深色，黑字設計疊上去會看不到字。改成依印花顏色（`ink` 參數）過濾掉會撞色的底色（黑字避深色底、白字避淺色底，双向判斷），過濾不到候選才退回原始清單。目前系統只會 pin 黑字版（白T listing），所以白字分支目前用不到，是為了以後萬一發黑T listing 也對的保險。

萬聖節主題 Dad Jokes / Tech Humor 3 個設計走完 `/meme` 全流程：
1. I'm Not Afraid of Ghosts / I'm Afraid of My WIFE（font caveat, collection Dad Jokes）：白 https://www.redbubble.com/shop/ap/183106867 / 黑 https://www.redbubble.com/shop/ap/183107052
2. My Scary Costume Monday Morning（font caveat, collection Life.exe Has Stopped Working）：白 https://www.redbubble.com/shop/ap/183108515 / 黑 https://www.redbubble.com/shop/ap/183108688
3. Trick or Tequila（font pacifico, collection Adult Class System）：白 https://www.redbubble.com/shop/ap/183109092 / 黑 https://www.redbubble.com/shop/ap/183109264

三個 Pinterest 都成功，因為 board 已經補齊，都直接進對應主題 board，沒有退回預設。第 4 個點子（Bug/Haunted House）字型預覽出來使用者覺得醜，取消不發。全站累計 106 個設計。

**新踩雷／教訓**：發布過程中用 `while pgrep -f pinterest_explore_like.py > /dev/null; do sleep 15; done` 等排程結束，結果自己這行指令的完整 command line 本身就含有 `pinterest_explore_like.py` 字串，被自己的 `pgrep -f` 誤抓到，導致以為排程一直在跑，卡等超過 8 小時。之後這種等待迴圈要用更精確的 pattern（例如 `pgrep -f 'python3.*pinterest_explore_like\.py'` 且避開迴圈自身指令，或改成先 `ps aux | grep` 一次性檢查而非在 pgrep 條件式裡放同名字串）。

## 目前狀態（2026-08-18，舊）
新增 `pinterest_trends_check.py`：每天 08:30 crontab 排程，Selenium 抓 Pinterest Trends 頁面文字，丟給隔離的 `claude -p` 子行程判斷「趨勢能不能延伸成梗圖 T 恤點子」（不硬套，沒有適合的就明講），結果直接用 Telegram Bot API 傳給使用者（不透過 MCP，避免搶常駐 bot session）。

當天測試產出 3 個點子並全部走完 `/meme` 完整流程發布：
1. Dressed for Success Crying Inside（font caveat, collection Adult Class System）：白 https://www.redbubble.com/shop/ap/183093771 / 黑 https://www.redbubble.com/shop/ap/183093956
2. Mode Activated: Zombie Mode（font cubic11, collection Adult Class System）：白 https://www.redbubble.com/shop/ap/183094217 / 黑 https://www.redbubble.com/shop/ap/183094364
3. My Personality Is a Bunch of Useless Skills（font anton, collection Life.exe Has Stopped Working）：白 https://www.redbubble.com/shop/ap/183094584 / 黑 https://www.redbubble.com/shop/ap/183094696

三個 Pinterest 都成功，都因為 collection 沒有同名 board 退回預設 board（正常 fallback，非 bug）。三個設計的 tags/description 都依使用者要求塞入對應趨勢關鍵字（stylish work attire、skeleton/zombie mode、bag charms）以利趨勢流量。全站累計 103 個設計。

## 目前狀態（2026-08-17，舊）
Pinterest 曝光低的問題，整批處理：

1. **Pinterest board 依 collection 分流**：`publish_design.py` 往後發布會把 collection 存進 `upload_metadata.json`（`meta["collection"]`）；`pinterest_upload.py` 的 `fill_and_publish_pin()` 改成優先用 `meta["collection"]` 選 board，找不到對應 board 就退回預設 board（`NoSuchElementException` 自動 fallback，不會整支爆掉）。
2. **舊資料回填**：100 個設計全部補上 `collection` 欄位——3 批有 commit/PROGRESS 紀錄可查的（漢字/Bilingual 12、Dad Jokes 5、Paw Prints & Puns 6）照原始紀錄回填；發現帳號上其實還有 5 個早就建好、名字取得不錯但沒接進程式碼的 board（Gym & Motivation Tees、Wholesome & Fun Lifestyle Tees、Gamer Life Level-Up Tees、Funny Work & Office Meme Tees、Bilingual Chinese Design Tees），剩下 77 個設計依主題人工分類進這 5 個（28/25/8/8/8/6/5，詳細分布見 git log c860ad8）。
3. **新建 board**：Pinterest 上補建「漢字 / Bilingual」「Paw Prints & Puns」兩個 board（Dad Jokes 之前就有）。
4. **預設 board 改名**：`Funny Meme Shirts` → `Funny Sarcastic Meme T-Shirts`（塞進常見搜尋詞），Pinterest 上同步改名，115 個既有 pin 不受影響，繼續當作抓不到對應 collection 時的備援 board。
5. **pin 描述加 SEO**：`build_pin_copy()` 改成 caption + description 兩段合併（不再兩選一）+ 自動附加前 5 個 tag 當 `#hashtag`，截斷在 500 字內。
6. **發文量調整**：`pinterest_upload.py daily` 排程從隨機 1-2 篇改成固定兩班各 3 篇（11:20 + 16:20，crontab），一天共 6 篇。

**決策**：Rich Pins 走不通（Redbubble 商品頁沒有 `og:type=product` metadata，且網域驗證需要 Redbubble 自己的權限，賣家做不到）；group board 加人 ROI 偏低（Pinterest 演算法已從 board 中心轉成內容相關性，該策略重要性下降），兩者都決定不投入。刻意把每個設計同時發去主題 board + 預設全部 board 的想法也決定不做——重複發同張圖有洗版疑慮，預設 board 保留 fallback 功能即可，不用手動雙發。

Pinterest Ads 使用者還沒決定，未實作。

效果要等 board 重新學分類，估 1-2 週才會反映在流量上，目前判斷太早。

## 目前狀態（2026-08-15，舊）
「漢字 / Bilingual」collection 再補 3 個中文餐點設計：小籠包 (Xiaolongbao)、割包 (Gua Bao)、肉圓 (Bawan)，字型 huninn，3/3 全部成功（黑白範本 + Pinterest）。
- 小籠包：白 https://www.redbubble.com/shop/ap/183022990 / 黑 https://www.redbubble.com/shop/ap/183023121
- 割包：白 https://www.redbubble.com/shop/ap/183023391 / 黑 https://www.redbubble.com/shop/ap/183023667
- 肉圓：白 https://www.redbubble.com/shop/ap/183024086 / 黑 https://www.redbubble.com/shop/ap/183024465

漢字/Bilingual collection 累計 12 個設計，全站累計 91 個設計。

**新發現的失敗模式：Chrome profile 搶佔衝突**——手動跑 `publish_design.py` 跟排程中的 `rb_explore_like.py`（09/13/20:00）或 `pinterest_explore_like.py`（10/14/21:00）如果時間窗重疊，會搶 `.rb_chrome_profile`，導致手動這邊 `SessionNotCreatedException`（連不上 chrome）。今天 13:20 左右發生一次，`pkill -9` 清 chrome process 時，意外把當時還在跑的 `rb_explore_like.py` 13:00 排程也砍掉（該次排程沒跑完就掛了，log 留下 traceback）——不影響大局，下個排程時間會自己再跑。**教訓：清 chrome process 前先 `ps aux | grep -E 'rb_explore_like|pinterest_explore_like'` 確認沒有排程正在跑。**

**另一個新發現：Chrome 有時候 `driver.quit()` 後沒有真的清乾淨**，process 還留著佔用 `.rb_chrome_profile`，下一個設計要發布前最好 `ps aux | grep chromium` 檢查一下，有殘留就 `pkill -9 -f '.rb_chrome_profile'` 再開始。

## 目前狀態（2026-08-14，舊）
「漢字 / Bilingual」collection 再補 4 個台灣小吃設計：珍珠奶茶 (Bubble Tea)、鹽酥雞 (Salt and Pepper Chicken)、蚵仔煎 (Oyster Omelette)、臭豆腐 (Stinky Tofu)，全部字型 huninn，4/4 全部成功（黑白範本 + Pinterest）。
- 珍珠奶茶：白 https://www.redbubble.com/shop/ap/183001975 / 黑 https://www.redbubble.com/shop/ap/183002660
- 鹽酥雞：白 https://www.redbubble.com/shop/ap/183003290 / 黑 https://www.redbubble.com/shop/ap/183004010
- 蚵仔煎：白 https://www.redbubble.com/shop/ap/183004584 / 黑 https://www.redbubble.com/shop/ap/183004844
- 臭豆腐：白 https://www.redbubble.com/shop/ap/183005289 / 黑 https://www.redbubble.com/shop/ap/183005599

漢字/Bilingual collection 累計 9 個設計，全站累計 88 個設計。

**新發現的失敗模式（今天多次遇到）**：Redbubble white/black template 發布步驟偶爾會卡住——`publish_design.py` process 還活著，但 Chrome renderer process 頂在 ~100% CPU、log 完全沒新輸出，卡 15-30 分鐘。有時等待視窗內自己解決（珍珠奶茶白底、鹽酥雞白底都是這樣），有時真的卡死需要 `kill` process + `pkill -f '.rb_chrome_profile'` 後，用單一 variant 的手動重試修復（跟 08-13 滷肉飯黑底那次一樣的手法：直接呼叫 `fill_design(images['white' 或 'black'], target_url=BLACK_TEMPLATE_DUP_URL 或 WHITE_TEMPLATE_DUP_URL)`）——珍珠奶茶黑底、鹽酥雞黑底、蚵仔煎黑底都是這樣修好的。判斷基準：process 存活但同一步驟 15-20 分鐘內 log 零進度、且有 Chrome renderer process 頂在接近 100% CPU，才視為卡死，不要看到「有點慢」就急著砍。

**另一個新發現**：Pinterest 發布步驟也出現過一次靜默失敗（蚵仔煎，`fill_and_publish_pin` 回傳 `False`，log 沒有任何錯誤訊息），單純重跑 `publish_pinterest()` 就成功，原因未查——如果之後常態發生，要去看 `pinterest_upload.py` 的 `fill_and_publish_pin` 在什麼情況下會靜默回傳 `False`。

**`rb_explore_like.py` 調整**：使用者要求增加互動量，預設按讚數從固定 20 改成隨機 20-30（`random.randint(20, 30)`），crontab 從每天一次(09:00) 改成每天三次(09:00/13:00/20:00)。

**新增 `pinterest_explore_like.py`**（Pinterest 版隨機瀏覽按愛心，仿 `rb_explore_like.py`）：流程 homefeed → 收集 `/pin/` 連結 → 逐個點進去按「回應」按鈕（aria-label="回應"，不是「儲存」，使用者要的是按愛心不是收藏）。使用者提供的 hashed CSS selector（`.sSBu24 .gEQpi5 .XjRT60`）沒用，改用穩定的 `button[aria-label="回應"]`。踩過的雷：homefeed 是虛擬捲動 DOM，`collect_pin_links()` 抓連結時要包 `try/except StaleElementReferenceException`，不然邊抓邊重繪會炸。成功判斷用 `aria-pressed` 屬性（true=已按），實測 3/3 成功且截圖確認愛心變實心、計數 +1，判斷可靠。預設隨機 45-55 個/次，crontab 每天三次 10:00/14:00/21:00（跟 `rb_explore_like.py` 的 09:00/13:00/20:00 錯開避免搶 Chrome profile）。

## 目前狀態（2026-08-13，舊）
新增 collection「漢字 / Bilingual」（台灣小吃雙關/雙語系列），一口氣發了 5 個設計：貢丸（字型 cubic11）、蛋花湯、滷肉飯、牛肉麵、炸雞排（後四個字型 huninn）。4/5 完全成功（黑白範本 + Pinterest 都成功）。**滷肉飯黑底範本 publish 失敗**：`rb_upload.py` 該步驟回傳 `None`（duplicate 頁面網址解析不到商品網址），但整支 process exit code 是 0、Pinterest 仍成功——這是新發現的失敗模式，之前都沒遇過「白底成功、黑底失敗、整體卻顯示完成」的情況，之後每次 publish 都要照實際輸出檔案核對兩個範本的網址，不能只看「=== 完成 ===」那行。已 Telegram 通知使用者，使用者回覆「重跑」後，寫一支只重跑黑底範本的一次性 script（直接呼叫 `fill_design(images['white'], target_url=BLACK_TEMPLATE_DUP_URL)`，不碰白底、不重跑 Pinterest）重試，**成功**：https://www.redbubble.com/shop/ap/182961877 。至此 5/5 全部成功。
目前累計 84 個設計。

## 目前狀態（2026-08-09，舊）
Redbubble + Pinterest 全自動管線穩定運作中。目前 79 個設計，全部有商品網址並發過 Pinterest（4 筆更早期的舊設計對不到網址，使用者說先不管，見下）。

新增一個 collection「Dad Jokes」（使用者自己在 Redbubble 後台建的）+ 對應 Pinterest board（我建的，選擇器記在 MEMORY.md），本次會話又補發了 3 個 dad-joke 設計進去（Mistakes are proof..., Seafood diet, Certified Dad 單行版+兩行版）。

2026-08-09 新增第二個 collection「Paw Prints & Puns」（寵物人主題，使用者在 Redbubble 後台建的，我建議的名字），一口氣發了 6 個設計進去（Fur mom/dad、My cat/dog owns me、My Dog need me、Purr-fectly exhausted parent）。`quote_search.py` 的 `DEFAULT_QUERIES` 也加了寵物雙關語錄的搜尋類別，之後 `/meme` 點子發想會一起搜。

**多設計連續發布時的已知限制**：`.last_meme_session.json` 一次只能存一個設計的 render 結果，`publish_design.py` 會驗證 `text` 是否匹配。排隊多個設計時，順序是：先把每個設計的字型預覽都跑過、收集好使用者選的字型，寫好全部 metadata，再依序「重新 render → 立刻 publish」一個接一個做，不能提前全部 render 完再一次發布（後面 render 的會蓋掉前面的 session）。

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
- `pinterest_explore_like.py`：homefeed 隨機瀏覽別人的 pin 按愛心，crontab 每天三次 10:00/14:00/21:00。
- `quick_meme_remote.sh`：字型預覽遠端算 + 自動 fallback 本機。

技術細節、選擇器、踩過的雷都記在 DECISIONS.md、MEMORY.md 和 `skills/meme-pinterest.md`。

## 下一步（下次會話上班打卡先看這）
1. 4 筆舊設計對不到 Redbubble 商品網址，使用者說先不管：Staff Adult Lv.99 Funny Gaming Meme、Orange Juice Sweat Zhongshan Qiang Abstract Chinese Tee、Cat Time Funny Cute Meme Tee、I Believe in Air Conditioner Funny Summer Meme Tee。
2. Pinterest 個人檔案簡介自動化失敗過（send_keys 漏字元 + JS setter 存不進去），使用者已手動貼過，之後不用再碰。
3. `design_generator.py` 的 `clean_text()` 白名單 2026-08-06 補了 `% = & # @ +`，如果之後又有符號被靜默濾掉（畫面上文字消失/跟預期不符），先檢查這個白名單，不用重新除錯半天。
4. `quote_weekly.py` 週一 10:00 才第一次真的透過 cron 跑，還沒看過真實排程觸發的結果，下次上班可以順便確認 `quote_weekly.log` 有沒有正常產生。
5. Google Drive 備份 token 過期（`drive_upload.py batch` 2026-08-07 起失敗，`invalid_grant: Token has been expired or revoked`），需要重新走一次 OAuth 授權流程才能繼續備份，這段期間累積的設計圖都還沒備份到 Drive。
6. `bot_mailbox_check.py` 2026-08-07 改成會用隔離的 `claude -p` 自動回覆純資訊性 mailbox 訊息（規則見 `~/.claude/bot-mailbox/README.md`），還沒實際收過一次別的 bot 主動問問題來驗證這條路徑真的有效。
7. `upload_metadata.json` 已 commit 乾淨，84 筆全部同步。
