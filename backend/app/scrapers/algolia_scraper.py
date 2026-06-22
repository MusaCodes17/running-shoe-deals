"""
Generic Algolia-backed scraper.

Several Canadian retailers (The Last Hunt and Altitude Sports — same parent
company) run Next.js storefronts with a commercetools catalogue exposed through
a public Algolia search index. Their own JavaScript queries Algolia with a
search-only API key; we use the same index, which returns price, original price,
stock, sizes and the product slug in a single request — no browser, no CSS.

Subclasses supply the Algolia app id / search key / index name and the product
URL path (e.g. "/p/"). Credentials are public values embedded in each site's
frontend and are overridable via scraper_config in case a site rotates them.
"""
import json
import logging
import time
from typing import List, Dict, Optional
from urllib.parse import urlsplit

from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class AlgoliaScraper(BaseScraper):
    """Scraper for a Next.js + commercetools store fronted by Algolia search."""

    def __init__(self, retailer_name: str, base_url: str, app_id: str,
                 api_key: str, index: str, product_path: str = "/p/",
                 homepage_url: str = None, search_selector: str = '[data-testid="global-search-input"]',
                 config: dict = None):
        merged = {
            "use_browser": False,
            "algolia_app_id": app_id,
            "algolia_api_key": api_key,
            "algolia_index": index,
            "product_path": product_path,
            # Used by automatic credential rediscovery if the key rotates.
            "homepage_url": homepage_url or base_url,
            "search_selector": search_selector,
        }
        merged.update(config or {})
        super().__init__(retailer_name=retailer_name, base_url=base_url, config=merged)
        # Guards against re-running rediscovery more than once per scrape session.
        self._rediscovered = False

    # ----- Algolia plumbing -------------------------------------------------

    def _algolia_url(self) -> str:
        app_id = self.config["algolia_app_id"].lower()
        index = self.config["algolia_index"]
        return f"https://{app_id}-dsn.algolia.net/1/indexes/{index}/query"

    def _do_algolia_request(self, query: str, hits_per_page: int):
        """
        Single Algolia request. Returns (hits, auth_error):
        - (list, False) on success
        - (None, True)  on a 401/403 auth error (key rotated / revoked)
        - (None, False) on any other failure
        """
        headers = {
            "X-Algolia-API-Key": self.config["algolia_api_key"],
            "X-Algolia-Application-Id": self.config["algolia_app_id"],
            "Content-Type": "application/json",
        }
        payload = {"query": query, "hitsPerPage": hits_per_page}
        try:
            resp = self.session.post(
                self._algolia_url(), headers=headers, data=json.dumps(payload), timeout=15
            )
            if resp.status_code in (401, 403):
                logger.warning(
                    f"[{self.retailer_name}] Algolia auth error {resp.status_code} "
                    f"(API key may have rotated)"
                )
                return None, True
            resp.raise_for_status()
            time.sleep(1)  # be polite
            return resp.json().get("hits", []), False
        except Exception as e:
            logger.error(f"[{self.retailer_name}] Algolia query failed for '{query}': {e}")
            return None, False

    def _algolia_query(self, query: str, hits_per_page: int = 20) -> List[Dict]:
        """
        Run a search against the Algolia index. On an auth error, attempt automatic
        credential rediscovery once per session, then retry. Always returns a list
        (empty on unrecoverable failure) — never raises.
        """
        hits, auth_error = self._do_algolia_request(query, hits_per_page)
        if not auth_error:
            return hits or []

        if self._rediscovered:
            return []  # already tried this session

        self._rediscovered = True
        logger.warning(f"[{self.retailer_name}] Attempting Algolia credential rediscovery…")
        creds = self.discover_algolia_credentials(
            self.config["homepage_url"], self.config["search_selector"]
        )
        if not creds:
            logger.error(f"[{self.retailer_name}] Rediscovery failed; returning no results")
            return []

        self.config["algolia_app_id"] = creds["app_id"]
        self.config["algolia_api_key"] = creds["api_key"]
        if creds.get("index"):
            self.config["algolia_index"] = creds["index"]
        logger.warning(
            f"[{self.retailer_name}] Rediscovered Algolia credentials "
            f"(app_id={creds['app_id']}, index={self.config['algolia_index']}). "
            f"⚠️  Update the hardcoded defaults in this scraper to make it permanent."
        )

        hits, auth_error = self._do_algolia_request(query, hits_per_page)
        if auth_error:
            logger.error(f"[{self.retailer_name}] Still auth error after rediscovery")
            return []
        return hits or []

    # ----- Hit parsing ------------------------------------------------------

    @staticmethod
    def _money(value: Optional[dict], pick_min: bool = True) -> Optional[float]:
        """
        Convert an Algolia money field to dollars.

        Shape is {"CAD": {"centAmount": <int | [int, ...]>}}. The price field is a
        list spanning the cheapest..dearest in-stock variant; original_price is a
        single MSRP. pick_min selects the best (lowest) price from a list.
        """
        if not isinstance(value, dict):
            return None
        cents = (value.get("CAD") or {}).get("centAmount")
        if isinstance(cents, list):
            cents = (min(cents) if pick_min else max(cents)) if cents else None
        if isinstance(cents, (int, float)):
            return round(cents / 100.0, 2)
        return None

    def _product_url(self, slug: str) -> str:
        return f"{self.base_url}{self.config['product_path']}{slug}"

    @staticmethod
    def _colorway_from_hit(hit: Dict, image_url: Optional[str]) -> Optional[str]:
        """
        Derive the colorway name from the hit's thumbnails.

        Each thumbnail is {color_name, image_url, price}. Prefer the thumbnail
        whose image matches the primary image; otherwise fall back to the first.
        """
        thumbs = hit.get("thumbnails") or []
        if not isinstance(thumbs, list) or not thumbs:
            return None
        if image_url:
            for t in thumbs:
                if isinstance(t, dict) and t.get("image_url") == image_url and t.get("color_name"):
                    return t["color_name"]
        first = thumbs[0]
        return first.get("color_name") if isinstance(first, dict) else None

    def _parse_hit(self, hit: Dict) -> Optional[Dict]:
        slug = hit.get("slug")
        if not slug:
            return None

        attributes = hit.get("attributes") or {}
        sizes = attributes.get("size") or attributes.get("size_1") or []
        sizes = [str(s).strip() for s in sizes if str(s).strip().upper() != "NA"]

        qty = hit.get("quantity_left")
        in_stock = (qty is None) or (qty > 0)

        image_url = hit.get("image_url")

        return {
            "product_url": self._product_url(slug),
            "name": hit.get("name", ""),
            "brand": attributes.get("brand_name") or "",
            "price": self._money(hit.get("price"), pick_min=True),
            "original_price": self._money(hit.get("original_price"), pick_min=False),
            "in_stock": in_stock,
            "sizes_available": sizes,
            "image_url": image_url,
            "colorway": self._colorway_from_hit(hit, image_url),
            "thumbnails": hit.get("thumbnails") or [],
            "_slug": slug,
        }

    @staticmethod
    def _matches(name: str, brand: str, model: str) -> bool:
        """True if every significant token of the model appears in the name."""
        name_l = name.lower()
        tokens = [t for t in model.lower().split() if t]
        if not tokens:
            return brand.lower() in name_l
        return all(t in name_l for t in tokens)

    def _slug_from_url(self, product_url: str) -> str:
        path = urlsplit(product_url).path
        marker = self.config["product_path"]
        return path.split(marker, 1)[-1].strip("/") if marker in path else path.strip("/")

    # ----- Public API -------------------------------------------------------

    def search_products(self, brand: str, model: str) -> List[Dict]:
        """
        Search the Algolia index for products matching brand + model.

        The returned dicts are already fully populated (price, stock, sizes), so
        get_product_details mostly just re-confirms a single product.
        """
        logger.info(f"[{self.retailer_name}] Searching Algolia for {brand} {model}")

        hits = self._algolia_query(f"{brand} {model}")
        results = []
        for hit in hits:
            name = hit.get("name", "")
            if not self._matches(name, brand, model):
                continue
            parsed = self._parse_hit(hit)
            if parsed and not any(p["product_url"] == parsed["product_url"] for p in results):
                results.append(parsed)

        self.log_scrape_attempt(brand, model, len(results))
        return results

    def get_product_details(self, product_url: str) -> Optional[Dict]:
        """
        Fetch fresh details for a single product by its slug.

        Re-queries Algolia with the slug's words and returns the hit whose slug
        matches exactly, so prices/stock reflect the latest index state.
        """
        slug = self._slug_from_url(product_url)
        if not slug:
            logger.warning(f"[{self.retailer_name}] Could not parse slug from {product_url}")
            return None

        hits = self._algolia_query(slug.replace("-", " "))
        for hit in hits:
            if hit.get("slug") == slug:
                return self._parse_hit(hit)

        logger.info(f"[{self.retailer_name}] No exact match for slug {slug}")
        return None
