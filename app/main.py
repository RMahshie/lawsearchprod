"""
LawSearch AI - FastAPI Backend

Main FastAPI application for querying U.S. federal appropriations bills
using Retrieval-Augmented Generation (RAG) with intelligent routing.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import API routers
from app.api.endpoints.query import router as query_router
# Import configuration
from app.core.config import get_settings

# Get settings instance
settings = get_settings()

# Create FastAPI application instance
app = FastAPI(
    title="LawSearch AI API",
    description="A Retrieval-Augmented Generation (RAG) system for querying U.S. federal appropriations bills",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "LawSearch AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

# Include API routers
app.include_router(query_router, prefix="/api", tags=["query"])

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )