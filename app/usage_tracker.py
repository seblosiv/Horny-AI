"""
Token counting and usage tracking with OpenMeter integration
"""
import httpx
import tiktoken
from typing import Optional
from uuid import UUID
import time
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class TokenCounter:
    """Count tokens for various models"""

    def __init__(self):
        # Default to GPT-3.5 encoding (cl100k_base) as a fallback
        # DeepInfra models often use similar tokenization
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to load tiktoken encoding: {e}")
            self.encoding = None

    def count_tokens(self, text: str, model_id: str = None) -> int:
        """Count tokens in text"""
        if self.encoding is None:
            # Fallback: rough estimate (1 token ≈ 4 chars)
            return len(text) // 4

        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.error(f"Token counting error: {e}")
            return len(text) // 4

    def count_messages_tokens(self, messages: list[dict], model_id: str = None) -> int:
        """Count tokens for a list of messages"""
        total = 0
        for msg in messages:
            # Count role and content
            total += self.count_tokens(msg.get("role", ""), model_id)
            total += self.count_tokens(msg.get("content", ""), model_id)
            # Add formatting tokens (rough estimate)
            total += 4

        # Add a few tokens for message formatting
        total += 3

        return total


class OpenMeterClient:
    """Client for OpenMeter API"""

    def __init__(self):
        self.base_url = settings.OPENMETER_URL
        self.token = settings.OPENMETER_TOKEN
        self.enabled = bool(self.token)

    async def ingest_event(
        self,
        tenant_id: UUID,
        api_key_id: Optional[UUID],
        bot_id: Optional[UUID],
        model_id: str,
        tokens_in: int,
        tokens_out: int,
        cost_cents: int,
        metadata: dict = None
    ):
        """Send usage event to OpenMeter"""
        if not self.enabled:
            logger.debug("OpenMeter disabled, skipping event ingestion")
            return

        event = {
            "specversion": "1.0",
            "type": "ai.usage",
            "source": "b2b-chat-api",
            "subject": str(api_key_id) if api_key_id else str(tenant_id),
            "id": f"{tenant_id}_{int(time.time() * 1000)}",
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "datacontenttype": "application/json",
            "data": {
                "tenant_id": str(tenant_id),
                "api_key_id": str(api_key_id) if api_key_id else None,
                "bot_id": str(bot_id) if bot_id else None,
                "model_id": model_id,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "total_tokens": tokens_in + tokens_out,
                "cost_cents": cost_cents,
                "timestamp_ms": int(time.time() * 1000),
                **(metadata or {})
            }
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/events",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    },
                    json=event
                )
                response.raise_for_status()
                logger.debug(f"OpenMeter event sent: {event['id']}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to send OpenMeter event: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending OpenMeter event: {e}")


class UsageCalculator:
    """Calculate usage costs"""

    def __init__(self):
        self.models_config = settings.MODELS_CONFIG

    def get_model_price(self, model_id: str) -> int:
        """Get price per million tokens in cents"""
        model_config = self.models_config.get(model_id)
        if model_config:
            return model_config["price_per_mtoken_cents"]
        # Default fallback
        return settings.BILLING_PRICE_PER_MTOKEN_CENTS

    def calculate_cost(self, model_id: str, tokens_in: int, tokens_out: int) -> int:
        """
        Calculate cost in cents for token usage
        Returns: cost in cents (integer)
        """
        total_tokens = tokens_in + tokens_out
        price_per_mtoken = self.get_model_price(model_id)

        # Calculate cost: (total_tokens / 1_000_000) * price_per_mtoken
        cost_cents = (total_tokens * price_per_mtoken) // 1_000_000

        # Ensure minimum charge of 1 cent for any usage
        return max(1, cost_cents)

    def estimate_max_cost(self, model_id: str, input_tokens: int, max_output_tokens: int) -> int:
        """Estimate maximum possible cost for pre-authorization"""
        return self.calculate_cost(model_id, input_tokens, max_output_tokens)


# Global instances
token_counter = TokenCounter()
openmeter_client = OpenMeterClient()
usage_calculator = UsageCalculator()
