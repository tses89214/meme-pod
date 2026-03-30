# /meme-trend

Fetch today's trending memes from Reddit + Google Trends and send a digest to Telegram.

## Syntax

```
/meme-trend
```

## What to do

1. Run:
   ```bash
   cd ~/meme-pod && python trend_monitor.py
   ```

2. Parse the output — ranked list of Reddit posts scored for T-shirt suitability.

3. Send top results to Telegram. Format as standalone phrases — skip anything that requires an image to make sense:
   ```
   🔥 今日梗圖熱搜 YYYY-MM-DD

   1. Me when the meeting could've been an email
   2. What's cool if you're 20 but weird if you're 30?
   3. I have no butt and I must poop

   輸入 /meme <文字> 直接生成設計！
   ```

## Scoring notes

The scorer (`score_for_tshirt`) now:
- Rewards: first-person phrases, relatable openers ("me when", "pov:", "unpopular opinion", etc.)
- Penalizes: image-dependent phrases ("every single time", "look at this"), political/news content
- Prefers: 4–12 word titles, phrases starting with I/me/my/we/you

## Notes

- Trend data saved to `~/meme-pod/trends/YYYY-MM-DD.json`
- Reddit sources: r/memes, r/funny, r/antiwork, r/gaming, r/AskReddit
- Google Trends: US RSS feed (pytrends as fallback; Google RSS sometimes returns 404)
