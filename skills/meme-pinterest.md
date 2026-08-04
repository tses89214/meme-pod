# /meme-pinterest

Auto-post pins to Pinterest for already-uploaded Redbubble designs, using the same Selenium/undetected-chromedriver stack as `rb_upload.py` (shared login profile — see `.claude/MEMORY.md`).

Status: v2. First real pin published successfully 2026-08-04 (manual single-pin test, not yet wired into a batch loop). Automation replaces the original manual-pilot plan per user's explicit call (DECISIONS.md 2026-08-04 "此決定被使用者明確推翻").

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

- Image upload: `input[type="file"][aria-label="上傳檔案"]` + `.send_keys(local_path)`, same pattern as Redbubble. **Confirmed working 2026-08-04.** Don't use "儲存自網站" (save-from-website) for Redbubble product pages — tested, it scrapes random page icons (avatar, heart icon) instead of the product mockup, useless for us.
- Title: `textarea[placeholder="新增標題"]` + plain `.send_keys()`. Confirmed working.
- Description: Draft.js contenteditable div, `div[aria-label="讓所有人知道你的 Pin 內容"]`. Plain click + `.send_keys()` worked fine, no React-hack needed (unlike Redbubble's tag fields).
- Destination link: `textarea[placeholder="新增目的地連結"]`, plain `.send_keys()`. Confirmed working with a full `https://...?utm_...` URL — the "no bare https://" gotcha (see Learned tactics) only applies to the description text, this field is fine.
- Board picker: click `[data-test-id="board-dropdown-select-button"]`, then click `[data-test-id="board-row-<exact board name>"]` directly — no need to type into the search box first, the row selector works even without narrowing the list. To create a new board: click `[data-test-id="create-board-button"]`, fill `#boardEditName`, leave `#secret` checkbox unchecked (public), click `[data-test-id="board-form-submit-button"]`. **Confirmed working 2026-08-04** — created "Funny Meme Shirts" this way, no CAPTCHA despite a recaptcha field existing in the DOM.
- Publish button: `[data-test-id="board-dropdown-save-button"]` (top-right red button, labelled 發布). Confirmed working — success shows a "你已建立一個 Pin！" modal and a "已儲存到 <board>" toast.
- Publish now vs scheduled: radio inputs `id^="pin-draft-schedule-publish-immediately-"` / `-later-`; "immediately" is selected by default, left untouched.
- AI-disclosure toggle/checkboxes: left off, untouched.
- Minor: Pinterest shows a non-blocking warning if the image aspect ratio isn't at least 2:3 (portrait) — our square 5000×5000 designs trigger it but publish anyway. Worth cropping/padding to portrait for better performance later, not a blocker now.

## What to do (current — manual single-pin, confirmed working end to end)

1. Pick a design from `upload_metadata.json` where `"uploaded": true`.
2. Get its live Redbubble product URL: the cleanest known way right now is from the upload's own promote-page confirmation (`https://www.redbubble.com/studio/promote/<work_id>`) — find the `<a>` with text "View", its `href` is the public product URL (e.g. `https://www.redbubble.com/shop/ap/<id>`). Only works if you have that promote URL from the upload step; there's no stored mapping from title → URL yet (see Open TODOs).
3. Build the pin link: `<product_url>?utm_source=pinterest&utm_medium=social&utm_campaign=auto` (drop any `?ref=...` Redbubble appended).
4. Image: use a local transparent design PNG from `output/` for now (confirmed working). Real product mockup photos would look better per the reference article, but there's no reliable automated way to fetch them yet (og:image fetch untested, save-from-website doesn't work) — open TODO.
5. Title/description: adapt from `upload_metadata.json`'s `title`/`description` — keep description free of any bare `https://` text.
6. Board: `Funny Meme Shirts` (already created).
7. Fill all fields, then Publish.

Not yet built: batch loop over multiple designs, product-URL-lookup that doesn't depend on having a promote-page link handy, real mockup image sourcing, de-dup tracking (which designs have already been pinned) analogous to `upload_metadata.json`'s `uploaded` flag.

## Learned tactics (from external article, 2026-08-04)

Source: https://straightforward.se/blog/creating-a-shopfront-for-your-redbubble-products-on-pinterest — one seller's manual Redbubble→Pinterest workflow. No automation in the source, but the tactics carry over:

- **Board naming**: keyword + brand combo (their example: "Mugs and Cups by Tiokvadrat"), board description up to 500 chars for Pinterest's own search/SEO, pick the closest-matching official category (they used "Home décor" for mugs — for us, closest is probably "Fashion" or similar for tees, need to check what categories exist).
- **Pin copy formula**: `[what] – [who] – [where] – [when] – [why] – [how]`. Example: "Blue 'Girly Swot' classic mug celebrating clever girls! Perfect gift mug for smart women studying at school, college, or university." Then a branding tagline line: "Design by X. shopname.redbubble.com".
- **⚠️ Critical gotcha**: Pinterest rejects the whole pin description if it contains a bare `https://` URL. The article's workaround is to write the shop domain without the scheme (`tiokvadrat.redbubble.com`, no `https://`). This matters for our automation — don't put `https://` inside the description text field; the separate destination-link field is a different input and presumably fine with a full URL.
- **Post-pin validation**: after posting, check (1) image renders right, (2) text/title display correctly, (3) the pin's link actually click-throughs to the right product page. Worth doing as an automated post-publish check too, not just for humans.
- **Volume**: no fixed cadence — started with about half a dozen pins, then kept going gradually. No stated timeline for when results showed up.

## Open TODOs (optimize later, per user — don't do these unasked)

- Capture live product URL in `upload_metadata.json` at upload time (edit `rb_upload.py`'s `fill_design` to grab the "View" link href right after submit) so future pins don't need manual URL hunting via the promote page.
- Add a `pinned` (or similar) flag per design in `upload_metadata.json`, mirroring `uploaded`, so a batch script can skip designs already pinned.
- Figure out real mockup image sourcing (og:image fetch from the product page, now that we know save-from-website doesn't work) instead of using the bare transparent design PNG.
- Write the actual batch loop (mirrors `rb_batch_upload.py`'s pattern) once the above are in place.
- Consider splitting "Funny Meme Shirts" into theme boards once Pinterest Analytics shows which theme performs.
