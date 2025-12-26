"""
QuantShift Admin API - FastAPI Backend

Main application entry point for the admin control center.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import structlog

from core.config import settings
from api import auth, users, bot, email, trades

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Create FastAPI application
app = FastAPI(
    title="QuantShift Admin API",
    description="Admin control center API for QuantShift trading bot",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(bot.router, prefix="/api/bot", tags=["Bot Control"])
app.include_router(email.router, prefix="/api/email", tags=["Email Configuration"])
app.include_router(trades.router, prefix="/api/trades", tags=["Trading Data"])


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting QuantShift Admin API", environment=settings.ENVIRONMENT)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down QuantShift Admin API")


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "service": "QuantShift Admin API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
