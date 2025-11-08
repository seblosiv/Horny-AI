"""
Configuration settings for B2B Chat API
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/b2b_chat"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenMeter
    OPENMETER_URL: str = "https://openmeter.cloud/api"
    OPENMETER_TOKEN: Optional[str] = None

    # DeepInfra
    DEEPINFRA_API_KEY: str = "NDnRfiSssrzknoL9X7Y5tOCzBCZ0bel2"
    DEEPINFRA_BASE_URL: str = "https://api.deepinfra.com/v1/openai"

    # NOWPayments
    NOWPAYMENTS_API_KEY: Optional[str] = None
    NOWPAYMENTS_IPN_SECRET: Optional[str] = None
    NOWPAYMENTS_SANDBOX: bool = True

    # Security
    JWT_SECRET: str = "change-me-in-production-use-secrets-token-urlsafe-32"
    API_KEY_PREFIX: str = "sk_live"

    # Billing & Pricing (cents)
    BILLING_PRICE_PER_MTOKEN_CENTS: int = 160  # $1.60 / 1M tokens
    INITIAL_TRIAL_CREDITS_CENTS: int = 30      # $0.30 free trial
    LOW_BALANCE_THRESHOLD_CENTS: int = 100     # $1.00 warning

    # Rate Limiting
    RATE_LIMIT_PER_MIN: int = 120
    RATE_LIMIT_BURST: int = 10

    # Model Settings
    MAX_CONTEXT_TOKENS: int = 8192
    MAX_NEW_TOKENS: int = 2048
    DEFAULT_TEMPERATURE: float = 0.7

    # Default Models & Pricing
    MODELS_CONFIG: dict = {
        "core-13b": {
            "id": "Gryphe/MythoMax-L2-13b",
            "price_per_mtoken_cents": 160,
            "max_tokens": 8192
        },
        "core-34b": {
            "id": "cognitivecomputations/dolphin-2.6-mixtral-8x7b",
            "price_per_mtoken_cents": 320,
            "max_tokens": 32768
        },
        "flagship-70b": {
            "id": "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "price_per_mtoken_cents": 600,
            "max_tokens": 8192
        }
    }

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8501"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
