"""
Altitude Sports scraper implementation
Website: https://www.altitude-sports.com

Altitude Sports shares The Last Hunt's parent company and runs the identical
Next.js + commercetools + Algolia stack, so it reuses AlgoliaScraper with its
own (public) Algolia credentials and index.
"""
from app.scrapers.algolia_scraper import AlgoliaScraper

# Public Algolia credentials used by altitude-sports.com's own frontend.
ALGOLIA_APP_ID = "I2Q2BWZE3K"
ALGOLIA_API_KEY = "8b62285e596a476fadc22970ed58e04a"
ALGOLIA_INDEX = "PRODUCTS_ALS_en-CA"


class AltitudeSportsScraper(AlgoliaScraper):
    """Scraper for Altitude Sports (altitude-sports.com) via its Algolia index."""

    def __init__(self):
        super().__init__(
            retailer_name="Altitude Sports",
            base_url="https://www.altitude-sports.com",
            app_id=ALGOLIA_APP_ID,
            api_key=ALGOLIA_API_KEY,
            index=ALGOLIA_INDEX,
            product_path="/p/",
        )
