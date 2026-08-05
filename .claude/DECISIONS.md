# DECISIONS

紀錄重要設計決策：做了什麼、為什麼、取捨是什麼。只記真正影響後續工作的決定，不記瑣事。

## 2026-08-03 — 導入會話打卡流程
每次會話開始讀 PROGRESS.md + DECISIONS.md，結束前更新兩者並把 local 記憶寫進 MEMORY.md、commit 完成的工作。
短任務（單次會話內完成）可跳過更新。
原因：專案是長期、跨會話的自動化管線，避免每次重啟都要重新摸索目前卡在哪。

## 2026-08-03 — Pinterest 導流：Phase 1 手動、不上自動化工具
評估過 `SoCloseSociety/PinterestBulkPostBot`（22★, MIT, Selenium）。決定先不用，也不自己寫 bot。
10 支種子 pin 全部手動貼，連結一律帶 `utm_source=pinterest&utm_medium=social&utm_campaign=pilot`，圖用 Redbubble 自動生成的 mockup 照（不是 output/ 的透明底設計圖），先開一個大 board「Funny Meme Shirts」不分子題材。
原因：Pinterest 策略本身還沒驗證過（帳號剛轉 Business、shop 網址剛送審），這階段裝自動化工具是本末倒置——量還沒起來、方向對不對都不知道，先手動測 3-4 週看有沒有反應，之後量衝到單週 30+ 支才回頭評估自動化。
細節與後續 TODO 見 `skills/meme-pinterest.md`。

**2026-08-04 更新：此決定被使用者明確推翻。** 問過使用者「要跳過驗證直接接自動發文嗎」，回答「跳過驗證直接接自動發文」。改成：生產設計完直接自動發 Pinterest，不等 3-4 週手動驗證信號。原本手動測水溫那套（10 支種子清單、UTM 連結）步驟不變，只是改成自動執行不用人工手動貼。

## 2026-08-03 — Redbubble 上傳：新品一律用「Duplicate design」，不能開 New Work
使用者要求：新品都要從既有設計「複製」出來（Redbubble 會複製該設計在各商品類型上的圖片縮放/位置設定），不能用空白的 New Work 表單——不然每個商品類型的圖片大小位置都要重新手動調整。
黑底設計複製自黑底範本（work id 179795066），白底設計複製自白底範本（work id 179795087），兩個 id 固定當範本用。
複製完仍要肉眼檢查圖片在各商品上的比例對不對，不能盲目自動送出。
原因：使用者原話——圖案大小需要人調到合適比例，避免「衣服很大圖很小」或相反。

技術細節（已用瀏覽器實測確認，供之後接手時參考）：
- Duplicate 網址：`https://www.redbubble.com/portfolio/images/<work_id>-<slug>/duplicate`
- 該頁面過 Cloudflare 需要等（實測 30-90 秒，非死擋，純等待即可，不用人手動點驗證框）
- 該頁面欄位 id 跟原本 New Work 表單共用：`#work_title_{lang}`、`#work_description_{lang}`（lang: en/de/fr/es）
- 換圖：`#select-image-base`（使用者用瀏覽器 DOM 檢查器實測確認，不是 `select-image-large_clothing`——這個選錯了圖片不會真的換掉，但也不會報錯，要看截圖才會發現）。
- 版權確認框：`#rightsDeclaration`（checkbox，name="rights_declaration"）— 已接進 `fill_design()`，送出前自動勾選。
- 送出鈕：`#submit-work`（跟原本 New Work 表單相同）

## 2026-08-04 — Redbubble Tags 欄位選擇器：用使用者原本寫好的邏輯解掉
使用者帶回自己先前用 DrissionPage 寫的「填寫產品資訊」腳本（不含上傳圖片、不含勾框送出）。決定：只擷取邏輯移植進現有 `rb_upload.py`（Selenium + undetected-chromedriver），不改用 DrissionPage——今天才剛驗證過 Selenium/UC 這套在這台 Pi 上能穩定過 Cloudflare、session 能持久化，換函式庫要重驗證一次不划算，使用者也明確說「擷取需要的地方去用就好」。

