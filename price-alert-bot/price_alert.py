"""
Shopping Price Alert Bot

Checks the price of a single product page and posts a Discord alert
whenever the price has dropped since the last check.

Target site: books.toscrape.com — a public sandbox built for scraping
practice (its homepage reads "We love being scraped!"). Only point this
script at sites that explicitly permit scraping.

Secrets: the Discord webhook URL is read from the DISCORD_WEBHOOK_URL
environment variable. It is never hardcoded and never printed.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

PRODUCT_URL = os.environ.get(
    "PRODUCT_URL",
    "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
)
STATE_FILE = Path(__file__).parent / "state" / "last_price.json"
REQUEST_TIMEOUT = 15


def fetch_price(url: str) -> tuple[str, float]:
    """Return (product_name, price) scraped from the product page."""
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h1")
    price_tag = soup.find("p", class_="price_color")

    if title_tag is None or price_tag is None:
        raise RuntimeError(
            "Could not find the product title or price on the page. "
            "The site's HTML layout may have changed — check the selectors "
            "before trusting any alert from this script."
        )

    product_name = title_tag.get_text(strip=True)

    price_text = price_tag.get_text(strip=True)
    match = re.search(r"[\d]+\.?\d*", price_text)
    if not match:
        raise RuntimeError(f"Could not parse a price out of: {price_text!r}")

    return product_name, float(match.group())


def load_last_price() -> dict | None:
    if not STATE_FILE.exists():
        return None
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(product_name: str, price: float) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(
            {
                "product_name": product_name,
                "price": price,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            },
            f,
            indent=2,
        )


def build_message(product_name: str, old_price: float, new_price: float, url: str) -> str:
    return (
        f"💰 **Price drop detected!**\n"
        f"**{product_name}**\n"
        f"Was £{old_price:.2f} → now **£{new_price:.2f}**\n"
        f"{url}"
    )


def send_discord_alert(message: str) -> None:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError(
            "DISCORD_WEBHOOK_URL is not set. Set it as an environment variable "
            "(locally via a .env file, or as a GitHub Actions repository secret). "
            "Never hardcode it in this script."
        )
    response = requests.post(webhook_url, json={"content": message}, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a product price and alert on drops.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what the alert would say instead of sending it to Discord.",
    )
    parser.add_argument(
        "--force-baseline",
        type=float,
        default=None,
        help="Testing helper: pretend the last recorded price was this value, "
        "so you can trigger a drop alert on demand.",
    )
    args = parser.parse_args()

    try:
        product_name, current_price = fetch_price(PRODUCT_URL)
    except (requests.RequestException, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    last_state = load_last_price()
    if args.force_baseline is not None:
        last_state = {"product_name": product_name, "price": args.force_baseline}

    if last_state is None:
        print(f"No prior price on record. Setting baseline: £{current_price:.2f}")
        save_state(product_name, current_price)
        return 0

    last_price = last_state["price"]
    print(f"Last recorded price: £{last_price:.2f} | Current price: £{current_price:.2f}")

    if current_price < last_price:
        message = build_message(product_name, last_price, current_price, PRODUCT_URL)
        if args.dry_run:
            print("--- DRY RUN: would send this message to Discord ---")
            print(message)
        else:
            send_discord_alert(message)
            print("Price drop alert sent to Discord.")
    else:
        print("No price drop. No alert sent.")

    if not args.force_baseline:
        save_state(product_name, current_price)

    return 0


if __name__ == "__main__":
    sys.exit(main())
