"""
Boutique Endurance scraper implementation
Website: https://www.boutiqueendurance.ca

Quebec running specialty store on Shopify. Uses the English locale (/en) so
titles/handles resolve in English; ShopifyScraper builds all endpoints
(suggest.json, products/<handle>.js) from base_url, so the /en prefix flows
through automatically.
"""
from app.scrapers.shopify_scraper import ShopifyScraper


class BoutiqueEnduranceScraper(ShopifyScraper):
    """Scraper for Boutique Endurance (boutiqueendurance.ca)."""

    def __init__(self):
        super().__init__(
            retailer_name="Boutique Endurance",
            base_url="https://www.boutiqueendurance.ca/en",
            config={"use_browser": False},
        )
