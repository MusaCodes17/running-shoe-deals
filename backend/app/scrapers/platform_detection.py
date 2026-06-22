"""
Platform detection for newly-created retailers.

Decides whether a retailer is "shopify", "algolia", or "custom" so the right
generic scraper (ShopifyScraper / AlgoliaScraper) can be wired up automatically
on creation, per the platform table in CLAUDE.md's Retailer Platform Analysis.
"""
import logging
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)

ALGOLIA_REQUIRED_KEYS = ("algolia_app_id", "algolia_api_key", "algolia_index")

PLATFORMS = ("shopify", "algolia", "custom")


class PlatformDetectionError(ValueError):
    """Raised when the requested platform can't be honored (e.g. missing creds)."""


def has_algolia_credentials(scraper_config: Optional[dict]) -> bool:
    cfg = scraper_config or {}
    return all(cfg.get(k) for k in ALGOLIA_REQUIRED_KEYS)


def probe_shopify(base_url: str) -> bool:
    """
    GET {base_url}/products.json — Shopify stores serve a public catalogue
    there. Network failures are treated as "not Shopify" rather than raised,
    so a flaky probe never blocks retailer creation.
    """
    url = base_url.rstrip("/") + "/products.json"
    try:
        resp = requests.get(
            url,
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0 (compatible; running-shoe-deals platform probe)"},
        )
        if resp.status_code != 200:
            return False
        data = resp.json()
        return isinstance(data, dict) and isinstance(data.get("products"), list)
    except Exception as e:
        logger.warning(f"Shopify probe failed for {base_url}: {e}")
        return False


def determine_platform(
    base_url: str,
    requested_platform: Optional[str],
    scraper_config: Optional[dict],
) -> Tuple[str, bool]:
    """
    Resolve the platform for a retailer being created, and whether scraping
    should be force-enabled.

    Returns (platform, scraping_enabled).
    Raises PlatformDetectionError if 'algolia' is requested/implied without
    the required credentials in scraper_config.
    """
    if requested_platform is not None and requested_platform not in PLATFORMS:
        raise PlatformDetectionError(
            f"Unknown platform '{requested_platform}'. Must be one of {PLATFORMS}."
        )

    algolia_creds_present = has_algolia_credentials(scraper_config)

    wants_algolia = requested_platform == "algolia" or (
        requested_platform is None and algolia_creds_present
    )
    if wants_algolia:
        if not algolia_creds_present:
            raise PlatformDetectionError(
                "Algolia retailers require scraper_config with algolia_app_id, "
                "algolia_api_key, and algolia_index."
            )
        return "algolia", True

    if requested_platform == "shopify":
        return "shopify", True

    if requested_platform == "custom":
        return "custom", False

    # No explicit platform requested and no Algolia credentials — auto-detect.
    if probe_shopify(base_url):
        return "shopify", True

    return "custom", False
