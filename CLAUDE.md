# CLAUDE.md — Meme Pod AI Context

This file provides context for AI assistants working on this project.

## Project overview

Meme T-shirt print-on-demand pipeline at `~/meme-pod/`. Generates designs → uploads to Google Drive → user manually uploads to Redbubble.

**Why Drive instead of direct Redbubble upload:** Redbubble uses reCAPTCHA v3, Playwright automation fails silently.

## Telegram command workflow

### /meme \<text\>
1. `python3 ~/meme-pod/quick_meme.py "<text>"` (timeout 180s)
2. Send `output/_preview_grid_latest.png` to Telegram with font list (1–16)
3. User replies with font number
4. Add to `.upload_queue.json`: `{"text": "...", "font": "<name>", "font_idx": <N>}`
5. Add metadata entry to `upload_metadata.json` (title, description, 15 tags, translations: en/de/fr/es)
6. Run `python3 ~/meme-pod/drive_upload.py batch` immediately — do NOT ask user first
7. `batch` auto-clears the queue after upload
8. Delete remaining output: `rm -rf ~/meme-pod/output/*`

### /meme-joke
Run `python3 ~/meme-pod/joke_fetch.py` and send results.

## Font index

| # | Font name | font key |
|---|-----------|----------|
| 1 | Anton | anton |
| 2 | Bebas Neue | bebas |
| 3 | Abril Fatface | abril |
| 4 | Oswald | oswald |
| 5 | Unifont JP | unifont |
| 6 | Fredoka One | fredoka |
| 7 | Dancing Script | dancing |
| 8 | Pacifico | pacifico |
| 9 | Caveat | caveat |
| 10 | JF Open Huninn | huninn |
| 11 | GenYoMin TW | genyomin |
| 12 | GenYoGot TW | genyogot |
| 13 | Noto Serif TC | notoserif |
| 14 | Noto Sans TC | notosans |
| 15 | Cubic 11 | cubic11 |
| 16 | Train One | trainone |

## Key files

| File | Purpose |
|------|---------|
| `quick_meme.py` | Generate 16-font preview grid |
| `design_generator.py` | Render 5000×5000px transparent PNGs |
| `drive_upload.py` | Upload to Google Drive; `batch` = full queue; `upload-meta` = meta only |
| `.upload_queue.json` | Queue of pending designs (auto-cleared after batch) |
| `.last_meme_session.json` | Last generation session (font paths) |
| `upload_metadata.json` | 30 designs × 4 languages metadata |
| `.drive_token.pickle` | Google Drive OAuth token |

## Text syntax

- `*text*` → large bold text
- `/n` → line break (user may send `\n`, treat as `/n`)
- `A /n *B* /n C` → three-line layout

## Metadata format

Each entry in `upload_metadata.json`:
```json
{
  "text": "*OOO* /n out of time /n out of energy /n out of money",
  "font": "FREDOKA",
  "title": "...",
  "description": "...",
  "tags": ["tag1", "...", up to 15],
  "translations": {
    "en": {"title": "...", "main_tag": "...", "tags": [...], "description": "..."},
    "de": {...},
    "fr": {...},
    "es": {...}
  }
}
```

## Google Drive auth

```bash
python drive_upload.py auth          # Get auth URL
python drive_upload.py auth <code>   # Exchange code for token
```

- Client secrets: `~/ambient-pipeline/client_secrets.json`
- Token: `~/meme-pod/.drive_token.pickle`
- Drive folder: `meme-pod-designs/<design name>/`

## Redbubble upload (manual)

- Use transparent PNG
- Do NOT disable any products
- Sticker: enable die-cut; Poster: all sizes
- Best for text: Sticker, Poster, Mug, Tote Bag, T-shirt

## Brand

- Name: Low Battery Meme Design
- Privacy policy: https://tses89214.github.io/low-battery-meme-design/privacy.html
- Pinterest app: under review (approved 2026-03-28, pending)
