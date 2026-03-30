# /meme

Generate a meme T-shirt design preview from text and send a 2×3 font preview grid to Telegram.

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

3. When user replies with a number:
   - Save to `.upload_queue.json` with font name and font_idx
   - Add metadata entry to `upload_metadata.json` (title, description, tags, translations in EN/DE/FR/ES)
   - Run batch upload to Google Drive and delete local files:
     ```bash
     cd ~/meme-pod && python drive_upload.py batch
     ```
   - Confirm to user: e.g. "ANTON 選好！上傳完成，共 N 組。"（local files are auto-deleted after upload）

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
- After Drive upload, local output PNGs are auto-deleted (drive_upload.py handles this)
