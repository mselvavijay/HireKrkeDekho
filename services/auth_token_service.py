import os
import hmac
import hashlib
import time
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, Request

# Secret used to sign session tokens for verified users
JWT_SECRET = os.getenv("SESSION_SECRET", os.getenv("GROQ_API_KEY", "hirekrkedekho_secure_token_secret_2026"))

def create_access_token(user_id: str, email: str) -> str:
    """
    Create a tamper-proof signed session token (user_id:email:timestamp:signature).
    Does not require external JWT libraries.
    """
    ts = str(int(time.time()))
    payload = f"{user_id}:{email}:{ts}"
    sig = hmac.new(JWT_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"

def verify_access_token(token: str, max_age_days: int = 30) -> Optional[Dict[str, str]]:
    """
    Verify signature and expiry of the signed token.
    """
    if not token or ":" not in token:
        return None
    parts = token.split(":")
    if len(parts) != 4:
        return None
    user_id, email, ts_str, signature = parts
    try:
        ts = int(ts_str)
    except ValueError:
        return None

    # Check expiration (default 30 days)
    if time.time() - ts > max_age_days * 86400:
        return None

    payload = f"{user_id}:{email}:{ts_str}"
    expected_sig = hmac.new(JWT_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, signature):
        return None

    return {"user_id": user_id, "email": email}

def extract_token_from_request(authorization: Optional[str] = None, request: Optional[Request] = None) -> Optional[str]:
    """Helper to extract bearer token from header, cookies, or query parameters."""
    if authorization and authorization.startswith("Bearer "):
        return authorization.split("Bearer ", 1)[1].strip()
    if request:
        # Check Cookies (for direct browser navigation)
        cookie_val = request.cookies.get("hkd_token") or request.cookies.get("access_token")
        if cookie_val:
            return cookie_val.strip()
        # Check Query Parameters
        query_val = request.query_params.get("token") or request.query_params.get("auth_token")
        if query_val:
            return query_val.strip()
    return None

def get_current_user_from_header(
    authorization: Optional[str] = Header(None),
    request: Request = None
) -> Dict[str, str]:
    """
    FastAPI dependency to enforce authenticated user token.
    Accepts:
      Authorization: Bearer <signed_token>
      Cookie: hkd_token=<signed_token>
      Query: ?token=<signed_token>
    """
    token_str = extract_token_from_request(authorization, request)
    if not token_str:
        raise HTTPException(
            status_code=401,
            detail="Authentication token missing or invalid. Please sign in with Google."
        )
    user_data = verify_access_token(token_str)
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Session has expired or is invalid. Please sign in again."
        )
    return user_data

def get_optional_user_from_header(
    authorization: Optional[str] = Header(None),
    request: Request = None
) -> Optional[Dict[str, str]]:
    """
    FastAPI dependency to optionally resolve user token if present.
    Returns user dict if valid token provided; returns None if missing or expired.
    Never raises 401 HTTPException.
    """
    token_str = extract_token_from_request(authorization, request)
    if not token_str:
        return None
    return verify_access_token(token_str)