移植進 `rb_upload.py` 的東西：
- 上一輪卡住的 Tags 欄位解法：`#main-tag-{lang}`（單一主標籤）與 `#supporting-tags-{lang}`（逗號分隔的其餘標籤）是兩個各自獨立的欄位，不是原本猜測的 `#work_tag_editor_{lang}` 隱藏欄位。兩者在 duplicate 頁面上也確認存在。
- 語言分頁改用 XPath 點擊（`//*[@id="add-new-work"]/div/div[2]/div/div/label[N]/h3`，N=2/3/4 對應 de/fr/es，en 不用點是預設分頁），取代原本沒驗證過的 `label[for='language-tab-{lang}']` CSS 選擇器猜測。
- 這頁的 React 欄位 plain `.clear()` 常清不乾淨：改用「JS 清空 value + Ctrl+A+Backspace + 硬送 30 次 Backspace」保底再輸入（`clear_and_input()`），Title/Main tag/Supporting tags/Description 都套用同一招。

還沒補的：換圖（`select-image-large_clothing`）跟實際跑一次全流程驗證。

## 2026-08-04 — Redbubble 全流程實測結果：換圖選擇器修正、換圖後極慢是正常現象
用「My faith is beer」(fredoka 字型) 對黑底範本 (179795066) 實測 `fill_design()` 全流程（submit=False）：
- 換圖 selector 修正為 `#select-image-base`（使用者實測確認），修正前用 `select-image-large_clothing` 不會報錯但圖沒真的換掉，容易誤判成功。
- 四語言 title/main tag/supporting tags/description 全部正確填入，版權框正確勾選，範本原本的分類設定（media type、collections）有跟著複製過來，符合預期。
- 把 Title/Description 的清空後輸入從 `send_keys()` 逐字打字改成 JS 原生 setter + dispatch `input`/`change` 事件（`clear_and_input()` 內），這段本身是有效加速，但不是這次耗時的主因。
- 真正的耗時主因：用 `#select-image-base` 真的觸發換圖後，Redbubble 要重算幾十種商品類型的 mockup，頁面忙碌導致後續每個操作都變慢，全流程跑了約 1173 秒（近 20 分鐘）。換錯圖（不觸發真實處理）的那次只要幾十秒。這個延遲研判是 Redbubble 後端/前端處理圖片的固有成本，換人手動操作大概也要等類似時間，不是腳本效率問題，之後排程批次上架要把這個時間成本算進去。

還沒做：實際按下 submit-work 送出測試（目前都停在 submit=False 的確認畫面）。

## 2026-08-04 — Redbubble 實際上架成功：兩個設計、各黑白兩版，共 4 筆
使用者指示「上這兩個，記得每個設計都要上黑白兩個版本」。實際跑了 `fill_design(..., submit=True)`：
- My Faith Is Beer Funny Drinking Tee：白字圖→黑範本、黑字圖→白範本，各一筆
- Universe Grant Me Power Cosmic Anime Tee：同上各一筆
4 筆全部拿到 Redbubble「Congratulations! Your design is published.」確認頁，mockup 截圖檢查圖片在 T恤/帽踢上的大小比例正常（範本複製的縮放設定有生效）。

黑底/白底範本配對邏輯（本回合確認）：黑底範本 (179795066) 配「白字」透明圖，白底範本 (179795087) 配「黑字」透明圖——卡片背景色跟文字顏色要對比，跟 `output/` 檔名的 black/white（代表文字顏色，不是底色）是反過來對應的，之後配對時要注意別搞反。

`upload_metadata.json` 這兩筆已標 `uploaded: true`，但檔案本身還有使用者自己先前的未 commit 修改混在一起，沒有一併 commit，留給使用者自己處理。

## 2026-08-04 — Redbubble 上傳偶發 timeout：Selenium command timeout 拉到 600 秒
第三筆設計（Actions Speak Louder Than Words，重新用 dancing script 字型再上一次，使用者確認即使 metadata 已有 uploaded:true 也要照跑）上傳時，白字配黑範本那版第一次跑遇到 `HTTPConnectionPool ... Read timed out (read timeout=120)`——是 Selenium/urllib3 對單一 command 的預設 120 秒 timeout，跟已知的「換圖後頁面很忙」問題疊加，某次單一操作卡超過 120 秒就直接整個 exception。
修法：`get_driver()` 建立後呼叫 `driver.command_executor.set_timeout(600)`，把單一 command 的等待上限拉到 10 分鐘。重跑同一版之後成功。
兩版最終都上架成功（black-text→white 範本、white-text→black 範本各一筆）。
結論：之後只要遇到這類 read timeout，先檢查是不是這個 command-level timeout 太短，不是流程邏輯錯。

