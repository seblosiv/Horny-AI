"""
Chat API routes - OpenAI-compatible streaming endpoint
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import time
import logging
from datetime import datetime
from uuid import UUID

from app.database import get_db
from app.models import User, APIKey, Bot, Wallet, Chat, Message, UsageLedger
from app.schemas import ChatCompletionRequest
from app.auth import get_current_user_from_api_key
from app.deepinfra import deepinfra_client
from app.usage_tracker import token_counter, usage_calculator, openmeter_client
from app.rate_limiter import rate_limiter
from app.config import settings

router = APIRouter(prefix="/v1/chat", tags=["Chat API"])
logger = logging.getLogger(__name__)


async def check_wallet_balance(user: User, estimated_cost_cents: int, db: Session):
    """Check if user has sufficient balance"""
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Wallet not found. Please contact support."
        )

    if wallet.balance_cents < estimated_cost_cents:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "Insufficient balance",
                "balance_cents": wallet.balance_cents,
                "required_cents": estimated_cost_cents,
                "message": "Please top up your wallet to continue"
            }
        )

    return wallet


async def debit_wallet_and_record_usage(
    user: User,
    api_key: APIKey,
    bot: Bot,
    model_id: str,
    tokens_in: int,
    tokens_out: int,
    cost_cents: int,
    db: Session
):
    """Debit wallet and record usage in ledger"""
    # Update wallet
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    wallet.balance_cents -= cost_cents
    wallet.total_spent_cents += cost_cents

    # Record in usage ledger
    usage_entry = UsageLedger(
        user_id=user.id,
        api_key_id=api_key.id,
        bot_id=bot.id,
        model_id=model_id,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_cents=cost_cents
    )
    db.add(usage_entry)
    db.commit()

    # Send to OpenMeter (async, non-blocking)
    try:
        await openmeter_client.ingest_event(
            tenant_id=user.id,
            api_key_id=api_key.id,
            bot_id=bot.id,
            model_id=model_id,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_cents=cost_cents
        )
    except Exception as e:
        logger.error(f"Failed to send OpenMeter event: {e}")


@router.post("/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    auth_data: tuple = Depends(get_current_user_from_api_key),
    db: Session = Depends(get_db)
):
    """
    OpenAI-compatible chat completions endpoint
    Supports streaming (SSE) and non-streaming responses
    """
    user, api_key = auth_data

    # Rate limiting
    rate_limit_key = f"api_key:{api_key.id}"
    allowed, current, limit = await rate_limiter.check_rate_limit(rate_limit_key)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {limit} requests per minute",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + 60)
            }
        )

    # Get bot
    bot = db.query(Bot).filter(
        Bot.id == request.bot_id,
        Bot.user_id == user.id,
        Bot.is_active == True
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found or inactive"
        )

    # Build messages with system prompt
    messages = [
        {"role": "system", "content": bot.system_prompt}
    ]

    # Handle customer system messages
    for msg in request.messages:
        if msg.role == "system" and not bot.allow_customer_system_messages:
            continue  # Skip customer system messages if not allowed
        messages.append({"role": msg.role, "content": msg.content})

    # Calculate input tokens
    input_tokens = token_counter.count_messages_tokens(messages, bot.model_id)

    # Estimate max cost for pre-authorization
    max_output_tokens = request.max_tokens or bot.max_tokens
    estimated_cost = usage_calculator.estimate_max_cost(
        bot.model_id,
        input_tokens,
        max_output_tokens
    )

    # Check wallet balance
    await check_wallet_balance(user, estimated_cost, db)

    # Get or create chat session
    chat = None
    if request.channel_session_id:
        chat = db.query(Chat).filter(
            Chat.external_thread_id == request.channel_session_id,
            Chat.bot_id == bot.id
        ).first()

    if not chat:
        chat = Chat(
            bot_id=bot.id,
            external_thread_id=request.channel_session_id
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)

    # Temperature override
    temperature = request.temperature if request.temperature is not None else bot.temperature

    # Stream or non-stream response
    if request.stream:
        return await handle_streaming_response(
            user, api_key, bot, chat, messages, temperature, max_output_tokens, db
        )
    else:
        return await handle_non_streaming_response(
            user, api_key, bot, chat, messages, temperature, max_output_tokens, db
        )


async def handle_streaming_response(
    user, api_key, bot, chat, messages, temperature, max_tokens, db
):
    """Handle streaming SSE response"""

    async def event_generator():
        collected_content = []
        request_id = f"chatcmpl-{int(time.time())}"

        try:
            async for chunk in deepinfra_client.create_completion_stream(
                model_id=bot.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                # Parse and collect content
                if chunk.startswith("data: "):
                    data_str = chunk[6:].strip()

                    if data_str == "[DONE]":
                        yield chunk
                        break

                    try:
                        data = json.loads(data_str)
                        # Collect content from delta
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                collected_content.append(delta["content"])

                        yield chunk
                    except json.JSONDecodeError:
                        pass

            # After streaming completes, calculate actual usage
            full_content = "".join(collected_content)
            output_tokens = token_counter.count_tokens(full_content, bot.model_id)
            input_tokens = token_counter.count_messages_tokens(messages, bot.model_id)

            # Calculate actual cost
            actual_cost = usage_calculator.calculate_cost(
                bot.model_id,
                input_tokens,
                output_tokens
            )

            # Debit wallet and record usage
            await debit_wallet_and_record_usage(
                user, api_key, bot, bot.model_id,
                input_tokens, output_tokens, actual_cost, db
            )

            # Save messages
            user_message = Message(
                chat_id=chat.id,
                role="user",
                content=messages[-1]["content"],  # Last user message
                tokens_in=input_tokens,
                model_id=bot.model_id
            )
            assistant_message = Message(
                chat_id=chat.id,
                role="assistant",
                content=full_content,
                tokens_out=output_tokens,
                model_id=bot.model_id,
                cost_cents=actual_cost
            )
            db.add(user_message)
            db.add(assistant_message)

            # Update chat timestamp
            chat.last_message_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_chunk = {
                "error": {
                    "message": str(e),
                    "type": "server_error"
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


async def handle_non_streaming_response(
    user, api_key, bot, chat, messages, temperature, max_tokens, db
):
    """Handle non-streaming JSON response"""
    try:
        response = await deepinfra_client.create_completion(
            model_id=bot.model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Extract usage from provider response
        usage = response.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        # Fallback to our counter if provider doesn't return usage
        if input_tokens == 0:
            input_tokens = token_counter.count_messages_tokens(messages, bot.model_id)
        if output_tokens == 0:
            content = response["choices"][0]["message"]["content"]
            output_tokens = token_counter.count_tokens(content, bot.model_id)

        # Calculate cost
        actual_cost = usage_calculator.calculate_cost(
            bot.model_id,
            input_tokens,
            output_tokens
        )

        # Debit wallet and record usage
        await debit_wallet_and_record_usage(
            user, api_key, bot, bot.model_id,
            input_tokens, output_tokens, actual_cost, db
        )

        # Save messages
        content = response["choices"][0]["message"]["content"]
        user_message = Message(
            chat_id=chat.id,
            role="user",
            content=messages[-1]["content"],
            tokens_in=input_tokens,
            model_id=bot.model_id
        )
        assistant_message = Message(
            chat_id=chat.id,
            role="assistant",
            content=content,
            tokens_out=output_tokens,
            model_id=bot.model_id,
            cost_cents=actual_cost
        )
        db.add(user_message)
        db.add(assistant_message)

        chat.last_message_at = datetime.utcnow()
        db.commit()

        return response

    except Exception as e:
        logger.error(f"Non-streaming error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
