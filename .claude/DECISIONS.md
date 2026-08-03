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
