"""
JD Sports Canada scraper.
Website: https://jdsports.ca

JD Sports Canada runs on Shopify, so we reuse the generic ShopifyScraper which
talks to the JSON endpoints. This reliably finds products the old CSS-based
approach missed (e.g. the Adidas Adizero Boston 13).
"""
from app.scrapers.shopify_scraper import ShopifyScraper


class JDSportsScraper(ShopifyScraper):
    """Scraper for JD Sports Canada (jdsports.ca)."""

    def __init__(self):
        super().__init__(
            retailer_name="JD Sports Canada",
            base_url="https://jdsports.ca",
            config={"use_browser": False},
        )
