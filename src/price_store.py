"""
Persists the last known price to a local JSON file so prices can be
compared across separate runs of the bot (e.g. one run per GitHub Action).
"""

import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def load_last_price(data_file: str) -> dict | None:
    """Return {"price": float, "name": str, "checked_at": str} or None if no history exists."""
    if not os.path.exists(data_file):
        logger.info("No price history found at %s (first run).", data_file)
        return None

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "price" not in data:
            raise ValueError("Missing 'price' key")
        return data
    except (json.JSONDecodeError, ValueError, OSError) as exc:
        logger.warning("Could not read existing price history (%s): %s", data_file, exc)
        return None


def save_price(data_file: str, price: float, name: str) -> None:
    """Write the current price to the local JSON store, creating parent dirs if needed."""
    directory = os.path.dirname(data_file)
    if directory:
        os.makedirs(directory, exist_ok=True)

    payload = {
        "price": price,
        "name": name,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info("Saved current price %.2f to %s", price, data_file)