## 2026-08-04 — Pinterest 自動發文：第一個真的 pin 發布成功
承接上面「跳過驗證直接接自動發文」的決定，動手做完整流程：
1. 建 board「Funny Meme Shirts」（帳號原本 0 個 board）——`#boardEditName` 填名稱、`#secret` 不勾（公開）、`[data-test-id="board-form-submit-button"]` 送出，沒卡 CAPTCHA。
2. 「儲存自網站」踩雷：餵 Redbubble 商品網址進去，Pinterest 抓回來的是頁面雜圖示（大頭貼、愛心 icon），不是商品照，這條路廢了。改回本地檔案直接 `send_keys()` 上傳，跟 Redbubble 那套一樣的招。
3. 標題／描述／目的地連結／board 選擇，全部一次填對，`board-row-<board 名稱>` 這個選擇器格式很穩定好用。
4. 送出後拿到「你已建立一個 Pin！」確認彈窗 + 「已儲存到 Funny Meme Shirts」提示，確認真的發布成功。

商品連結來源：目前是從上傳 Redbubble 時的 promote 確認頁（`/studio/promote/<work_id>`）上找文字為「View」的 `<a>` 連結抓 `href`，得到 `redbubble.com/shop/ap/<id>` 這種格式，再自己加 `?utm_source=pinterest&utm_medium=social&utm_campaign=auto`。這個抓法依賴「剛好有 promote 頁網址」，還沒有通用的「給標題就能查到商品網址」機制——這是下一步要補的缺口，見 `skills/meme-pinterest.md` Open TODOs。

圖片目前用本地的透明設計圖（非商品 mockup 照），Pinterest 有跳出「建議長寬比至少 2:3」的非阻擋警告（我們的圖是正方形）。

還沒做：批次迴圈（一次跑多個設計）、真的商品 mockup 圖來源、「哪些設計已經 pin 過」的追蹤欄位。

## 2026-08-04 — Pinterest 批次管線補完：`pinterest_upload.py`
補完上面留的三個缺口：
1. `rb_upload.py` 的 `fill_design()` 送出後自動抓 View 連結存 `product_url`（return 值），不用再手動去 promote 頁挖。
2. 真的商品 mockup 圖：意外發現 Redbubble 公開商品頁（`/shop/ap/<id>`）完全不擋 Cloudflare，純 `requests` 就能抓，連瀏覽器都不用開。圖片網址不是 `<img src>`，是藏在頁面內嵌的 client-hydration JSON 裡，斜線被跳脫成 `{{%2F}}`，要用 regex 撈 `square_close_portrait...x1000...jpg` 這個模式再還原跳脫字元。找不到就退回 `og:image`（純設計平面圖）當備案。
3. `upload_metadata.json` 加 `redbubble_url` + `pinned` 兩個欄位，`pinned` 邏輯跟既有的 `uploaded` 一樣。

新增 `pinterest_upload.py`（`list`/`batch`/`one <關鍵字>`），跟 `rb_upload.py` 共用同一個瀏覽器 profile/登入。實測：Universe Grant Me Power 用 `one` 指令跑，抓到真實 mockup 照（毛衣實拍）、自動判斷「已建立一個 Pin」成功訊息、自動存回 `pinned: true`，全程沒人手動介入。

Beer 那筆是手動測試時發的，事後補標 `pinned: true`（沒有真的重跑一次自動流程去發第二次）。

## 2026-08-04 — 串成單一指令：`publish_design.py`
使用者要求把整條流程接起來，但選字型這步依然要留給使用者自己決定（明確講「選字型一樣交給我」）。
分界線定在：字型選擇 + metadata 文案撰寫（標題/描述/tags/翻譯）是需要判斷的工作，留給人／Claude；選完字型、metadata 寫好之後，剩下全部自動：Redbubble 黑白兩版上架 → 抓商品網址 → Pinterest 發 pin，一個指令 `python publish_design.py "<text>" <font>` 跑完。
`/meme` skill 的 step 3 已改成呼叫這支，取代舊的 Google Drive 備份路徑（Drive 變成非預設、使用者要才跑）。

