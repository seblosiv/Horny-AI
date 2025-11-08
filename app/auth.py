"""
Authentication and API key management utilities
"""
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User, APIKey

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key(prefix: str = None) -> tuple[str, str, str]:
    """
    Generate a new API key
    Returns: (full_key, prefix, key_hash)
    """
    if prefix is None:
        prefix = settings.API_KEY_PREFIX

    random_part = secrets.token_urlsafe(32)
    full_key = f"{prefix}_{random_part}"

    # Create a showable prefix (first 16 chars)
    key_prefix = full_key[:20]

    # Hash the full key
    key_hash = hash_api_key(full_key)

    return full_key, key_prefix, key_hash


def hash_api_key(key: str) -> str:
    """Hash an API key using SHA-256"""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    """Verify an API key against its hash"""
    return hmac.compare_digest(
        hashlib.sha256(raw_key.encode()).hexdigest(),
        key_hash
    )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


async def get_current_user_from_token(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token (for console/dashboard)
    Header format: "Bearer <token>"
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise credentials_exception
    except ValueError:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_current_user_from_api_key(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> tuple[User, APIKey]:
    """
    Get current user from API key (for API endpoints)
    Header format: "Bearer <api_key>"
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        scheme, api_key = authorization.split()
        if scheme.lower() != "bearer":
            raise credentials_exception
    except ValueError:
        raise credentials_exception

    # Extract prefix to find potential matches
    if "_" not in api_key:
        raise credentials_exception

    key_prefix = api_key[:20]  # Match our prefix length

    # Find API keys with this prefix
    api_keys = db.query(APIKey).filter(
        APIKey.key_prefix == key_prefix,
        APIKey.revoked == False
    ).all()

    # Verify hash
    matched_key = None
    for key in api_keys:
        if verify_api_key(api_key, key.key_hash):
            matched_key = key
            break

    if matched_key is None:
        raise credentials_exception

    # Update last used
    matched_key.last_used_at = datetime.utcnow()
    db.commit()

    # Get user
    user = db.query(User).filter(User.id == matched_key.user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user, matched_key


def verify_nowpayments_signature(payload: dict, signature: str, ipn_secret: str) -> bool:
    """Verify NOWPayments IPN signature"""
    import json

    # Sort payload keys for consistent hashing
    sorted_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))

    # Calculate HMAC
    calculated_sig = hmac.new(
        ipn_secret.encode(),
        sorted_payload.encode(),
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(calculated_sig, signature)
