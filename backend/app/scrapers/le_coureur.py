"""
Le Coureur scraper implementation
Website: https://lecoureur.com

Quebec running specialty store on Shopify. Uses the /en locale; ShopifyScraper
builds all endpoints from base_url so the prefix flows through automatically.
(Note: some product titles remain in French even on /en.)
"""
from app.scrapers.shopify_scraper import ShopifyScraper


class LeCoureurScraper(ShopifyScraper):
    """Scraper for Le Coureur (lecoureur.com)."""

    def __init__(self):
        super().__init__(
            retailer_name="Le Coureur",
            base_url="https://lecoureur.com/en",
            config={"use_browser": False},
        )
