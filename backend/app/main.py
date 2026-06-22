"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.database import init_db
from app.routers import shoes, retailers, deals, dashboard, scraping, export

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Running Shoe Deal Finder",
    description="API for finding deals on running shoes from Canadian retailers",
    version="1.0.0"
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database tables on application startup"""
    init_db()
    print("✅ Database initialized")


# Include routers
app.include_router(shoes.router, prefix="/api")
app.include_router(retailers.router, prefix="/api")
app.include_router(deals.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(scraping.router, prefix="/api")
app.include_router(export.router, prefix="/api")


# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint - API information"""
    return {
        "message": "Running Shoe Deal Finder API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# To run this application, use: python run.py from the backend directory
# Or use: uvicorn app.main:app --reload