**2026-08-04 補充：Google Drive 備份使用者說還是要做**，不是非預設——上面那句寫錯了。已改回 `/meme` flow 的固定步驟（跑在 Redbubble/Pinterest 之後，不卡住它們），見 skill 文件最新版。

## 2026-08-04 — Redbubble Collection 選擇：只能選現有的，不做新增
使用者要求上架時能選要放哪個 collection，明確說「新增不要做，幫我選擇就好」。
技術細節：collection 勾選框 id 是 `work_group_ids_<id>`，對應的名稱不是標準 `label[for]`，是 parent `<label title="名稱">`，勾選框的 `name` 屬性是 `work[collection_ids][<id>]`。目前這個範本（duplicate 來源）底下有 5 個 collection：漢字/Bilingual、Adult Class System、Life.exe Has Stopped Working、Train Hard. Repeat.、Dark Tech humor（範本預設勾這個）。
實作：`rb_upload.py` 加 `list_collections()`/`select_collection()`，選了哪個就只勾那個（取消其他），沒給就保留範本原本勾的。新增 CLI `python rb_upload.py collections` 方便先查現有選項。`publish_design.py` 第三個參數就是 collection 名稱，`/meme` flow 選字型時一併問使用者。找不到對應名稱時直接跳過並印警告，不會自己新增。

## 2026-08-04 — 舊設計補發 Pinterest：manage_works 分頁比對出商品網址
使用者要求把「今天自動化之前」就上架的舊設計也補發 Pinterest。這些設計沒有存商品網址（今天的自動抓網址功能是後來才加的），解法：
- `redbubble.com/portfolio/manage_works` 後台管理頁每個作品卡片有「Edit」連結，格式 `/portfolio/images/<work_id>-<title-slug>/edit`，這個 slug 就是商品公開網址 `redbubble.com/shop/ap/<work_id>` 的來源，不用一個一個開 promote 頁。
- 這頁是真分頁（`?page=2`，不是無限捲動），第一輪只抓到第 1 頁（24 個作品/48 個連結）漏了第 2 頁，要照 `rel="next"` 連結把每一頁都load 完才抓得全（2 頁共 42 個作品/84 個連結）。
- 用「metadata 標題 slugify 後比對 work slug」配對，slugify 規則要注意：句點 `.` 要轉成 `-` 不是直接刪掉（例如 "Lv.1" 對應 "lv-1"），刪掉會比對失敗。
- 4 筆比對不到：Staff Adult Lv.99 Funny Gaming Meme、Orange Juice Sweat Zhongshan Qiang Abstract Chinese Tee、Cat Time Funny Cute Meme Tee、I Believe in Air Conditioner Funny Summer Meme Tee——可能當初沒有真的上架成功（`uploaded:true` 標記可能不準），使用者說先不管，之後要人工去後台核對。
- 另外 3 筆是標題有出入的模糊比對（人工核對過詞序/用字差異後手動配對，不是自動化邏輯）：Mushroom Funny Food Bilingual Tee、Mist Bilingual Chinese Nature Tee、Chimi Moryo Chinese Demons Mythology Tee——Redbubble 上的實際標題跟 metadata 存的有些微差異（詞序或單複數）。

抓 mockup 圖也順手改了：原本永遠抓第一張（`candidates[0]`），使用者要求隨機化避免每次都同一件商品照，改成去重後 `random.choice()`。

結果：42 筆裡 42 筆都補上網址並發了 Pinterest（一次批次 20 筆 + 一次 18 筆，其中 1 筆判斷失敗但實際有成功，重跑後確認），4 筆無網址擱置。這也算是第一次批次量測試（38 筆一次跑完），沒出穩定性問題。

## 2026-08-04 — Pinterest board 拆分：5 個主題 board + 保留舊的當「全部商品」
使用者確認 5 個主題分類（見前面草稿），board 都建好後把 42 支既有設計依分類重新發了一次 pin 到對應主題 board（`fill_and_publish_pin()` 的 `board` 參數化，見同名 commit）。
關鍵決定：一開始想刪掉舊的「Funny Meme Shirts」大 board 避免重複內容，後來使用者提出「一個設計可以出現在多個 board」+ 想要一個「所有商品」大 board 的需求——查了一下 Pinterest 本來就允許同一設計發到多個 board（各自獨立的 pin），所以**不刪舊 board**，直接讓它變成「所有商品」大 board，跟 5 個主題 board 並存。省了一次刪除的工。
42 筆全部重發成功（用 `pin_reassign_boards.py`，scratchpad 裡，內建 title→board 對照表）。

