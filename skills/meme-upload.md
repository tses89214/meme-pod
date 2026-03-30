# /meme-upload

Upload queued designs to Google Drive (one subfolder per design) and organize local output folders.

## Syntax

```
/meme-upload          # upload entire queue to Drive
/meme-upload organize # organize output folders only (no Drive upload)
```

## What to do

### Full queue upload

1. Run:
   ```bash
   cd ~/meme-pod && python drive_upload.py batch
   ```
2. Script regenerates each design, uploads 2 transparent versions (black text + white text) into its own subfolder under `meme-pod-designs/` on Drive.
3. Confirm to Telegram: "✅ 批量上傳完成，共 N 組"

### Organize local folders (generate output/)

```bash
cd ~/meme-pod && python organize_designs.py
```

This creates `output/<DesignName>/` folders, each containing:
- `for_light_shirt.png` — black text transparent PNG (for light-coloured shirts)
- `for_dark_shirt.png` — white text transparent PNG (for dark-coloured shirts)
- `meta.txt` — title, tags, description in EN/DE/FR/ES

## Drive folder structure

```
meme-pod-designs/
  <design name>/
    ├── black.png   (for light shirts)
    └── white.png   (for dark shirts)
```

## Auth

- Token stored at `~/meme-pod/.drive_token.pickle`
- If missing or expired:
  1. Run `python drive_upload.py auth` → get URL
  2. User opens URL in browser, Google shows auth code on screen (OOB flow, no redirect needed)
  3. User pastes code → run `python drive_upload.py auth <code>`
- Note: uses PKCE/OOB — works from Docker container (no localhost redirect required)

## Notes

- Queue: `~/meme-pod/.upload_queue.json`
- Metadata (with translations): `~/meme-pod/upload_metadata.json`
- Redbubble upload: https://www.redbubble.com/portfolio/images/new
  - Enable all products
  - Sticker = die-cut
  - Poster = all sizes
