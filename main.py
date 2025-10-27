"""
Ask Rumi Backend - Main FastAPI Application
Local, offline-first AI mentor app inspired by Rumi's wisdom.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path

# Import routers
from routes import chat, models, providers, system

# Create FastAPI app
app = FastAPI(
    title="Ask Rumi Backend",
    description="Local, offline-first AI mentor app inspired by Rumi's wisdom",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for React Native frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(providers.router, prefix="/api/providers", tags=["providers"])
app.include_router(system.router, prefix="/api/system", tags=["system"])

# Mount static files for frontend
app.mount("/frontend", StaticFiles(directory="frontend_test"), name="frontend")

@app.get("/")
async def root():
    """Root endpoint - health check and basic info"""
    return JSONResponse({
        "message": "Ask Rumi Backend is running",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
        "endpoints": {
            "chat": "/api/chat",
            "models": "/api/models", 
            "providers": "/api/providers",
            "system": "/api/system"
        }
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"  # Will be updated with actual timestamp
    })

if __name__ == "__main__":
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
