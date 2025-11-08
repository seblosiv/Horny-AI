"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ==================== Auth Schemas ====================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== API Key Schemas ====================

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    revoked: bool

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    api_key: APIKeyResponse
    secret_key: str  # Full key, shown only once


# ==================== Wallet Schemas ====================

class WalletResponse(BaseModel):
    user_id: UUID
    balance_cents: int
    total_deposited_cents: int
    total_spent_cents: int
    updated_at: datetime

    class Config:
        from_attributes = True


class TopUpRequest(BaseModel):
    amount_usd: float = Field(..., gt=0, le=10000)
    currency: str = Field(default="usd")


class TopUpResponse(BaseModel):
    payment_id: UUID
    amount_cents: int
    payment_url: Optional[str] = None
    status: str


# ==================== Bot Schemas ====================

class BotCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    model_id: str = Field(..., regex="^(core-13b|core-34b|flagship-70b)$")
    system_prompt: str = Field(..., min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    allow_customer_system_messages: bool = False
    safety_level: str = Field(default="none", regex="^(none|loose|medium)$")


class BotUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=8192)
    allow_customer_system_messages: Optional[bool] = None
    safety_level: Optional[str] = Field(None, regex="^(none|loose|medium)$")
    is_active: Optional[bool] = None


class BotResponse(BaseModel):
    id: UUID
    name: str
    model_id: str
    system_prompt: str
    temperature: float
    max_tokens: int
    allow_customer_system_messages: bool
    safety_level: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Channel Schemas ====================

class ChannelCreate(BaseModel):
    bot_id: UUID
    kind: str = Field(..., regex="^(web|telegram|whatsapp)$")
    config: Dict[str, Any]


class ChannelResponse(BaseModel):
    id: UUID
    bot_id: UUID
    kind: str
    config: Dict[str, Any]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Chat Schemas ====================

class ChatMessage(BaseModel):
    role: str = Field(..., regex="^(user|assistant|system)$")
    content: str


class ChatCompletionRequest(BaseModel):
    bot_id: UUID
    messages: List[ChatMessage] = Field(..., min_items=1)
    stream: bool = True
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=8192)
    channel_session_id: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


# ==================== Usage Schemas ====================

class UsageStats(BaseModel):
    total_tokens: int
    total_cost_cents: int
    requests_count: int
    period_start: datetime
    period_end: datetime


class UsageLedgerEntry(BaseModel):
    id: UUID
    model_id: str
    tokens_in: int
    tokens_out: int
    cost_cents: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Payment Schemas ====================

class PaymentResponse(BaseModel):
    id: UUID
    status: str
    amount_cents: int
    currency: str
    payment_url: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Webhook Schemas ====================

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[Dict[str, Any]] = None


class WhatsAppMessage(BaseModel):
    object: str
    entry: List[Dict[str, Any]]
