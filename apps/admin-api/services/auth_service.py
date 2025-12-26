"""
Authentication service for user login, logout, and token management.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib

from models.user import User
from models.session import Session as UserSession
from core.security import verify_password, create_access_token, create_refresh_token, decode_token
from core.config import settings
import structlog

logger = structlog.get_logger()


class AuthService:
    """Authentication service."""
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            db: Database session
            email: User email
            password: Plain text password
        
        Returns:
            User object if authentication successful, None otherwise
        """
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            logger.warning("Authentication failed - user not found", email=email)
            return None
        
        if not user.is_active:
            logger.warning("Authentication failed - user inactive", email=email)
            return None
        
        if not verify_password(password, user.password_hash):
            logger.warning("Authentication failed - invalid password", email=email)
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.info("User authenticated successfully", email=email, user_id=str(user.id))
        return user
    
    @staticmethod
    def create_user_tokens(db: Session, user: User) -> Dict[str, str]:
        """
        Create access and refresh tokens for user.
        
        Args:
            db: Database session
            user: User object
        
        Returns:
            Dictionary with access_token and refresh_token
        """
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        
        # Create refresh token
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Store refresh token hash in database
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        session = UserSession(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        
        db.add(session)
        db.commit()
        
        logger.info("Tokens created for user", user_id=str(user.id))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    
    @staticmethod
    def verify_refresh_token(db: Session, refresh_token: str) -> Optional[User]:
        """
        Verify refresh token and return user.
        
        Args:
            db: Database session
            refresh_token: Refresh token string
        
        Returns:
            User object if token valid, None otherwise
        """
        # Decode token
        payload = decode_token(refresh_token)
        if not payload:
            logger.warning("Invalid refresh token - decode failed")
            return None
        
        # Check token type
        if payload.get("type") != "refresh":
            logger.warning("Invalid token type", token_type=payload.get("type"))
            return None
        
        # Get user ID
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Invalid refresh token - no user ID")
            return None
        
        # Verify token exists in database
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = db.query(UserSession).filter(
            UserSession.token_hash == token_hash,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if not session:
            logger.warning("Refresh token not found or expired", user_id=user_id)
            return None
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            logger.warning("User not found or inactive", user_id=user_id)
            return None
        
        logger.info("Refresh token verified", user_id=user_id)
        return user
    
    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token: str) -> bool:
        """
        Revoke refresh token (logout).
        
        Args:
            db: Database session
            refresh_token: Refresh token string
        
        Returns:
            True if token revoked, False otherwise
        """
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = db.query(UserSession).filter(UserSession.token_hash == token_hash).first()
        
        if session:
            db.delete(session)
            db.commit()
            logger.info("Refresh token revoked", session_id=str(session.id))
            return True
        
        logger.warning("Refresh token not found for revocation")
        return False
    
    @staticmethod
    def revoke_all_user_tokens(db: Session, user_id: str) -> int:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Number of tokens revoked
        """
        count = db.query(UserSession).filter(UserSession.user_id == user_id).delete()
        db.commit()
        
        logger.info("All user tokens revoked", user_id=user_id, count=count)
        return count
    
    @staticmethod
    def cleanup_expired_sessions(db: Session) -> int:
        """
        Clean up expired sessions.
        
        Args:
            db: Database session
        
        Returns:
            Number of sessions deleted
        """
        count = db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).delete()
        db.commit()
        
        logger.info("Expired sessions cleaned up", count=count)
        return count
