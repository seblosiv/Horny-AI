"""
DeepInfra API client for chat completions
"""
import httpx
import json
import logging
from typing import AsyncGenerator, Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class DeepInfraClient:
    """Client for DeepInfra API"""

    def __init__(self):
        self.api_key = settings.DEEPINFRA_API_KEY
        self.base_url = settings.DEEPINFRA_BASE_URL
        self.models_config = settings.MODELS_CONFIG

    def get_provider_model_id(self, model_id: str) -> str:
        """Convert our model ID to DeepInfra model ID"""
        model_config = self.models_config.get(model_id)
        if model_config:
            return model_config["id"]
        # Fallback
        return model_id

    async def create_completion_stream(
        self,
        model_id: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion from DeepInfra
        Yields SSE-formatted data chunks
        """
        provider_model_id = self.get_provider_model_id(model_id)

        payload = {
            "model": provider_model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        # DeepInfra returns SSE format: "data: {...}"
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix

                            # Check for end signal
                            if data_str.strip() == "[DONE]":
                                yield "data: [DONE]\n\n"
                                break

                            try:
                                # Validate JSON
                                json.loads(data_str)
                                # Yield in SSE format
                                yield f"data: {data_str}\n\n"
                            except json.JSONDecodeError:
                                logger.warning(f"Invalid JSON in stream: {data_str}")
                                continue

        except httpx.HTTPError as e:
            logger.error(f"DeepInfra API error: {e}")
            error_data = {
                "error": {
                    "message": str(e),
                    "type": "api_error"
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            raise

    async def create_completion(
        self,
        model_id: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a non-streaming chat completion
        Returns the complete response
        """
        provider_model_id = self.get_provider_model_id(model_id)

        payload = {
            "model": provider_model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            **kwargs
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"DeepInfra API error: {e}")
            raise


# Global client instance
deepinfra_client = DeepInfraClient()
