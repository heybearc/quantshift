"""Bot control endpoints."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def get_bot_status():
    """Get bot status endpoint - to be implemented."""
    return {"message": "Bot status endpoint - implementation pending"}
