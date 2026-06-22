"""
Scrapers package
"""
from app.scrapers.base_scraper import BaseScraper
from app.scrapers.the_last_hunt import TheLastHuntScraper
from app.scrapers.scraper_manager import ScraperManager

__all__ = [
    "BaseScraper",
    "TheLastHuntScraper",
    "ScraperManager"
]
