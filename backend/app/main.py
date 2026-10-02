"""OmniLog Backend API - Main Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.db import engine, Base

settings = get_settings()

# Create all database tables at startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="Video Game & TV Series Tracking API",
    version=settings.app_version,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Root endpoint - returns API information"""
    return {
        "message": "OmniLog Backend is running!",
        "version": settings.app_version,
        "environment": settings.environment
    }


@app.get("/health")
def health_check():
    """Health check endpoint - verifies API is operational"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "debug": settings.debug
    }