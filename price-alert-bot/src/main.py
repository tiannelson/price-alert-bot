"""
Entry point for the Shopping Price Alert Bot.

Flow:
  1. Load configuration from .env
  2. Scrape the current product price
  3. Compare against the last known price (stored locally as JSON)
  4. If the price dropped, send a Discord webhook alert
  5. Save the current price for the next run

Run manually:  python -m src.main
Run on a schedule: see .github/workflows/price_check.yml
"""

import logging
import sys

from src.config import ConfigError, load_config
from src.notifier import NotifyError, send_price_drop_alert
from src.price_store import load_last_price, save_price
from src.scraper import ScrapeError, fetch_product_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("price_alert_bot")


def run() -> int:
    try:
        config = load_config()
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        return 1

    try:
        current = fetch_product_data(
            url=config.product_url,
            price_selector=config.price_selector,
            name_selector=config.name_selector,
            fallback_name=config.product_name,
            timeout=config.request_timeout,
            user_agent=config.user_agent,
        )
    except ScrapeError as exc:
        logger.error("Scrape failed: %s", exc)
        return 1

    previous = load_last_price(config.data_file)

    if previous is not None and current["price"] < previous["price"]:
        logger.info(
            "Price dropped for '%s': $%.2f -> $%.2f",
            current["name"], previous["price"], current["price"],
        )
        try:
            send_price_drop_alert(
                webhook_url=config.discord_webhook_url,
                product_name=current["name"],
                previous_price=previous["price"],
                new_price=current["price"],
                product_url=current["url"],
            )
        except NotifyError as exc:
            # Don't block saving the new price just because the alert failed.
            logger.error("%s", exc)
    elif previous is not None and current["price"] > previous["price"]:
        logger.info(
            "Price increased for '%s': $%.2f -> $%.2f (no alert sent)",
            current["name"], previous["price"], current["price"],
        )
    elif previous is not None:
        logger.info("No price change for '%s' ($%.2f).", current["name"], current["price"])
    else:
        logger.info(
            "First run for '%s' — baseline price $%.2f saved, no alert sent.",
            current["name"], current["price"],
        )

    save_price(config.data_file, current["price"], current["name"])
    return 0


if __name__ == "__main__":
    sys.exit(run())
