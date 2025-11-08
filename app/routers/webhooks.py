"""
Webhook handlers for NOWPayments, Telegram, and WhatsApp
"""
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
import httpx
import hmac
import hashlib
import json
import logging
from datetime import datetime

from app.database import get_db
from app.models import Payment, Wallet, AuditLog, Channel, Bot, Chat, Message
from app.auth import verify_nowpayments_signature
from app.config import settings

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)


@router.post("/nowpayments")
async def nowpayments_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle NOWPayments IPN webhook"""
    try:
        body = await request.json()
        signature = request.headers.get("x-nowpayments-sig", "")

        # Verify signature if IPN secret is configured
        if settings.NOWPAYMENTS_IPN_SECRET:
            if not verify_nowpayments_signature(body, signature, settings.NOWPAYMENTS_IPN_SECRET):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid signature"
                )

        payment_status = body.get("payment_status")
        order_id = body.get("order_id")

        if not order_id:
            logger.warning(f"NOWPayments webhook missing order_id: {body}")
            return {"status": "ignored"}

        # Find payment
        payment = db.query(Payment).filter(Payment.id == order_id).first()

        if not payment:
            logger.warning(f"Payment not found for order_id: {order_id}")
            return {"status": "ignored"}

        # Update payment record
        payment.raw_data = body

        if payment_status == "finished":
            # Payment confirmed - credit wallet
            if payment.status != "confirmed":  # Idempotent check
                payment.status = "confirmed"
                payment.confirmed_at = datetime.utcnow()

                # Credit wallet
                wallet = db.query(Wallet).filter(Wallet.user_id == payment.user_id).first()
                if wallet:
                    wallet.balance_cents += payment.amount_cents
                    wallet.total_deposited_cents += payment.amount_cents

                    # Create audit log
                    audit = AuditLog(
                        user_id=payment.user_id,
                        action="wallet.credit",
                        entity_type="payment",
                        entity_id=payment.id,
                        metadata={
                            "amount_cents": payment.amount_cents,
                            "provider": "NOWPAYMENTS",
                            "payment_id": body.get("payment_id")
                        }
                    )
                    db.add(audit)

                db.commit()
                logger.info(f"Payment {order_id} confirmed, wallet credited")

        elif payment_status in ["failed", "expired"]:
            payment.status = payment_status
            db.commit()
            logger.info(f"Payment {order_id} {payment_status}")

        else:
            # Other statuses (waiting, sending, etc.)
            payment.status = payment_status
            db.commit()

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"NOWPayments webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/telegram/{channel_id}")
async def telegram_webhook(channel_id: str, request: Request, db: Session = Depends(get_db)):
    """Handle Telegram bot webhook"""
    try:
        update = await request.json()
        logger.info(f"Telegram update: {update}")

        # Get message
        message = update.get("message")
        if not message:
            return {"ok": True}

        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")
        from_user = message.get("from", {})

        if not chat_id or not text:
            return {"ok": True}

        # Find channel
        channel = db.query(Channel).filter(
            Channel.id == channel_id,
            Channel.kind == "telegram",
            Channel.is_active == True
        ).first()

        if not channel:
            logger.warning(f"Telegram channel {channel_id} not found")
            return {"ok": True}

        # Get bot
        bot = db.query(Bot).filter(Bot.id == channel.bot_id).first()
        if not bot or not bot.is_active:
            return {"ok": True}

        # Get or create chat session
        external_thread_id = f"tg_{chat_id}"
        chat = db.query(Chat).filter(
            Chat.bot_id == bot.id,
            Chat.external_thread_id == external_thread_id
        ).first()

        if not chat:
            chat = Chat(
                bot_id=bot.id,
                channel_id=channel.id,
                external_thread_id=external_thread_id,
                metadata={"platform": "telegram", "chat_id": chat_id}
            )
            db.add(chat)
            db.commit()
            db.refresh(chat)

        # Build messages for AI (get recent history)
        recent_messages = db.query(Message).filter(
            Message.chat_id == chat.id
        ).order_by(Message.created_at.desc()).limit(10).all()

        messages = [{"role": "system", "content": bot.system_prompt}]
        for msg in reversed(recent_messages):
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": text})

        # Call DeepInfra (non-streaming for Telegram)
        from app.deepinfra import deepinfra_client
        from app.usage_tracker import token_counter, usage_calculator

        response = await deepinfra_client.create_completion(
            model_id=bot.model_id,
            messages=messages,
            temperature=bot.temperature,
            max_tokens=bot.max_tokens
        )

        assistant_content = response["choices"][0]["message"]["content"]

        # Save messages
        user_msg = Message(
            chat_id=chat.id,
            role="user",
            content=text,
            tokens_in=token_counter.count_tokens(text, bot.model_id),
            model_id=bot.model_id
        )
        assistant_msg = Message(
            chat_id=chat.id,
            role="assistant",
            content=assistant_content,
            tokens_out=token_counter.count_tokens(assistant_content, bot.model_id),
            model_id=bot.model_id
        )
        db.add(user_msg)
        db.add(assistant_msg)
        chat.last_message_at = datetime.utcnow()
        db.commit()

        # Send reply via Telegram Bot API
        bot_token = channel.config.get("bot_token")
        if bot_token:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": assistant_content,
                        "parse_mode": "Markdown"
                    },
                    timeout=10.0
                )

        return {"ok": True}

    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"ok": True}  # Return ok to Telegram to avoid retries


@router.get("/telegram/{channel_id}")
async def telegram_webhook_verify(channel_id: str):
    """Telegram webhook verification (for testing)"""
    return {"status": "ok", "channel_id": channel_id}


@router.post("/whatsapp/{channel_id}")
async def whatsapp_webhook(channel_id: str, request: Request, db: Session = Depends(get_db)):
    """Handle WhatsApp Cloud API webhook"""
    try:
        body = await request.json()
        logger.info(f"WhatsApp webhook: {body}")

        # Extract message
        entry = body.get("entry", [])
        if not entry:
            return {"status": "ok"}

        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "ok"}

        value = changes[0].get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ok"}

        message = messages[0]
        from_number = message.get("from")
        message_type = message.get("type")
        text = message.get("text", {}).get("body", "")

        if message_type != "text" or not text:
            return {"status": "ok"}

        # Find channel
        channel = db.query(Channel).filter(
            Channel.id == channel_id,
            Channel.kind == "whatsapp",
            Channel.is_active == True
        ).first()

        if not channel:
            logger.warning(f"WhatsApp channel {channel_id} not found")
            return {"status": "ok"}

        # Get bot
        bot = db.query(Bot).filter(Bot.id == channel.bot_id).first()
        if not bot or not bot.is_active:
            return {"status": "ok"}

        # Similar flow as Telegram...
        # (Implementation follows same pattern)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return {"status": "ok"}


@router.get("/whatsapp/{channel_id}")
async def whatsapp_webhook_verify(channel_id: str, request: Request):
    """WhatsApp webhook verification"""
    # WhatsApp Cloud API verification
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # You should set a verify token in channel config
    if mode == "subscribe" and token:
        return int(challenge) if challenge else 200

    return {"status": "error"}
