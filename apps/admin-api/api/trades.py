"""Trading data endpoints."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_trades():
    """Get trades endpoint - to be implemented."""
    return {"message": "Trades endpoint - implementation pending"}
