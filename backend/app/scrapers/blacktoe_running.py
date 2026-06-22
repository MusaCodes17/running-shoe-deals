"""
BlackToe Running scraper implementation
Website: https://www.blacktoerunning.com

Toronto running specialty store on Shopify (English-only, no locale prefix).
"""
from app.scrapers.shopify_scraper import ShopifyScraper


class BlackToeRunningScraper(ShopifyScraper):
    """Scraper for BlackToe Running (blacktoerunning.com)."""

    def __init__(self):
        super().__init__(
            retailer_name="BlackToe Running",
            base_url="https://www.blacktoerunning.com",
            config={"use_browser": False},
        )
