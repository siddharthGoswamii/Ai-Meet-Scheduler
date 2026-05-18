# backend/auth/oauth.py

from fastapi import APIRouter
from google_auth_oauthlib.flow import Flow
import os

router = APIRouter()

# Google OAuth config
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI         = "http://localhost:8000/auth/callback"

# Scopes — what permissions we need
SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/calendar",      # read/write calendar
    "https://www.googleapis.com/auth/calendar.events" # create events
]

@router.get("/auth/login")
def login():
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id":     GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri":  "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )
    return {"auth_url": auth_url}


@router.get("/auth/callback")
def callback(code: str, db=Depends(get_db)):
    flow = Flow.from_client_config(...)
    flow.redirect_uri = REDIRECT_URI
    flow.fetch_token(code=code)

    credentials = flow.credentials

    # Get user info
    from google.oauth2 import id_token
    user_info = id_token.verify_oauth2_token(
        credentials.id_token,
        requests.Request(),
        GOOGLE_CLIENT_ID
    )

    # Save user + tokens to DB
    user = save_user(db, user_info, credentials)

    # Generate JWT
    jwt_token = create_jwt_token(user.id)

    return {"token": jwt_token, "user": user_info}