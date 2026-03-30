# /meme-joke

Fetch English jokes & puns from free APIs and send a ranked digest to Telegram.

## Syntax

```
/meme-joke        # fetch fresh jokes
```

## What to do

1. Run:
   ```bash
   cd ~/meme-pod && python joke_fetch.py
   ```

2. Send top results to Telegram. Format:
   ```
   🎭 英文笑話/雙關語 YYYY-MM-DD

   1. A steak pun is a rare medium well done.
   2. I'm reading a book about anti-gravity. It's impossible to put down!
   3. I invented a new word! Plagiarism!

   輸入 /meme <文字> 直接生成設計！
   ```

## Sources

- **icanhazdadjoke.com** — dad jokes (no auth)
- **v2.jokeapi.dev/joke/Pun** — puns only (no auth)

## Notes

- Jokes are scored for T-shirt suitability (short, standalone, no context needed)
- Re-run to get fresh results (APIs return random each time)
