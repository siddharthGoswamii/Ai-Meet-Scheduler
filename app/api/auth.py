"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import cast, Any
import logging

from app.db.database import get_db
from app.models import User
from app.schemas import UserResponse, TokenData
from app.services import auth_service
from app.services.google_calendar_service import GoogleCalendarService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.get("/login")
async def login(request: Request):
    """
    Initiate Google OAuth login flow with state verification persistence
    """
    try:
        # 1. Unpack url, state, and code_verifier from the service
        auth_url, state, code_verifier = auth_service.get_authorization_url()
        
        # 2. Persist both state and code_verifier in the signed session cookie
        request.session["oauth_state"] = state
        request.session["code_verifier"] = code_verifier
        
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
    request: Request,
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State parameter returned from Google"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle OAuth callback from Google and redirect back to the React Frontend
    """
    try:
        # 1. Pull the original state and code_verifier out of the signed session cookie
        saved_state = request.session.get("oauth_state")
        code_verifier = request.session.get("code_verifier")
        
        # 2. Verify state presence and guard against CSRF issues
        if not saved_state or saved_state != state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authentication failed: State mismatch or session expired."
            )
        
        # 3. Verify code_verifier presence (required for PKCE flow)
        if not code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authentication failed: Code verifier missing from session."
            )
        
        # 3. Consume and clear both values immediately from session storage
        request.session.pop("oauth_state", None)
        request.session.pop("code_verifier", None)

        # 4. Supply code, state, AND code_verifier to exchange tokens safely
        token_result = await auth_service.get_token_from_code(code, state=saved_state, code_verifier=code_verifier)
        
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
        
        # 5. Create or update user
        if not user:
            user = User(
                email=email,
                display_name=display_name,
                teams_user_id=google_user_id,
                access_token=cast(Any, auth_service.encrypt_token(access_token)),
                refresh_token=cast(Any, auth_service.encrypt_token(refresh_token) if refresh_token else None),
                token_expires_at=cast(Any, auth_service.get_token_expiry(expires_in)),
                last_login=cast(Any, datetime.utcnow())
            )
            db.add(user)
        else:
            user.access_token = cast(Any, auth_service.encrypt_token(access_token))
            user.refresh_token = cast(Any, auth_service.encrypt_token(refresh_token) if refresh_token else None)
            user.token_expires_at = cast(Any, auth_service.get_token_expiry(expires_in))
            user.last_login = cast(Any, datetime.utcnow())
            user.display_name = cast(Any, display_name)
        
        await db.commit()
        await db.refresh(user)
        
        # Create internal JWT tokens
        jwt_access_token = auth_service.create_jwt_token(
            str(user.user_id),
            str(user.email),
            "access"
        )
        jwt_refresh_token = auth_service.create_jwt_token(
            str(user.user_id),
            str(user.email),
            "refresh"
        )

        # Redirect to React dashboard with token
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/dashboard?token={jwt_access_token}&refresh={jwt_refresh_token}"
        )
        
    except HTTPException:
        raise
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
        
        # Check if Google token needs refresh
        if user.token_expires_at and auth_service.is_token_expired(user.token_expires_at):
            # Refresh Google token
            if not user.refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No refresh token available"
                )
            
            token_result = await auth_service.refresh_access_token(user.refresh_token)
            
            access_token = token_result.get("access_token")
            new_refresh_token = token_result.get("refresh_token")
            expires_in = token_result.get("expires_in", 3600)
            
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh access token"
                )
            
            # Update user tokens
            user.access_token = auth_service.encrypt_token(access_token)
            if new_refresh_token:
                user.refresh_token = auth_service.encrypt_token(new_refresh_token)
            user.token_expires_at = auth_service.get_token_expiry(expires_in)
            
            await db.commit()
        
        # Create new JWT access token
        new_access_token = auth_service.create_jwt_token(
            str(user.user_id),
            str(user.email),
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
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
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