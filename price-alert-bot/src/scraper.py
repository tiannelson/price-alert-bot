"""
Retrieves the current product price (and optionally name) from a retail
product page using requests + BeautifulSoup.

IMPORTANT: Only scrape sites whose Terms of Service and robots.txt permit it.
CSS selectors are site-specific and WILL break if the retailer changes their
HTML — update PRICE_SELECTOR / NAME_SELECTOR in your .env when that happens.
"""

import logging
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_PRICE_CLEAN_RE = re.compile(r"[^\d.,]")


class ScrapeError(Exception):
    """Raised when the page can't be fetched or the price can't be parsed."""


def _parse_price(raw_text: str) -> float:
    """Convert text like '$1,299.99' or '1299,99 €' into a float."""
    cleaned = _PRICE_CLEAN_RE.sub("", raw_text).strip()
    if not cleaned:
        raise ScrapeError(f"Could not find a numeric price in text: {raw_text!r}")

    # Handle both '1,299.99' (US) and '1.299,99' (EU) formats.
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # Ambiguous: treat comma as decimal only if it looks like one (2 digits after)
        parts = cleaned.split(",")
        if len(parts[-1]) == 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")

    try:
        return round(float(cleaned), 2)
    except ValueError as exc:
        raise ScrapeError(f"Could not parse price from text: {raw_text!r}") from exc


def fetch_product_data(
    url: str,
    price_selector: str,
    name_selector: str = "",
    fallback_name: str = "Product",
    timeout: int = 15,
    user_agent: str = "Mozilla/5.0",
) -> dict:
    """
    Fetch the product page and extract price (float) and name (str).

    Returns: {"name": str, "price": float, "url": str}
    Raises: ScrapeError on network failure, bad status code, or missing/unparsable price.
    """
    headers = {"User-Agent": user_agent}

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScrapeError(f"Failed to fetch {url}: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")

    price_element = soup.select_one(price_selector)
    if price_element is None:
        raise ScrapeError(
            f"Price selector '{price_selector}' matched nothing on {url}. "
            "The page layout may have changed — update PRICE_SELECTOR."
        )
    price = _parse_price(price_element.get_text())

    name = fallback_name
    if name_selector:
        name_element = soup.select_one(name_selector)
        if name_element is not None:
            name = name_element.get_text(strip=True)
    elif soup.title is not None:
        name = soup.title.get_text(strip=True) or fallback_name

    logger.info("Scraped price %.2f for '%s'", price, name)
    return {"name": name, "price": price, "url": url}
