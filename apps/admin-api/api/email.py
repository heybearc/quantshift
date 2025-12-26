"""Email configuration endpoints."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/config")
async def get_email_config():
    """Get email config endpoint - to be implemented."""
    return {"message": "Email config endpoint - implementation pending"}
