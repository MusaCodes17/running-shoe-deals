"""
ForeRunners scraper implementation
Website: https://shop.forerunners.ca

Vancouver running specialty store on Shopify (English-only, no locale prefix).
"""
from app.scrapers.shopify_scraper import ShopifyScraper


class ForeRunnersScraper(ShopifyScraper):
    """Scraper for ForeRunners (shop.forerunners.ca)."""

    def __init__(self):
        super().__init__(
            retailer_name="ForeRunners",
            base_url="https://shop.forerunners.ca",
            config={"use_browser": False},
        )
