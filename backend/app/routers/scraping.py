"""
API routes for scraping operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models import ScrapeRequest, ScrapeResult
from app.scrapers.scraper_manager import ScraperManager
from datetime import datetime

router = APIRouter(prefix="/scrape", tags=["scraping"])


@router.post("/shoe/{shoe_id}", response_model=dict)
def scrape_shoe(
    shoe_id: int,
    retailer_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """
    Manually trigger scraping for a specific shoe
    
    - **shoe_id**: ID of the shoe to scrape
    - **retailer_ids**: Optional list of retailer IDs (if None, scrape all active retailers)
    """
    manager = ScraperManager(db)
    
    try:
        results = manager.scrape_shoe(shoe_id, retailer_ids)
        
        if not results.get('success', True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=results.get('error', 'Unknown error')
            )
        
        return {
            "success": True,
            "message": f"Scraping completed for shoe ID {shoe_id}",
            "results": results,
            "scraped_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraping failed: {str(e)}"
        )


@router.post("/all", response_model=dict)
def scrape_all_shoes(
    retailer_ids: Optional[List[int]] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Manually trigger scraping for all active shoes
    
    This can take a while, so consider running in background
    
    - **retailer_ids**: Optional list of retailer IDs (if None, scrape all active retailers)
    """
    manager = ScraperManager(db)
    
    try:
        results = manager.scrape_all_shoes(retailer_ids)
        
        return {
            "success": True,
            "message": "Scraping completed for all active shoes",
            "results": results,
            "scraped_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scraping failed: {str(e)}"
        )


@router.post("/retailer/{retailer_id}", response_model=dict)
def scrape_retailer(
    retailer_id: int,
    shoe_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """
    Scrape a specific retailer for all shoes (or specific shoes)
    
    - **retailer_id**: ID of the retailer to scrape
    - **shoe_ids**: Optional list of shoe IDs (if None, scrape all active shoes)
    """
    from app.models.models import Shoe
    
    manager = ScraperManager(db)
    
    # Get shoes to scrape
    query = db.query(Shoe).filter(Shoe.is_active == True)
    if shoe_ids:
        query = query.filter(Shoe.id.in_(shoe_ids))
    
    shoes = query.all()
    
    if not shoes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active shoes found"
        )
    
    aggregated_results = {
        'total_shoes': len(shoes),
        'total_products_found': 0,
        'total_prices_recorded': 0,
        'total_deals_found': 0,
        'errors': []
    }
    
    for shoe in shoes:
        results = manager.scrape_shoe(shoe.id, [retailer_id])
        
        aggregated_results['total_products_found'] += results.get('products_found', 0)
        aggregated_results['total_prices_recorded'] += results.get('prices_recorded', 0)
        aggregated_results['total_deals_found'] += results.get('deals_found', 0)
        
        if results.get('errors'):
            aggregated_results['errors'].extend(results['errors'])
    
    return {
        "success": True,
        "message": f"Scraping completed for retailer ID {retailer_id}",
        "results": aggregated_results,
        "scraped_at": datetime.utcnow().isoformat()
    }


@router.post("/promos", response_model=dict)
def detect_all_promos(db: Session = Depends(get_db)):
    """
    Scan all active retailers' sites for discount codes.
    """
    manager = ScraperManager(db)
    try:
        results = manager.detect_all_promo_codes()
        return {
            "success": True,
            "message": "Promo code detection completed",
            "results": results,
            "scraped_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Promo detection failed: {str(e)}"
        )


@router.post("/promos/{retailer_id}", response_model=dict)
def detect_retailer_promos(retailer_id: int, db: Session = Depends(get_db)):
    """
    Scan a single retailer's site for discount codes.
    """
    from app.models.models import Retailer

    retailer = db.query(Retailer).filter(Retailer.id == retailer_id).first()
    if not retailer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retailer with id {retailer_id} not found"
        )

    manager = ScraperManager(db)
    try:
        results = manager.detect_promo_codes_for_retailer(retailer)
        return {
            "success": True,
            "message": f"Promo detection completed for {retailer.name}",
            "results": results,
            "scraped_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Promo detection failed: {str(e)}"
        )


@router.get("/test/the-last-hunt")
def test_the_last_hunt_scraper(
    brand: str = "Nike",
    model: str = "Vaporfly"
):
    """
    Test The Last Hunt scraper without database
    
    Quick test to verify scraper is working
    
    - **brand**: Shoe brand to search for
    - **model**: Shoe model to search for
    """
    from app.scrapers.the_last_hunt import TheLastHuntScraper
    
    scraper = TheLastHuntScraper()
    
    try:
        # Search for products
        products = scraper.search_products(brand, model)
        
        # Get details for first product if found
        product_details = []
        for product in products[:3]:  # Limit to first 3 to avoid long wait
            details = scraper.get_product_details(product['product_url'])
            if details:
                product_details.append(details)
        
        return {
            "success": True,
            "search_query": f"{brand} {model}",
            "products_found": len(products),
            "products": products,
            "detailed_results": product_details,
            "tested_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )


@router.get("/test/altitude-sports")
def test_altitude_sports_scraper(
    brand: str = "Saucony",
    model: str = "Endorphin"
):
    """
    Test the Altitude Sports (Algolia) scraper without touching the database.
    """
    from app.scrapers.altitude_sports import AltitudeSportsScraper

    scraper = AltitudeSportsScraper()

    try:
        products = scraper.search_products(brand, model)
        product_details = []
        for product in products[:3]:
            details = scraper.get_product_details(product['product_url'])
            if details:
                product_details.append(details)

        return {
            "success": True,
            "search_query": f"{brand} {model}",
            "products_found": len(products),
            "products": products,
            "detailed_results": product_details,
            "tested_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )


@router.get("/test/jd-sports")
def test_jd_sports_scraper(
    brand: str = "Adidas",
    model: str = "Adizero Boston 13"
):
    """
    Test the JD Sports (Shopify) scraper without touching the database.

    Defaults to the Adidas Adizero Boston 13 — the product the old scraper
    couldn't find.
    """
    from app.scrapers.jd_sports import JDSportsScraper

    scraper = JDSportsScraper()

    try:
        products = scraper.search_products(brand, model)

        product_details = []
        for product in products[:3]:
            details = scraper.get_product_details(product['product_url'])
            if details:
                product_details.append(details)

        return {
            "success": True,
            "search_query": f"{brand} {model}",
            "products_found": len(products),
            "products": products,
            "detailed_results": product_details,
            "tested_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )
