"""
SQLAlchemy database models
"""
from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, Float, Text,
    ForeignKey, DateTime, JSON, func, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)  # nullable for magic link auth
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    bots = relationship("Bot", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    usage_ledger = relationship("UsageLedger", back_populates="user", cascade="all, delete-orphan")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    key_prefix = Column(String, nullable=False, index=True)  # e.g., "sk_live_abc"
    key_hash = Column(String, nullable=False)  # SHA-256 hash
    revoked = Column(Boolean, default=False)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="api_keys")
    usage_ledger = relationship("UsageLedger", back_populates="api_key")

    __table_args__ = (
        Index('idx_api_keys_prefix_active', 'key_prefix', 'revoked'),
    )


class Wallet(Base):
    __tablename__ = "wallets"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    balance_cents = Column(BigInteger, nullable=False, default=0)
    total_deposited_cents = Column(BigInteger, default=0)
    total_spent_cents = Column(BigInteger, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="wallet")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # "NOWPAYMENTS"
    status = Column(String, nullable=False)  # pending/confirmed/failed/expired
    amount_cents = Column(BigInteger, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    provider_invoice_id = Column(String, unique=True, index=True)
    payment_url = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)  # Store full provider response
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="payments")


class Bot(Base):
    __tablename__ = "bots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    model_id = Column(String, nullable=False)  # e.g., "core-13b"
    system_prompt = Column(Text, nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    allow_customer_system_messages = Column(Boolean, default=False)
    safety_level = Column(String, default="none")  # none/loose/medium
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="bots")
    channels = relationship("Channel", back_populates="bot", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="bot", cascade="all, delete-orphan")


class Channel(Base):
    __tablename__ = "channels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False)
    kind = Column(String, nullable=False)  # "web", "telegram", "whatsapp"
    config = Column(JSON, nullable=False)  # channel-specific config
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bot = relationship("Bot", back_populates="channels")
    chats = relationship("Chat", back_populates="channel")


class Chat(Base):
    __tablename__ = "chats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=False)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("channels.id"), nullable=True)
    external_thread_id = Column(String, nullable=True, index=True)  # telegram/wa thread or web session
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bot = relationship("Bot", back_populates="chats")
    channel = relationship("Channel", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_chats_external_thread', 'external_thread_id', 'channel_id'),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    role = Column(String, nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    model_id = Column(String, nullable=True)
    cost_cents = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chat = relationship("Chat", back_populates="messages")

    __table_args__ = (
        Index('idx_messages_chat_created', 'chat_id', 'created_at'),
    )


class UsageLedger(Base):
    __tablename__ = "usage_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=True)
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"), nullable=True)
    model_id = Column(String, nullable=False)
    tokens_in = Column(Integer, nullable=False)
    tokens_out = Column(Integer, nullable=False)
    cost_cents = Column(Integer, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="usage_ledger")
    api_key = relationship("APIKey", back_populates="usage_ledger")

    __table_args__ = (
        Index('idx_usage_user_created', 'user_id', 'created_at'),
        Index('idx_usage_api_key_created', 'api_key_id', 'created_at'),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # "wallet.credit", "api_key.create", etc.
    entity_type = Column(String, nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    metadata = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_action_created', 'action', 'created_at'),
    )
