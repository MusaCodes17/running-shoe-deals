"""
En Route Run scraper (enroute.run)

Vancouver-based running specialist. Backed by Shopify (cdn.shopify.com,
myshopify.com show up in the page source) but the storefront itself is a
headless Astro site — it does NOT expose the standard Shopify endpoints our
generic ShopifyScraper relies on:

    /products.json              -> 404
    /products/<handle>.js       -> 404
    /search/suggest.json        -> unusable

Instead, every page (product pages AND search results) embeds the Shopify
Storefront API's variant data inline as serialized hydration JSON for an
Astro/Qwik island (HTML-entity-encoded, e.g. `&quot;availableForSale&quot;`).
Each variant block is self-contained — id, availableForSale, price,
compareAtPrice, the "Colour / Size" variant title, and the parent product's
title + handle — so it's parsed directly with regex rather than a JSON
endpoint. This is more reliable than the rendered Product JSON-LD block also
present on product pages, because the JSON-LD doesn't include compareAtPrice
(so it can't tell us whether something is actually on sale).

The same variant blob also appears on /search?q=<query> results pages
(re-used for "frequently bought together" / recommendation widgets), so
search and detail use the same parser, just filtered to a different handle.
"""
import html as ihtml
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import quote, urlsplit

from app.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class EnRouteRunScraper(BaseScraper):
    """Scraper for En Route Run (enroute.run) — headless Astro + Shopify backend."""

    # Each variant's hydration block starts here; splitting on this marker
    # isolates one variant's JSON per chunk (next variant = next split item).
    _VARIANT_MARKER = '"availableForSale":[0,'

    def __init__(self):
        super().__init__(
            retailer_name="En Route Run",
            base_url="https://enroute.run",
            config={"use_browser": False},
        )

    # ----- variant-blob parsing ---------------------------------------------

    def _parse_variant_blocks(self, html_text: str) -> List[Dict]:
        """
        Parse every embedded Shopify variant block on a page (product page or
        search results page) into raw dicts. Entity-unescaped up front so the
        regexes below match plain JSON syntax instead of &quot;-encoded HTML.
        """
        text = ihtml.unescape(html_text)
        blocks = []
        for chunk in text.split(self._VARIANT_MARKER)[1:]:
            avail_m = re.match(r'(true|false)', chunk)
            if not avail_m:
                continue
            price_m = re.search(r'"price":\[0,\{"amount":\[0,"([0-9.]+)"', chunk)
            if not price_m:
                continue
            compare_m = re.search(r'"compareAtPrice":\[0,\{"amount":\[0,"([0-9.]+)"', chunk)
            variant_title_m = re.search(r'"title":\[0,"([^"]*)"', chunk)
            product_title_m = re.search(r'"product":\[0,\{"title":\[0,"([^"]*)"', chunk)
            handle_m = re.search(r'"handle":\[0,"([a-z0-9-]+)"', chunk)
            image_m = re.search(r'"image":\[0,\{[^}]*?"url":\[0,"([^"]*)"', chunk)
            if not (variant_title_m and product_title_m and handle_m):
                continue
            blocks.append({
                "available": avail_m.group(1) == "true",
                "price": float(price_m.group(1)),
                "compare_at_price": float(compare_m.group(1)) if compare_m else None,
                "variant_title": variant_title_m.group(1),
                "product_title": product_title_m.group(1),
                "handle": handle_m.group(1),
                "image_url": image_m.group(1) if image_m else None,
            })
        return blocks

    @staticmethod
    def _dedupe_variants(blocks: List[Dict]) -> List[Dict]:
        """The same variant blob is embedded multiple times per page (buy box,
        recommendation widgets, etc.) — collapse to one entry per variant."""
        seen = {}
        for b in blocks:
            seen[(b["handle"], b["variant_title"])] = b
        return list(seen.values())

    @staticmethod
    def _matches(title: str, brand: str, model: str) -> bool:
        """True if every significant token of the model appears in the title."""
        title_l = title.lower()
        tokens = [t for t in model.lower().split() if t]
        if not tokens:
            return brand.lower() in title_l
        return all(t in title_l for t in tokens)

    def _handle_from_url(self, product_url: str) -> Optional[str]:
        path = urlsplit(product_url).path
        if "/products/" not in path:
            return None
        return path.split("/products/", 1)[1].strip("/").split("/")[0] or None

    # ----- Public API ---------------------------------------------------------

    def search_products(self, brand: str, model: str) -> List[Dict]:
        query = f"{brand} {model}".strip()
        url = f"{self.base_url}/search?q={quote(query)}"
        logger.info(f"[{self.retailer_name}] Searching: {url}")

        html_text = self.fetch_page(url, use_browser=False)
        if not html_text:
            logger.warning(f"[{self.retailer_name}] No search results for '{query}'")
            return []

        # Search-result cards are <a href="/products/<handle>"> immediately
        # followed by an <img alt="<Title> product image">.
        text = ihtml.unescape(html_text)
        pairs = re.findall(
            r'href="(/products/[a-z0-9-]+)"[^>]*>.*?alt="([^"]+?)\s+product image"',
            text, re.S,
        )

        results = []
        seen_handles = set()
        for href, title in pairs:
            if not self._matches(title, brand, model):
                continue
            handle = href.rsplit("/products/", 1)[1]
            if handle in seen_handles:
                continue
            seen_handles.add(handle)
            results.append({
                "product_url": f"{self.base_url}/products/{handle}",
                "name": title,
                "price": None,
                "original_price": None,
                "in_stock": True,
                "sizes_available": [],  # filled in by get_product_details
                "image_url": None,
                "colorway": None,
            })

        self.log_scrape_attempt(brand, model, len(results))
        return results

    def get_product_details(self, product_url: str) -> Optional[Dict]:
        handle = self._handle_from_url(product_url)
        if not handle:
            logger.warning(f"[{self.retailer_name}] Could not parse handle from {product_url}")
            return None

        html_text = self.fetch_page(product_url, use_browser=False)
        if not html_text:
            return None

        blocks = [b for b in self._parse_variant_blocks(html_text) if b["handle"] == handle]
        variants = self._dedupe_variants(blocks)
        if not variants:
            logger.warning(f"[{self.retailer_name}] No variant data found for {handle}")
            return None

        available = [v for v in variants if v["available"]]
        if available:
            # Prefer the cheapest available variant with a real markdown;
            # fall back to the cheapest available full-price variant. Mirrors
            # the same available-variants-only fix applied to ShopifyScraper
            # (the product can have sold-out sale colorways alongside in-stock
            # full-price ones, or vice versa).
            on_sale = [v for v in available if v["compare_at_price"] and v["compare_at_price"] > v["price"]]
            chosen = min(on_sale, key=lambda v: v["price"]) if on_sale else min(available, key=lambda v: v["price"])
            price = chosen["price"]
            original_price = chosen["compare_at_price"] if chosen in on_sale else None
            in_stock = True
        else:
            price = None
            original_price = None
            in_stock = False

        sizes_available = []
        for v in available:
            size = self.extract_numeric_size(v["variant_title"].rsplit("/", 1)[-1].strip())
            if size and size not in sizes_available:
                sizes_available.append(size)

        # All distinct colourways the product comes in (not just the chosen
        # variant's) — matches the convention used by ShopifyScraper.
        colorways = []
        for v in variants:
            colour = v["variant_title"].rsplit("/", 1)[0].strip()
            if colour and colour not in colorways:
                colorways.append(colour)

        image_url = next((v["image_url"] for v in variants if v["image_url"]), None)

        return {
            "product_url": f"{self.base_url}/products/{handle}",
            "name": variants[0]["product_title"],
            "brand": "",
            "price": price,
            "original_price": original_price,
            "in_stock": in_stock,
            "sizes_available": sorted(sizes_available, key=lambda x: float(x) if x else 0),
            "image_url": image_url,
            "colorway": ", ".join(colorways) if colorways else None,
        }
