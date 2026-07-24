"""
Sends a formatted price-drop alert to a Discord channel via webhook.
"""

import logging

import requests

logger = logging.getLogger(__name__)


class NotifyError(Exception):
    """Raised when the Discord webhook request fails."""


def send_price_drop_alert(
    webhook_url: str,
    product_name: str,
    previous_price: float,
    new_price: float,
    product_url: str,
    timeout: int = 10,
) -> None:
    """Post a price-drop embed to the configured Discord webhook."""
    savings = round(previous_price - new_price, 2)
    percent_off = round((savings / previous_price) * 100, 1) if previous_price else 0

    embed = {
        "title": f"Price Drop: {product_name}",
        "url": product_url,
        "color": 3066993,  # green
        "fields": [
            {"name": "Previous Price", "value": f"${previous_price:,.2f}", "inline": True},
            {"name": "New Price", "value": f"${new_price:,.2f}", "inline": True},
            {"name": "You Save", "value": f"${savings:,.2f} ({percent_off}%)", "inline": True},
            {"name": "Product Link", "value": product_url, "inline": False},
        ],
    }

    payload = {"embeds": [embed]}

    try:
        response = requests.post(webhook_url, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise NotifyError(f"Failed to send Discord alert: {exc}") from exc

    logger.info("Discord alert sent for '%s' ($%.2f -> $%.2f)", product_name, previous_price, new_price)