個人檔案簡介編輯踩了大坑：send_keys 打字在這個特定欄位會確定性地漏字元（同一段文字每次漏同一個位置，不是隨機 flaky），JS 原生 setter 那招（Redbubble 那邊有效）在這裡也失敗——值有設進去但「儲存」按鈕的 disabled 狀態沒被觸發，存了等於沒存。花了 7-8 輪嘗試都沒解決，最後放棄自動化，請使用者自己手動貼（10 秒的事）。這個欄位的可靠自動化方法還沒找到，之後如果要再碰，別重複踩同樣的坑，直接问使用者手動處理更划算。

## 2026-08-04 — Pin 文案風格：5 種語氣，都帶 tag 朋友鉤子，隨機抽不是全發
使用者想要文案更有個性，不要純商品介紹。來回反覆確認後定案 5 種風格：搞笑吐槽、日記/心情碎念、直白吐槽、tag 朋友、瘋癲版（ㄎㄧㄤ）——而且五種都要能融入「tag 朋友」的鉤子（不是獨立第 4 種而已，是每種都能加這個元素）。
使用方式：5 種文案存成素材庫，發文時隨機抽 1 種配隨機 mockup，不是一次把 5 種都發出去（42 設計 × 5 篇 = 210 篇太暴力，跟「穩定發文」的 best practice 衝突）。同一設計未來要重複曝光時，重新發一次會自動抽到不同組合。
使用者也要求排程：之後每天自動發 1-2 篇（設計產出速度比發文速度快，需要細水長流），這步還沒做，是下一步。
還沒動手把這套風格寫進全部設計的 metadata，只在對話裡試寫了 3 個設計的範例文案取得使用者認可。

Hashtag 補充查證：Pinterest 官方 2026 年建議至多 2-5 個 hashtag，排名權重僅約 1%，關鍵字在標題/描述才是主力，加不加都不會扣分。

## 2026-08-05 — 文案全部寫完 + 每日排程接上本機 crontab（不是雲端 /schedule）
5 種文案風格（搞笑/日記/直白吐槽/tag朋友/瘋癲）幫全部 48 個設計都寫好了，存進 `upload_metadata.json` 的 `pinterest_captions` 欄位（每個設計一個 list，5 個字串）。`pinterest_upload.py` 的 `build_pin_copy()` 改成有這欄位就 `random.choice()`，沒有才退回舊的商品描述當備案。

新增 `pinterest_upload.py daily [count]`：從全部有商品網址的設計（不管 pinned 與否）隨機挑 N 個（不給 count 就隨機 1-2 個，配合使用者要的節奏）重新發文，每次都是新的隨機 caption + 隨機 mockup。這支是給排程用的，跟 `batch`/`one`（只處理還沒 pin 過的新設計）分開。

排程踩了一個大坑：一開始叫了 `/schedule` skill（`RemoteTrigger`），才發現這是建立**雲端** Claude 代理排程，跑在 Anthropic 雲端隔離環境，完全碰不到這台 Pi 本機的瀏覽器 session/`.rb_chrome_profile`/display——用這個排程 `pinterest_upload.py` 一定失敗。改用本機 `crontab`：`20 11 * * *` 執行 `pinterest_upload.py daily`（Asia/Taipei 時區，本機系統時區）。

crontab 安裝過程另外踩一個環境雷：這台機器的 `crontab <file>` 指令，檔案路徑太長/太深層（例如 scratchpad 底下那種長路徑）會讀到一半報 "No such file or directory"（檔案其實存在），解法是先複製到 `/tmp/xxx.txt` 這種短路徑再安裝。已記進 MEMORY.md，下次直接用短路徑，不用重新除錯。

