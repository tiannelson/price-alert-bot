# Shopping Price Alert Bot

Checks a product page on books.toscrape.com and posts to Discord when the price drops. Runs manually or on a 30-minute GitHub Actions schedule.

## Files

- `price_alert.py` — the bot
- `requirements.txt` — dependencies
- `.env.example` — template for your local webhook URL (copy to `.env`, never commit `.env`)
- `.gitignore` — excludes `.env` and other local junk
- `state/last_price.json` — created automatically; stores the last price seen
- `.github/workflows/price-check.yml` — the scheduled job
- `claude_code_prompt.md` — the GCAO prompt used to generate the script (your Step 2 submission)

## 1. Test it locally

1. `pip install -r requirements.txt`
2. `cp .env.example .env` and paste your real webhook URL into `.env`
3. Load it into your shell, then run:
   ```
   export $(cat .env | xargs)
   python3 price_alert.py --dry-run
   ```
   First run just sets a baseline price — no alert yet, that's expected.
4. Force a fake drop to see a real message land in Discord:
   ```
   python3 price_alert.py --force-baseline 999.99
   ```
   (Drop `--dry-run` this time so it actually posts.) You should see the alert in your Discord channel within seconds.

## 2. Push to GitHub

Since your repo already exists:
```
git init   # skip if already a git repo
git add .
git status   # double check .env is NOT listed — only .env.example should be
git commit -m "Add price alert bot"
git remote add origin <your-repo-url>   # skip if already set
git push -u origin main
```

## 3. Add the secret (if not already there)

Repo → **Settings → Secrets and variables → Actions → New repository secret**
- Name: `DISCORD_WEBHOOK_URL`
- Value: your real webhook URL

## 4. Confirm it's running

- Repo → **Actions** tab → you should see "Price Check" listed
- Click **Run workflow** to trigger it immediately instead of waiting 30 minutes
- Open the run and check the logs for `price_alert.py` output
- After a successful run, `state/last_price.json` should show a new commit from `github-actions[bot]` — that's how the bot remembers the price between runs in the cloud

## Notes

- Prices on books.toscrape.com never actually change (it's a static sandbox), so real-world drops won't occur on their own — the `--force-baseline` flag is how you demonstrate the drop-detection path.
- If you swap in a real retail product URL later, re-check that site's robots.txt/terms allow scraping, and confirm the price CSS selector in `fetch_price()` still matches — the script will raise a clear error if it can't find the price element, rather than posting a bad alert.
