# Prompt for Claude Code — Shopping Price Alert Bot

**Goal:**
Write a Python script that checks the price of one product page on books.toscrape.com and sends a Discord alert whenever the price has dropped since the last check.

**Context:**
- Target page: http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html (a public sandbox site built for scraping practice — its robots.txt and homepage explicitly permit scraping).
- The price is inside `<p class="price_color">` on the page.
- The script needs to remember the last price it saw between runs (store it in a small JSON file, e.g. `state/last_price.json`), since each run is a fresh process with no memory.
- This will eventually run on a 30-minute schedule via GitHub Actions, so the script must run non-interactively and exit cleanly whether or not a drop is found.
- Only scrape sites that explicitly allow it, and if the page's HTML structure changes and the price element can't be found, the script should fail loudly with a clear error rather than silently posting garbage.

**Action:**
1. Fetch the page with `requests`, parse it with `BeautifulSoup`.
2. Extract and parse the price (strip currency symbols, convert to float).
3. Compare it to the price stored in `state/last_price.json`.
   - If no state file exists yet, save the current price as the baseline and exit without alerting.
   - If the new price is lower than the stored price, trigger an alert.
4. Send the alert as a POST request to a Discord webhook.
5. Read the webhook URL only from an environment variable (`DISCORD_WEBHOOK_URL`) — never hardcode it in the script, never print it, and never commit it. Include a `.gitignore` that excludes any local `.env` file.
6. Update `state/last_price.json` with the new price after every run, drop or not.
7. Add a `--dry-run` flag that prints what the alert message would say instead of sending it, so I can test the logic without spamming Discord.

**Output:**
- A single script, `price_alert.py`.
- A `requirements.txt` listing dependencies.
- A `.env.example` showing the expected `DISCORD_WEBHOOK_URL` variable name (no real value).
- The Discord message should include: the product name, the old price, the new price, and a link back to the product page.