## 2026-08-05 — upload_metadata.json 競態條件修好；意外把自己的 TG 連線弄斷
早上發現 Focus、後來又發現 PRAF 的 metadata 整筆消失。查了 git 歷史抓包：兇手是 `publish_design.py`／`pinterest_upload.py` 各自的存檔邏輯——一輪跑好幾分鐘，中途把整包 metadata 存記憶體裡，結束才整包蓋回檔案。這中間如果我另外用 Edit 幫下一個設計寫 metadata 進去，等前一輪存檔那刻就把新加的蓋掉了（不是 cron 造成的——有查 `pinterest_daily.log`，cron 那次其實是撞上我同時在跑的互動瀏覽器搶同一份 `.rb_chrome_profile`，直接在啟動瀏覽器那步就整個掛掉，連檔案都還沒碰到）。
修法：兩支腳本都改成「即用即讀最新檔案、只更新這一筆（用 `text` 欄位比對）、立刻存檔」，不再拿舊的整包陣列去蓋檔案。Focus、PRAF 的 metadata 從 git 歷史救回來，順便幫這兩個 + Sip + Fat Otaku 補上遺漏的 5 種 Pinterest 文案（`pinterest_captions`）。

同一次會話另外意外搞出一個新坑：為了驗證「排程能不能連 Telegram MCP」，跑了一次 `claude mcp list`（純粹想看 telegram plugin 健不健康），結果**這個 session 自己的 telegram plugin 子行程直接消失**，`reply` 工具整個叫不出來，沒辦法回 TG 了。細節、之後怎麼避開，記在 MEMORY.md「這台機器跑多個 Telegram bot session」那節——重點是之後絕對不要在 Bash 裡跑裸的 `claude` 指令。

靠 `~/start_all_claude_bots.sh`（每 5 分鐘 cron 檢查 tmux session 存不存在，不存在就用 `--continue` 重開）復原：使用者確認「都弄完之後自己重啟」，等 Focus 那筆的 `publish_design.py` 走到還沒送出（安全可砍）的階段後，主動 `tmux kill-session -t claude_bg_memepod`，5 分鐘內自動重開、TG 連線恢復正常、對話透過 `--continue` 接上。過程中發現砍 session 會讓 Chrome 留下不會自己清的 `SingletonLock`（對應行程其實已經不在了），重啟後第一次重跑 Redbubble 上傳因此卡在 Cloudflare 表單 150 秒沒過，刪掉 `.rb_chrome_profile/SingletonLock`/`SingletonCookie`/`SingletonSocket` 就解了。之後如果又遇到「表單一直載入不出來」但確定帳號沒問題，先檢查是不是這個殘留鎖檔。

## 2026-08-05 — Pinterest caption 不能含 BMP 外字元（多數 emoji）
PRAF 上架時 Redbubble 兩版都成功，Pinterest 那步卻直接丟 `WebDriverException: unknown error: ChromeDriver only supports characters in the BMP`。根因：文案裡帶了 💸（U+1F4F8，在 Basic Multilingual Plane 之外），ChromeDriver 的 `send_keys` 不支援這種字元，直接拋例外（不是像其他雷那樣默默失敗）。查了一下全部 5 個新設計的文案，🤖🥤📵💸 都中招。
修法：`pinterest_upload.py` 的 `build_pin_copy()` 存描述前先過濾掉 `ord(ch) > 0xFFFF` 的字元，修在共用函式上，之後寫新文案不用刻意避開 emoji。原本已上架失敗的 PRAF 用 `pinterest_upload.py one "PRAF"` 單獨補跑 Pinterest 那步就好（Redbubble 兩版已經成功，不用重跑，也沒有重複刊登風險）。

## 2026-08-05 — 新增「每天愛心其他設計師作品」自動化
使用者提出想法：想增加跟其他設計師的互動，問能不能每天開 explore 頁隨機愛心幾個作品。確認方案：純隨機不篩類別、每天 3-5 個（避免看起來像洗版）。
技術細節：Redbubble UI 上看起來是愛心圖示，但實際 DOM 是 `button[data-testid="add-to-list-button"]`，aria-label 在 "Add to list"/"Remove from list" 間切換，拿這個當成功判斷兼防止重複點擊時誤取消。商品連結來源是 explore 首頁的推薦輪播（`a[class*="MediaCard-styles__link"]`），會混進使用者自己的設計（explore 個人化推薦），過濾條件是 URL 含 `-by-tses89214/`。
新增 `rb_explore_like.py`，裝進本機 crontab `0 9 * * *`（刻意早於 Pinterest daily 的 11:20，避免兩支腳本搶同一份 `.rb_chrome_profile` 導致其中一支在啟動瀏覽器就掛掉——這個坑今天稍早在 Focus 重跑時已經真的踩過一次）。
