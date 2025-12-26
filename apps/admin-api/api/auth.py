"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from core.security import decode_token
from schemas.auth import LoginRequest, LoginResponse, TokenResponse, UserResponse
from services.auth_service import AuthService
from models.user import User
import structlog

logger = structlog.get_logger()
router = APIRouter()


def get_current_user_from_token(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from access token cookie.
    
    Args:
        access_token: JWT access token from cookie
        db: Database session
    
    Returns:
        User object
    
    Raises:
        HTTPException: If token invalid or user not found
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Decode token
    payload = decode_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Get user
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    
    Returns access and refresh tokens in httpOnly cookies.
    """
    # Authenticate user
    user = AuthService.authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create tokens
    tokens = AuthService.create_user_tokens(db, user)
    
    # Create response
    response = JSONResponse(
        content={
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            },
            "token_type": "bearer"
        }
    )
    
    # Set httpOnly cookies
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=True,  # HTTPS only in production
        samesite="lax",
        max_age=60 * 15  # 15 minutes
    )
    
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7  # 7 days
    )
    
    logger.info("User logged in", user_id=str(user.id), email=user.email)
    
    return response


@router.post("/logout")
async def logout(
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Logout user by revoking refresh token.
    """
    if refresh_token:
        AuthService.revoke_refresh_token(db, refresh_token)
    
    # Create response
    response = JSONResponse(
        content={"message": "Logged out successfully"}
    )
    
    # Clear cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    logger.info("User logged out")
    
    return response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )
    
    # Verify refresh token
    user = AuthService.verify_refresh_token(db, refresh_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new tokens
    tokens = AuthService.create_user_tokens(db, user)
    
    # Create response
    response = JSONResponse(
        content={
            "token_type": "bearer"
        }
    )
    
    # Set new cookies
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 15
    )
    
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7
    )
    
    logger.info("Token refreshed", user_id=str(user.id))
    
    return response


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Get current authenticated user.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )
