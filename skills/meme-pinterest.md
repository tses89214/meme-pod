# /meme-pinterest

Auto-post pins to Pinterest for already-uploaded Redbubble designs, using the same Selenium/undetected-chromedriver stack as `rb_upload.py` (shared login profile — see `.claude/MEMORY.md`).

Status: v2, being built 2026-08-04. Automation replaces the original manual-pilot plan per user's explicit call (DECISIONS.md 2026-08-04 "此決定被使用者明確推翻"). Pin-builder UI has been explored (selectors below); board creation + full post flow + batch loop not yet written.

## Syntax

```
/meme-pinterest              # prep next batch (ask user how many, default 10)
/meme-pinterest <N>           # prep N pins
```

## Context (read once, don't re-derive every time)

- Pinterest account: Business, category "網路商家或市集", `redbubble.com/people/tses89214/shop` claimed (declared, was in review as of 2026-08-03). Login persisted 2026-08-03 in the same `.rb_chrome_profile` used for Redbubble — confirmed still logged in on fresh browser launches.
- No Pinterest API — same Selenium + undetected-chromedriver stack as `rb_upload.py`. Evaluated `SoCloseSociety/PinterestBulkPostBot` (22★, MIT, Python+Selenium) on 2026-08-03 — shelved, not needed.
- Single board for now: **"Funny Meme Shirts"**. Don't split into sub-boards until a theme shows real signal in Pinterest Analytics. **As of 2026-08-04 this board does not exist yet** — account has zero boards, must be created via the pin-builder's "建立圖版" flow before the first real pin.
- `upload_metadata.json` does NOT store the live Redbubble product URL per design — only text/title/tags/description/translations. Getting the URL for a given title currently means finding it on the shop page by hand (or asking the user to paste it). This is a known gap, not a bug to silently work around.

## Pin-builder UI (explored 2026-08-04, Selenium selectors confirmed)

URL: `https://www.pinterest.com/pin-builder/` — went straight to the create-pin form, no onboarding popup this session (may reappear, handle defensively).

Per-pin dynamic UUID suffix on several element ids (e.g. `pin-draft-title-<uuid>`) — don't hardcode the full id, match by placeholder/aria-label/id-prefix instead:

- Image upload: `input[type="file"][aria-label="上傳檔案"]` (likely works with `.send_keys(path)` same as Redbubble's pattern — not yet tested). Alternate: "儲存自網站" button lets Pinterest pull the image straight from a URL (Save-button style, matches the reference article's workflow) — not yet tested which is more reliable for us.
- Title: `textarea[placeholder="新增標題"]`
- Description: NOT a plain input — it's a Draft.js contenteditable div, `div[aria-label="讓所有人知道你的 Pin 內容"]`. Click + send_keys should work but untested; React/Draft.js editors sometimes need the same native-setter+event-dispatch trick used for Redbubble's fields if plain send_keys misbehaves.
- Destination link: `textarea[placeholder="新增目的地連結"]` — separate field from description, so the "no bare https://" gotcha (see Learned tactics below) only applies to the description text, not this field.
- Board picker: click `[data-test-id="board-dropdown-select-button"]` to open a flyout with a search box (`[data-test-id="search-boards-field-container"]`) and, if searching an existing board name, presumably `[role="option"]` results (untested — account has no boards yet to verify against). To create a new board: `[data-test-id="create-board-button"]` (opens a further flow, not yet explored — likely name/description/category/privacy fields, not yet mapped).
- Publish button: `[data-test-id="board-dropdown-save-button"]` (top-right red button, labelled 發布).
- Publish now vs scheduled: radio inputs `id^="pin-draft-schedule-publish-immediately-"` / `-later-`; "immediately" is selected by default.
- AI-disclosure toggle/checkboxes: leave off, our art isn't AI-generated-person content.

Not yet done: create-board flow, actually filling+submitting one real pin end to end, verifying the image upload approach, wiring up a batch loop over designs.

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

## Learned tactics (from external article, 2026-08-04)

Source: https://straightforward.se/blog/creating-a-shopfront-for-your-redbubble-products-on-pinterest — one seller's manual Redbubble→Pinterest workflow. No automation in the source, but the tactics carry over:

- **Board naming**: keyword + brand combo (their example: "Mugs and Cups by Tiokvadrat"), board description up to 500 chars for Pinterest's own search/SEO, pick the closest-matching official category (they used "Home décor" for mugs — for us, closest is probably "Fashion" or similar for tees, need to check what categories exist).
- **Pin copy formula**: `[what] – [who] – [where] – [when] – [why] – [how]`. Example: "Blue 'Girly Swot' classic mug celebrating clever girls! Perfect gift mug for smart women studying at school, college, or university." Then a branding tagline line: "Design by X. shopname.redbubble.com".
- **⚠️ Critical gotcha**: Pinterest rejects the whole pin description if it contains a bare `https://` URL. The article's workaround is to write the shop domain without the scheme (`tiokvadrat.redbubble.com`, no `https://`). This matters for our automation — don't put `https://` inside the description text field; the separate destination-link field is a different input and presumably fine with a full URL.
- **Post-pin validation**: after posting, check (1) image renders right, (2) text/title display correctly, (3) the pin's link actually click-throughs to the right product page. Worth doing as an automated post-publish check too, not just for humans.
- **Volume**: no fixed cadence — started with about half a dozen pins, then kept going gradually. No stated timeline for when results showed up.

## Open TODOs (optimize later, per user — don't do these unasked)

- Capture live product URL in `upload_metadata.json` at upload time (edit `uploader.py`) so future batches don't need manual URL hunting.
- Once signal is validated: revisit whether a bulk tool (own Playwright script reusing `rb_interactive.py`'s manual-login pattern, vs. a third-party Selenium bot) is worth it.
- Consider splitting "Funny Meme Shirts" into theme boards once Pinterest Analytics shows which theme performs.
