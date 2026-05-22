"""
Authentication service for Google OAuth 2.0
"""

from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from jose.exceptions import JWTError

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

from jose import jwt
from cryptography.fernet import Fernet

from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:

    def __init__(self):

        # ENV VALUES
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

        print("FINAL REDIRECT URI:", self.redirect_uri)

        # :white_check_mark: FIXED SCOPES (PROPER LIST)
        self.scopes = [
            "openid",
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]

        # Encryption
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())

        # OAuth config
        self.client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }

    def get_authorization_url(self) -> tuple[str, str, str]:
        # Create flow with PKCE enabled
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        # Enable PKCE by setting code_verifier before generating auth URL
        # This will automatically generate a code_verifier and code_challenge
        import secrets
        import hashlib
        import base64
        
        # Generate a cryptographically secure random code verifier
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge from verifier
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        # Set the code verifier on the flow
        flow.code_verifier = code_verifier

        # Generate authorization URL with PKCE parameters
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='false',
            prompt='consent',
            code_challenge=code_challenge,
            code_challenge_method='S256'
        )

        logger.info(f"Generated auth URL with PKCE enabled")
        return auth_url, state, code_verifier

    async def get_token_from_code(self, code: str, state: str, code_verifier: str) -> Dict[str, Any]:
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
            state=state
        )

        flow.code_verifier = code_verifier  # <-- restore the verifier before fetching

        flow.fetch_token(code=code)
        credentials = flow.credentials

        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": " ".join(self.scopes)
        }

    def encrypt_token(self, token: str) -> str:
        return self.cipher.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        return self.cipher.decrypt(encrypted_token.encode()).decode()

    def get_token_expiry(self, expires_in: int) -> datetime:
        return datetime.utcnow() + timedelta(seconds=expires_in)

    # :closed_lock_with_key: VERIFY JWT TOKEN
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            raise Exception("Invalid or expired token")

    # :hourglass_flowing_sand: CHECK IF TOKEN EXPIRED
    def is_token_expired(self, expiry_time: datetime) -> bool:
        return datetime.utcnow() >= expiry_time

    # REFRESH TOKEN
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:

        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes
        )

        credentials.refresh(Request())

        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": " ".join(self.scopes)
        }

    # JWT
    def create_jwt_token(self, user_id: str, email: str, token_type: str = "access") -> str:

        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            if token_type == "access"
            else settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
        )

        payload = {
            "sub": user_id,
            "email": email,
            "type": token_type,
            "exp": expire
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# GLOBAL INSTANCE
auth_service = AuthService()