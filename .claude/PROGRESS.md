# PROGRESS

## 目前狀態（2026-08-04）
Redbubble 自動上架管線可用且已實戰驗證：3 個設計（My faith is beer、Universe Grant Me Power、Actions Speak Louder Than Words）、黑白共 6 筆，全部真的 submit 上架成功。換圖 selector `#select-image-base`，Selenium command timeout 拉到 600 秒解掉間歇性 timeout。細節見 DECISIONS.md。

Pinterest 決定跳過手動驗證階段，直接做自動發文（使用者明確指示推翻 8/3 的手動優先決定）。已建好「Funny Meme Shirts」board，並成功自動發布第一個真的 pin（My faith is beer，本地圖檔+標題+描述+目的地連結+board 全自動填寫送出，Pinterest 確認「你已建立一個 Pin！」）。技術細節、選擇器、踩過的雷（「儲存自網站」抓不到商品圖）都記在 `skills/meme-pinterest.md`。

## 已完成
- 掃過專案結構，確認 `.upload_queue.json` 為空（無待傳項目）。
- 建立進度／決策／記憶文件，並修正 .gitignore 讓三份文件可被 commit。
- CLAUDE.md 補上「TG 來的問題一律回 TG」規則。
- 用 grilling 拷問完 Pinterest 導流計畫，定案並寫成 `skills/meme-pinterest.md`，10 支種子清單的文案已交付使用者。
- 修好 Redbubble 自動化環境：apt 裝 `chromium`+`chromium-driver`（arm64 版本對齊，原本系統只有 chromium 沒有 chrome）、把系統 chromedriver 複製到使用者可寫路徑讓 undetected_chromedriver 能 patch、`rb_upload.py` 的 `get_driver()` 指定正確的 browser/driver 路徑。
- 實測確認：Redbubble 登入 session 靠 `.rb_chrome_profile` 持久化，重開全新瀏覽器實例不用重新登入；`/portfolio/images/new`、`/portfolio/images/<id>/duplicate` 這類頁面的 Cloudflare 驗證會自動過關（30-90 秒等待，不用人手動點），已把 `rb_upload.py` 的等待 timeout 從 20 秒拉到 150 秒、拿掉會卡死的 `input()`。
- 探索「Duplicate design」流程（決策見 DECISIONS.md）：找到黑/白範本 work id、duplicate 網址規則、title/description/checkbox/submit 的欄位 id（跟原 New Work 表單共用）。Tags 欄位是 React pill 元件還沒摸清楚怎麼操作。
- Pinterest 也用同一個 `.rb_chrome_profile` 手動登入過一次並實測持久化成功（全新瀏覽器實例直接進企業專區，不用重登）。
- `.gitignore` 補上 `.rb_chrome_profile/`（內含登入 session/cookie，不可進版控）。

## 下一步（下次會話上班打卡先看這）
- Redbubble 上傳管線已經可用（`rb_upload.py` 的 `get_driver()` + `fill_design(target_url=..., submit=True)`），新設計要上架照黑範本配白字圖、白範本配黑字圖的模式跑。只驗證過 3 個設計，大量批次（10+ 件）的穩定性沒測過。
- Pinterest 自動發文機制可用但還是單支手動觸發，還沒做成批次迴圈。缺口：
  1. 商品網址目前靠 promote 確認頁的「View」連結現抓，沒有存到 `upload_metadata.json`，之後每次都要重找
  2. 圖片用的是本地透明設計圖，不是商品 mockup 照（Pinterest 建議 2:3 長寬比，我們是正方形）
  3. 沒有「哪些設計已經 pin 過」的追蹤，重跑會不會重複發要注意
  上述都列在 `skills/meme-pinterest.md` 的 Open TODOs，下次可以直接接著做批次版本。
- `upload_metadata.json` 有未 commit 的修改（使用者原本的 + 這次新增的 2 筆 uploaded:true，Actions 那筆本來就已經是 true），下次動這個檔案前先跟使用者確認要不要一起 commit。
