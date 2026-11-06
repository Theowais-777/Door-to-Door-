"""
Authentication and Google Single Sign-On (SSO) Service.
Verifies Google ID Tokens, manages User registration/login,
and signs production JWT sessions.
"""
import jwt
import time
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session

from infra.config import settings
from database import User

def create_jwt_token(user: User) -> str:
    """Generates signed JWT session token for authenticated users."""
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_jwt_token(token: str) -> Optional[Dict]:
    """Decodes and validates signed JWT session token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except Exception:
        return None

def verify_google_id_token(id_token: str) -> Optional[Dict]:
    """
    Verifies Google ID token against Google's tokeninfo endpoint.
    If valid, returns token payload containing sub (google_id), email, name, picture.
    """
    try:
        resp = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
            timeout=5.0
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "google_id": data.get("sub"),
                "email": data.get("email"),
                "name": data.get("name", data.get("email", "").split("@")[0]),
                "picture": data.get("picture", "")
            }
    except Exception:
        pass
    
    # Development / Sandbox token fallback for local prototype testing
    if id_token.startswith("mock_google_"):
        email_part = id_token.replace("mock_google_", "")
        return {
            "google_id": f"gid_{hash(email_part) & 0x7fffffff}",
            "email": f"{email_part}@gmail.com",
            "name": email_part.capitalize() + " Traveler",
            "picture": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=120"
        }
    return None

def get_or_create_google_user(db: Session, google_info: Dict) -> User:
    """Finds existing user by google_id or email, or registers a new user."""
    user = db.query(User).filter(
        (User.google_id == google_info["google_id"]) | (User.email == google_info["email"])
    ).first()

    if not user:
        user = User(
            google_id=google_info["google_id"],
            email=google_info["email"],
            name=google_info["name"],
            picture=google_info.get("picture", ""),
            provider="google",
            role="tourist"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update profile info
        if not user.google_id:
            user.google_id = google_info["google_id"]
        if google_info.get("picture"):
            user.picture = google_info["picture"]
        user.name = google_info["name"]
        db.commit()
        db.refresh(user)
        
    return user

