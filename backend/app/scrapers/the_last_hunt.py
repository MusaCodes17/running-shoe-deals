"""
The Last Hunt scraper implementation
Website: https://www.thelasthunt.com

The Last Hunt is a Next.js storefront whose catalogue is powered by Algolia
(commercetools behind it). The old CSS-selector approach found nothing because
products are rendered client-side; this scraper talks to the same public Algolia
index the site's own JavaScript uses. See AlgoliaScraper for the shared logic.

The Algolia application id + search-only API key + index name are public values
embedded in the site's frontend (discovered by inspecting its search requests).
"""
from app.scrapers.algolia_scraper import AlgoliaScraper

# Public Algolia credentials used by thelasthunt.com's own frontend.
ALGOLIA_APP_ID = "2YG4O6L95L"
ALGOLIA_API_KEY = "e8b31524fd0d708f603240f2bfaec48a"
ALGOLIA_INDEX = "PRODUCTS_TLH_en-CA"


class TheLastHuntScraper(AlgoliaScraper):
    """Scraper for The Last Hunt (thelasthunt.com) via its Algolia index."""

    def __init__(self):
        super().__init__(
            retailer_name="The Last Hunt",
            base_url="https://www.thelasthunt.com",
            app_id=ALGOLIA_APP_ID,
            api_key=ALGOLIA_API_KEY,
            index=ALGOLIA_INDEX,
            product_path="/p/",
        )
