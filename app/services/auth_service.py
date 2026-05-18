"""
Authentication service for Google OAuth 2.0
"""
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging
import os

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
except ImportError as e:
    raise ImportError(
        "Google authentication libraries not found. "
        "Please install: pip install google-auth google-auth-oauthlib google-auth-httplib2"
    ) from e

from jose import jwt, JWTError
from cryptography.fernet import Fernet

from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling Google authentication and token management"""
    
    def __init__(self):
        """Initialize authentication service"""
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.scopes = settings.google_scopes_list
        
        # Initialize encryption for storing tokens
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        
        # Create client config for OAuth flow
        self.client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Get Google OAuth authorization URL
        
        Args:
            state: Optional state parameter for CSRF protection
        
        Returns:
            Authorization URL string
        """
        try:
            # Create flow instance
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            # Generate authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',  # Request refresh token
                include_granted_scopes='true',
                state=state,
                prompt='consent'  # Force consent screen to get refresh token
            )
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise
    
    async def get_token_from_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from OAuth callback
        
        Returns:
            Dict containing token information
        """
        try:
            # Create flow instance
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            
            # Get credentials
            credentials = flow.credentials
            
            # Prepare result
            result = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'expires_in': 3600,  # Google tokens typically expire in 1 hour
                'token_type': 'Bearer',
                'scope': ' '.join(self.scopes)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting token from code: {str(e)}")
            raise
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token
        
        Returns:
            Dict containing new token information
        """
        try:
            # Decrypt refresh token
            decrypted_token = self.decrypt_token(refresh_token)
            
            # Create credentials with refresh token
            credentials = Credentials(
                token=None,
                refresh_token=decrypted_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes
            )
            
            # Refresh the token
            request = Request()
            credentials.refresh(request)
            
            # Prepare result
            result = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token or decrypted_token,
                'expires_in': 3600,
                'token_type': 'Bearer',
                'scope': ' '.join(self.scopes)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise
    
    def encrypt_token(self, token: str) -> str:
        """
        Encrypt token for secure storage
        
        Args:
            token: Token to encrypt
        
        Returns:
            Encrypted token string
        """
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt stored token
        
        Args:
            encrypted_token: Encrypted token
        
        Returns:
            Decrypted token string
        """
        return self.cipher.decrypt(encrypted_token.encode()).decode()
    
    def create_jwt_token(
        self,
        user_id: str,
        email: str,
        token_type: str = "access"
    ) -> str:
        """
        Create JWT token for internal authentication
        
        Args:
            user_id: User ID
            email: User email
            token_type: Type of token (access or refresh)
        
        Returns:
            JWT token string
        """
        if token_type == "access":
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": user_id,
            "email": email,
            "type": token_type,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return token
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
        
        Returns:
            Dict containing token payload
        
        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.error(f"JWT verification error: {str(e)}")
            raise
    
    def is_token_expired(self, expires_at: datetime) -> bool:
        """
        Check if token is expired
        
        Args:
            expires_at: Token expiration datetime
        
        Returns:
            True if expired, False otherwise
        """
        return datetime.utcnow() >= expires_at
    
    def get_token_expiry(self, expires_in: int) -> datetime:
        """
        Calculate token expiry datetime
        
        Args:
            expires_in: Seconds until expiry
        
        Returns:
            Expiry datetime
        """
        return datetime.utcnow() + timedelta(seconds=expires_in)


# Global auth service instance
auth_service = AuthService()

# Made with Bob
