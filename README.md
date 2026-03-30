# Low Battery Meme Design — Meme Pod

Automated pipeline for generating and publishing text-based T-shirt designs to Redbubble via Google Drive.

## What it does

1. Takes a meme text input
2. Renders it in 16 fonts as print-ready 5000×5000px transparent PNGs
3. Uploads selected designs to Google Drive with multilingual metadata (EN/DE/FR/ES)
4. Designs are manually uploaded to Redbubble from Drive

## Usage

```bash
# Preview a design in all fonts
python quick_meme.py "*Your Text* /n subtitle"

# Upload selected designs from queue to Google Drive
python drive_upload.py batch

# Fetch T-shirt-worthy jokes from public APIs
python joke_fetch.py
```

## Text syntax

| Input | Result |
|-------|--------|
| `*text*` | Large bold text |
| `/n` | Line break |
| `small /n *BIG* /n small` | Three-line layout |

## Fonts (16 total)

Anton, Bebas Neue, Abril Fatface, Oswald, Unifont JP, Fredoka One, Dancing Script, Pacifico, Caveat, JF Open Huninn, GenYoMin TW, GenYoGot TW, Noto Serif TC, Noto Sans TC, Cubic 11, Train One

## Setup

1. Install dependencies: `pip install Pillow requests google-api-python-client google-auth-oauthlib`
2. Place Google OAuth client secrets at `~/ambient-pipeline/client_secrets.json`
3. Run `python drive_upload.py auth` to authenticate

## Brand

**Low Battery Meme Design** — [Redbubble Store](https://www.redbubble.com)
