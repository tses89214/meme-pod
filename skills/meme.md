# /meme

Generate a meme T-shirt design preview from text, send a 2×3 font preview grid to Telegram, then — once the user picks a font — write metadata and run the full Redbubble + Pinterest publish pipeline automatically.

## Syntax

```
/meme <text>
/meme *big text* /n small text
/meme small /n *BIG* /n small
/meme small /n *BIG*
```

- `*text*` → large bold text
- `/n` → manual line break（支援三段式結構，順序完整保留）
- plain text → small text
- 使用者可能傳 `\n`，一律轉成 `/n` 處理

## What to do

1. Run the generator:
   ```bash
   cd ~/meme-pod && python quick_meme.py "<text>"
   ```
   Capture the output path (last line printed = path to `_preview_grid_latest.png`).

2. Send the preview grid to Telegram with a caption asking user to pick a font:
   ```
   選哪個字型？(1-16)
   ```
   Font list:
   1. ANTON
   2. BEBAS NEUE
   3. ABRIL FATFACE
   4. OSWALD
   5. UNIFONT JP
   6. FREDOKA ONE
   7. DANCING SCRIPT
   8. PACIFICO
   9. CAVEAT
   10. JF OPEN HUNINN（jf 粉圓）
   11. GENYOMIN TW（源様明朝 TW）
   12. GENYOGOT TW（源様圓體 TW）
   13. NOTO SERIF TC（思源宋體 TC）
   14. NOTO SANS TC（思源黑體 TC）
   15. CUBIC 11（像素風 TC）
   16. TRAIN ONE（手書き風）

3. When user replies with a number (font choice is always the user's call, never pick for them):
   - Save to `.upload_queue.json` with font name and font_idx (still needed — `drive_upload.py batch` in step 5 depends on this queue, it's not dead).
   - Write the metadata entry into `upload_metadata.json` yourself — title/description/tags/main_tag + translations in EN/DE/FR/ES. This is a judgment call (copywriting), not scriptable — see `## Metadata entry format` below.
   - Ask which Redbubble collection to file it under (also always the user's call — never pick for them, and never invent a new collection name). Check current options first (they can change over time, don't rely on a stale hardcoded list):
     ```bash
     cd ~/meme-pod && python rb_upload.py collections
     ```
     Present the list, let them pick one or say "skip" (skipping leaves whatever the duplicated template already had checked — see DECISIONS.md 2026-08-04). If they name a collection that isn't in the list, tell them it doesn't exist — this flow only selects existing collections, it doesn't create new ones.
4. Run the full shop-publish pipeline in the background (this takes a while — two Redbubble submits ~20min each plus a Pinterest post, see `skills/meme-pinterest.md` and DECISIONS.md 2026-08-04 for why):
   ```bash
   cd ~/meme-pod && python publish_design.py "<text>" <font name, e.g. dancing> ["<collection name>"]
   ```
   Omit the third arg if the user skipped collection choice. Does: Redbubble upload (black+white variants, duplicated from the correct template — see `rb_upload.py`'s `BLACK_TEMPLATE_DUP_URL`/`WHITE_TEMPLATE_DUP_URL`), captures the product URL, then auto-posts a Pinterest pin with a real product mockup image. No further confirmation needed mid-flow.
5. Also run the Google Drive backup (still part of the default flow — user confirmed 2026-08-04 this isn't optional, just not blocking):
   ```bash
   cd ~/meme-pod && python drive_upload.py batch
   ```
   This regenerates the design fresh from `.upload_queue.json` (its own subprocess call to `quick_meme.py`), uploads both variants + a meta.json to Drive, and deletes the local files + clears the queue when done. Order relative to step 4 doesn't matter functionally (it regenerates its own copies), but do it after so the shop/Pinterest steps aren't waiting on it.
6. Confirm to user once both are done: report both Redbubble product URLs, Pinterest publish status, and the Drive folder link (the publish script prints a `=== 完成 ===` summary; `drive_upload.py batch` prints its own links per variant).

## Queue entry format

```json
{
  "text": "*staff adult* /n lv.99",
  "font": "anton",
  "font_idx": 1
}
```

Font index mapping: 1=anton, 2=bebas, 3=abril, 4=oswald, 5=unifont, 6=fredoka, 7=dancing, 8=pacifico, 9=caveat, 10=huninn, 11=genyomin, 12=genyogot, 13=notoserif, 14=notosans, 15=cubic11, 16=trainone

## Metadata entry format

Each entry in `upload_metadata.json` must include `translations` with EN/DE/FR/ES:
```json
{
  "text": "...",
  "font": "ANTON",
  "title": "...",
  "description": "...",
  "tags": [...],
  "translations": {
    "en": { "title": "...", "main_tag": "...", "tags": [...], "description": "..." },
    "de": { ... },
    "fr": { ... },
    "es": { ... }
  }
}
```

## Notes

- Output files go to `~/meme-pod/output/`
- Session is saved to `~/meme-pod/.last_meme_session.json`
- The preview grid is `~/meme-pod/output/_preview_grid_latest.png`
- 16 fonts always shown, regardless of text language
- `publish_design.py` reads image paths straight from `.last_meme_session.json` (not the `output/<name>/` folder convention `organize_designs.py` builds — that's for the older Drive-backup path only)
