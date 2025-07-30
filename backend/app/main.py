"""
Main FastAPI application for AI Code Review Squad.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis import init_redis, close_redis, cache
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    try:
        # Initialize database
        await init_db()
        print("✅ Database initialized")
        
        # Initialize Redis
        await init_redis()
        global cache
        from app.core.redis import RedisCache, redis_client
        cache = RedisCache(redis_client)
        print("✅ Redis initialized")
        
        print("🚀 AI Code Review Squad started successfully!")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        await close_db()
        await close_redis()
        print("✅ Application shutdown complete")
    except Exception as e:
        print(f"❌ Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title="AI Code Review Squad",
    description="Multi-agent AI system for comprehensive code reviews",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts,
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
            "path": str(request.url.path)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        from app.core.database import async_engine
        async with async_engine.begin() as conn:
            await conn.execute("SELECT 1")
        
        # Check Redis connection
        from app.core.redis import redis_client
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "service": "AI Code Review Squad",
            "version": "1.0.0",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "AI Code Review Squad",
        "version": "1.0.0",
        "description": "Multi-agent AI system for comprehensive code reviews",
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1"
    }


# Include API router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
