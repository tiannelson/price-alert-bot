"""
Loads and validates configuration from environment variables (.env file).
Never hardcode secrets here — this module only reads them.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    product_url: str
    product_name: str
    price_selector: str
    name_selector: str
    discord_webhook_url: str
    data_file: str
    request_timeout: int
    user_agent: str


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value or not value.strip():
        raise ConfigError(f"Missing required environment variable: {key}")
    return value.strip()


def load_config() -> Config:
    """Read and validate all settings needed to run the bot."""
    return Config(
        product_url=_require("PRODUCT_URL"),
        product_name=os.getenv("PRODUCT_NAME", "").strip() or "Product",
        price_selector=_require("PRICE_SELECTOR"),
        name_selector=os.getenv("NAME_SELECTOR", "").strip(),
        discord_webhook_url=_require("DISCORD_WEBHOOK_URL"),
        data_file=os.getenv("DATA_FILE", "data/last_price.json").strip(),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "15")),
        user_agent=os.getenv(
            "USER_AGENT",
            "Mozilla/5.0 (compatible; PriceAlertBot/1.0; +https://github.com/)",
        ).strip(),
    )
