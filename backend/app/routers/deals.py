"""
API routes for viewing deals
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from app.database import get_db
from app.models import Deal, DealResponse

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("/", response_model=List[DealResponse])
def get_deals(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = True,
    min_savings_percent: Optional[float] = Query(None, ge=0, le=100),
    brand: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all deals with optional filtering
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **is_active**: Filter by active status (default: True)
    - **min_savings_percent**: Minimum savings percentage (optional)
    - **brand**: Filter by shoe brand (optional)
    """
    query = db.query(Deal)
    
    # Filter by active status
    if is_active is not None:
        query = query.filter(Deal.is_active == is_active)
    
    # Filter by minimum savings percentage
    if min_savings_percent is not None:
        query = query.filter(Deal.savings_percent >= min_savings_percent)
    
    # Filter by brand (join with Shoe table)
    if brand:
        query = query.join(Deal.shoe).filter(Deal.shoe.has(brand=brand))
    
    # Order by savings percentage (best deals first)
    query = query.order_by(desc(Deal.savings_percent))
    
    deals = query.offset(skip).limit(limit).all()
    return deals


@router.get("/{deal_id}", response_model=DealResponse)
def get_deal(deal_id: int, db: Session = Depends(get_db)):
    """
    Get a specific deal by ID
    """
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with id {deal_id} not found"
        )
    
    return deal


@router.put("/{deal_id}/deactivate", response_model=DealResponse)
def deactivate_deal(deal_id: int, db: Session = Depends(get_db)):
    """
    Mark a deal as inactive (e.g., when purchased or expired)
    """
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    
    if not deal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deal with id {deal_id} not found"
        )
    
    deal.is_active = False
    db.commit()
    db.refresh(deal)
    return deal


@router.get("/shoe/{shoe_id}", response_model=List[DealResponse])
def get_deals_for_shoe(
    shoe_id: int,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all deals for a specific shoe
    """
    query = db.query(Deal).filter(Deal.shoe_id == shoe_id)
    
    if is_active is not None:
        query = query.filter(Deal.is_active == is_active)
    
    query = query.order_by(desc(Deal.savings_percent))
    deals = query.all()
    return deals


@router.get("/retailer/{retailer_id}", response_model=List[DealResponse])
def get_deals_from_retailer(
    retailer_id: int,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all deals from a specific retailer
    """
    query = db.query(Deal).filter(Deal.retailer_id == retailer_id)
    
    if is_active is not None:
        query = query.filter(Deal.is_active == is_active)
    
    query = query.order_by(desc(Deal.savings_percent))
    deals = query.all()
    return deals
