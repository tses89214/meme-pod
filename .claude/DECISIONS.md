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
- 換圖：`#select-image-large_clothing`（畫面上「Replace all images」按鈕對應的 input，可能需要確認是否要連動填其他 product-type 的 image input）
- 版權確認框：`#rightsDeclaration`（checkbox，name="rights_declaration"）
- 送出鈕：`#submit-work`（跟原本 New Work 表單相同）
- 卡住的地方：Tags 欄位（`#work_tag_editor_{lang}`）在這頁是隱藏 input + React pill 元件，不是原本 New Work 表單那種可以直接打字按 Enter 的欄位，還沒摸清楚怎麼用 Selenium 可靠操作。

現況：使用者說會自己帶一份寫好的爬蟲腳本回來，到時候直接 import 進 `rb_upload.py`，取代這裡未完成的摸索。此決策記錄先保留已驗證的部分，避免下次從頭來過。
