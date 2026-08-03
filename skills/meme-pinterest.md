# /meme-pinterest

Prep a batch of Pinterest pins from already-uploaded Redbubble designs. Posting itself stays manual (human clicks "Create Pin" in the Pinterest app) — this skill only prepares the assets/copy/links so the user can paste-and-go.

Status: v1, manual-pilot phase. No bulk-posting automation yet — see "Why manual" below before adding any.

## Syntax

```
/meme-pinterest              # prep next batch (ask user how many, default 10)
/meme-pinterest <N>           # prep N pins
```

## Context (read once, don't re-derive every time)

- Pinterest account: Business, category "網路商家或市集", `redbubble.com/people/tses89214/shop` claimed (declared, was in review as of 2026-08-03).
- No Pinterest API use — everything here is manual posting, no Selenium/bulk-post bot. Evaluated `SoCloseSociety/PinterestBulkPostBot` (22★, MIT, Python+Selenium) on 2026-08-03 — shelved, see below.
- Single board for now: **"Funny Meme Shirts"**. Don't split into sub-boards until a theme shows real signal in Pinterest Analytics.
- `upload_metadata.json` does NOT store the live Redbubble product URL per design — only text/title/tags/description/translations. Getting the URL for a given title currently means finding it on the shop page by hand (or asking the user to paste it). This is a known gap, not a bug to silently work around.

## What to do

1. Pick N designs from `upload_metadata.json` where `"uploaded": true`, favoring broad/universal punchlines (work humor, gym, gaming-life-level jokes) over niche bilingual/Chinese-culture ones — those may deserve their own board later but dilute a small pilot batch.
2. For each pick, get the live product URL:
   - Ask the user to paste the shop page URL (fastest), or
   - Fetch `https://www.redbubble.com/people/tses89214/shop` and match by title if it renders without JS (may not work — SPA).
3. Build the pin link: `<product_url>?utm_source=pinterest&utm_medium=social&utm_campaign=pilot`
4. Get the mockup image: fetch the product page, extract `og:image` (Redbubble's auto-generated mockup photo). Do NOT use the bare transparent design PNG from `output/` — mockups convert better on a visual platform.
5. Draft Pinterest copy per pin (reuse `upload_metadata.json`'s `title`/`description`/`tags` as the seed, adapt to Pinterest's format/length):
   - Title: ≤100 chars, keyword-first
   - Description: ≤500 chars, natural sentence with 2-3 keywords worked in
6. Hand the user a checklist (image + title + description + link per pin) — they paste it into Pinterest manually.
7. Tell the user to spread posting over 3-5 days, not all at once, and to wait 3-4 weeks before judging signal (Pinterest is slow-burn discovery, not like IG/TikTok).

## Why manual (don't skip to automation)

Decided 2026-08-03: the strategy itself is unvalidated — no Pinterest presence existed before this. Building/wiring a bulk-post tool before knowing whether Pinterest drives any Redbubble traffic is wasted setup. Revisit automation only once weekly pin volume would need to exceed ~30/week AND the pilot has shown a measurable traffic/CTR signal via the UTM tags. Until then, every pin here is posted by hand.

## First pilot batch (2026-08-03, for reference — not meant to be reused verbatim next time)

1. Ask AI Before You Ask Me Anything
2. Human Pro Max Funny Upgrade Meme
3. Fine You're Right You're Always Right
4. Life Is a Bitch So Learn How to F It
5. I'm Not Lazy, I'm On Energy Saving Mode
6. I'm Allergic to Work
7. Professional Overthinker
8. Work Hard. Stay Humble. Quit Early.
9. OOO Out Of Time Energy Money
10. KPI Killing People Inside

## Open TODOs (optimize later, per user — don't do these unasked)

- Capture live product URL in `upload_metadata.json` at upload time (edit `uploader.py`) so future batches don't need manual URL hunting.
- Once signal is validated: revisit whether a bulk tool (own Playwright script reusing `rb_interactive.py`'s manual-login pattern, vs. a third-party Selenium bot) is worth it.
- Consider splitting "Funny Meme Shirts" into theme boards once Pinterest Analytics shows which theme performs.
