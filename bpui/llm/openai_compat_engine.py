"""OpenAI-compatible REST API engine adapter."""

import time
import json
from typing import AsyncIterator, Dict, Any

import httpx

from .base import LLMEngine


class OpenAICompatEngine(LLMEngine):
    """OpenAI-compatible REST API adapter."""

    def __init__(self, *args, base_url: str = "", **kwargs):
        """Initialize OpenAI-compatible engine."""
        super().__init__(*args, **kwargs)
        self.base_url = base_url.rstrip("/")
        if not self.base_url:
            raise ValueError("base_url is required for OpenAI-compatible engine")

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate completion (non-streaming)."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:
        """Generate completion with streaming."""
        return self._generate_stream_impl(system_prompt, user_prompt)

    async def _generate_stream_impl(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:
        """Internal streaming implementation."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status."""
        try:
            start = time.time()
            messages = [{"role": "user", "content": "test"}]

            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 5,
                "stream": False,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

            latency = time.time() - start
            return {
                "success": True,
                "latency_ms": int(latency * 1000),
                "model": self.model,
                "base_url": self.base_url,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": self.model,
                "base_url": self.base_url,
            }
