"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging

from app.db.database import get_db
from app.models import User
from app.schemas import UserResponse, TokenData
from app.services import auth_service
from app.services.google_calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.get("/login")
async def login():
    """
    Initiate Google OAuth login flow
    
    Returns:
        Dict with authorization URL
    """
    try:
        auth_url = auth_service.get_authorization_url()
        return {
            "authorization_url": auth_url,
            "message": "Redirect user to this URL for authentication"
        }
    except Exception as e:
        logger.error(f"Error generating auth URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )


@router.get("/callback")
async def auth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle OAuth callback from Google
    
    Args:
        code: Authorization code
        db: Database session
    
    Returns:
        User data and JWT tokens
    """
    try:
        # Exchange code for tokens
        token_result = await auth_service.get_token_from_code(code)
        
        access_token = token_result.get("access_token")
        refresh_token = token_result.get("refresh_token")
        expires_in = token_result.get("expires_in", 3600)
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to obtain access token"
            )
        
        # Get user profile from Google
        google_service = GoogleCalendarService(access_token, refresh_token or "")
        user_profile = await google_service.get_user_profile()
        
        # Extract user information
        email = user_profile.get("email")
        display_name = user_profile.get("name")
        google_user_id = user_profile.get("id")
        
        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        # Create or update user
        if not user:
            user = User(
                email=email,
                display_name=display_name,
                teams_user_id=google_user_id,
                access_token=auth_service.encrypt_token(access_token),
                refresh_token=auth_service.encrypt_token(refresh_token) if refresh_token else None,
                token_expires_at=auth_service.get_token_expiry(expires_in),
                last_login=datetime.utcnow()
            )
            db.add(user)
        else:
            user.access_token = auth_service.encrypt_token(access_token)
            user.refresh_token = auth_service.encrypt_token(refresh_token) if refresh_token else None
            user.token_expires_at = auth_service.get_token_expiry(expires_in)
            user.last_login = datetime.utcnow()
            user.display_name = display_name
        
        await db.commit()
        await db.refresh(user)
        
        # Create internal JWT tokens
        jwt_access_token = auth_service.create_jwt_token(
            str(user.user_id),
            user.email,
            "access"
        )
        jwt_refresh_token = auth_service.create_jwt_token(
            str(user.user_id),
            user.email,
            "refresh"
        )
        
        return {
            "user": UserResponse.model_validate(user),
            "tokens": TokenData(
                access_token=jwt_access_token,
                refresh_token=jwt_refresh_token,
                expires_at=user.token_expires_at,
                token_type="bearer"
            ),
            "message": "Authentication successful"
        }
        
    except Exception as e:
        logger.error(f"Error in auth callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    Args:
        refresh_token: JWT refresh token
        db: Database session
    
    Returns:
        New access token
    """
    try:
        # Verify JWT refresh token
        payload = auth_service.verify_jwt_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        
        # Get user from database
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if Microsoft token needs refresh
        if auth_service.is_token_expired(user.token_expires_at):
            # Refresh Microsoft token
            token_result = await auth_service.refresh_access_token(user.refresh_token)
            
            access_token = token_result.get("access_token")
            new_refresh_token = token_result.get("refresh_token")
            expires_in = token_result.get("expires_in", 3600)
            
            # Update user tokens
            user.access_token = auth_service.encrypt_token(access_token)
            if new_refresh_token:
                user.refresh_token = auth_service.encrypt_token(new_refresh_token)
            user.token_expires_at = auth_service.get_token_expiry(expires_in)
            
            await db.commit()
        
        # Create new JWT access token
        new_access_token = auth_service.create_jwt_token(
            str(user.user_id),
            user.email,
            "access"
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_at": user.token_expires_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )


@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (clear tokens)
    
    Args:
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Success message
    """
    try:
        # Clear user tokens
        current_user.access_token = None
        current_user.refresh_token = None
        current_user.token_expires_at = None
        
        await db.commit()
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user
    
    Args:
        token: JWT access token
        db: Database session
    
    Returns:
        Current user
    
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Verify JWT token
        payload = auth_service.verify_jwt_token(token)
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        
        # Get user from database
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


# Made with Bob
