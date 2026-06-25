"""
Models package - exports all models and schemas
"""
from app.models.models import Shoe, Retailer, PriceRecord, Deal, PromoCode, OwnedShoe, ShoeRun, ShoeNote, AppSettings
from app.models.schemas import (
    ShoeCreate, ShoeUpdate, ShoeResponse,
    RetailerCreate, RetailerUpdate, RetailerResponse,
    PriceRecordCreate, PriceRecordResponse,
    DealCreate, DealResponse,
    DashboardStats, ScrapeResult, ScrapeRequest, ShoeTestRequest,
    PromoCodeCreate, PromoCodeResponse,
    OwnedShoeCreate, OwnedShoeUpdate, OwnedShoeResponse,
    ShoeRunCreate, ShoeRunResponse, LogRunResponse,
    ShoeNoteCreate, ShoeNoteResponse,
    CorosRun, CorosFetchResponse, CorosAssignment, CorosConfirmRequest,
    CorosConfirmResponse, CorosSyncStatus,
)

__all__ = [
    # Database models
    "Shoe", "Retailer", "PriceRecord", "Deal", "PromoCode", "OwnedShoe", "ShoeRun", "ShoeNote",
    "AppSettings",

    # Pydantic schemas
    "ShoeCreate", "ShoeUpdate", "ShoeResponse",
    "RetailerCreate", "RetailerUpdate", "RetailerResponse",
    "PriceRecordCreate", "PriceRecordResponse",
    "DealCreate", "DealResponse",
    "DashboardStats", "ScrapeResult", "ScrapeRequest", "ShoeTestRequest",
    "PromoCodeCreate", "PromoCodeResponse",
    "OwnedShoeCreate", "OwnedShoeUpdate", "OwnedShoeResponse",
    "ShoeRunCreate", "ShoeRunResponse", "LogRunResponse",
    "ShoeNoteCreate", "ShoeNoteResponse",
    "CorosRun", "CorosFetchResponse", "CorosAssignment", "CorosConfirmRequest",
    "CorosConfirmResponse", "CorosSyncStatus",
]
