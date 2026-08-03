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
