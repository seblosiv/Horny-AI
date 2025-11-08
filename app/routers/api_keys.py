"""
API Key management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import User, APIKey
from app.schemas import APIKeyCreate, APIKeyResponse, APIKeyCreateResponse
from app.auth import get_current_user_from_token, generate_api_key

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("", response_model=APIKeyCreateResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    # Generate key
    full_key, key_prefix, key_hash = generate_api_key()

    # Create database record
    api_key = APIKey(
        user_id=current_user.id,
        name=key_data.name,
        key_prefix=key_prefix,
        key_hash=key_hash
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return APIKeyCreateResponse(
        api_key=api_key,
        secret_key=full_key
    )


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """List all API keys for current user"""
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id
    ).order_by(APIKey.created_at.desc()).all()

    return api_keys


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Revoke an API key"""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    api_key.revoked = True
    db.commit()

    return {"success": True, "message": "API key revoked"}
