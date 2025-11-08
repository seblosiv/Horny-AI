"""
Bot management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import User, Bot
from app.schemas import BotCreate, BotUpdate, BotResponse
from app.auth import get_current_user_from_token

router = APIRouter(prefix="/bots", tags=["Bots"])


@router.post("", response_model=BotResponse)
async def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new bot"""
    bot = Bot(
        user_id=current_user.id,
        name=bot_data.name,
        model_id=bot_data.model_id,
        system_prompt=bot_data.system_prompt,
        temperature=bot_data.temperature,
        max_tokens=bot_data.max_tokens,
        allow_customer_system_messages=bot_data.allow_customer_system_messages,
        safety_level=bot_data.safety_level
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)

    return bot


@router.get("", response_model=List[BotResponse])
async def list_bots(
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """List all bots for current user"""
    bots = db.query(Bot).filter(
        Bot.user_id == current_user.id
    ).order_by(Bot.created_at.desc()).all()

    return bots


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get a specific bot"""
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    return bot


@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: UUID,
    bot_data: BotUpdate,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update a bot"""
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    # Update fields
    update_data = bot_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bot, field, value)

    db.commit()
    db.refresh(bot)

    return bot


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a bot"""
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )

    db.delete(bot)
    db.commit()

    return {"success": True, "message": "Bot deleted"}
