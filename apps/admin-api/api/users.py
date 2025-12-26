"""User management endpoints."""

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_users():
    """List users endpoint - to be implemented."""
    return {"message": "List users endpoint - implementation pending"}

@router.post("/")
async def create_user():
    """Create user endpoint - to be implemented."""
    return {"message": "Create user endpoint - implementation pending"}
