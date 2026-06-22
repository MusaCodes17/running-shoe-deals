"""
Models package - exports all models and schemas
"""
from app.models.models import Shoe, Retailer, PriceRecord, Deal, PromoCode
from app.models.schemas import (
    ShoeCreate, ShoeUpdate, ShoeResponse,
    RetailerCreate, RetailerUpdate, RetailerResponse,
    PriceRecordCreate, PriceRecordResponse,
    DealCreate, DealResponse,
    DashboardStats, ScrapeResult, ScrapeRequest, ShoeTestRequest,
    PromoCodeCreate, PromoCodeResponse
)

__all__ = [
    # Database models
    "Shoe", "Retailer", "PriceRecord", "Deal", "PromoCode",

    # Pydantic schemas
    "ShoeCreate", "ShoeUpdate", "ShoeResponse",
    "RetailerCreate", "RetailerUpdate", "RetailerResponse",
    "PriceRecordCreate", "PriceRecordResponse",
    "DealCreate", "DealResponse",
    "DashboardStats", "ScrapeResult", "ScrapeRequest", "ShoeTestRequest",
    "PromoCodeCreate", "PromoCodeResponse"
]
