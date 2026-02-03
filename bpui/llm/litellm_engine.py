"""LiteLLM engine adapter."""

import time
from typing import AsyncIterator, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    import litellm  # type: ignore

try:
    import litellm  # type: ignore
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    litellm = None  # type: ignore

from .base import LLMEngine


class LiteLLMEngine(LLMEngine):
    """LiteLLM adapter for multiple providers."""

    def __init__(self, *args, **kwargs):
        """Initialize LiteLLM engine."""
        if not LITELLM_AVAILABLE:
            raise ImportError(
                "LiteLLM not installed. Install with: pip install litellm"
            )
        super().__init__(*args, **kwargs)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate completion (non-streaming)."""
        if not LITELLM_AVAILABLE or litellm is None:
            raise RuntimeError("LiteLLM not available")
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await litellm.acompletion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key,
            stream=False,
            **self.extra_params
        )

        return response.choices[0].message.content

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
        if not LITELLM_AVAILABLE or litellm is None:
            raise RuntimeError("LiteLLM not available")
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await litellm.acompletion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key,
            stream=True,
            **self.extra_params
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_chat(
        self,
        messages: list[dict],
    ) -> str:
        """Generate completion from full messages list (multi-turn chat)."""
        if not LITELLM_AVAILABLE or litellm is None:
            raise RuntimeError("LiteLLM not available")

        response = await litellm.acompletion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key,
            stream=False,
            **self.extra_params
        )

        return response.choices[0].message.content

    def generate_chat_stream(
        self,
        messages: list[dict],
    ) -> AsyncIterator[str]:
        """Generate completion from full messages list with streaming."""
        return self._generate_chat_stream_impl(messages)

    async def _generate_chat_stream_impl(
        self,
        messages: list[dict],
    ) -> AsyncIterator[str]:
        """Internal streaming implementation for chat."""
        if not LITELLM_AVAILABLE or litellm is None:
            raise RuntimeError("LiteLLM not available")

        response = await litellm.acompletion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key,
            stream=True,
            **self.extra_params
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status."""
        if not LITELLM_AVAILABLE or litellm is None:
            return {
                "success": False,
                "error": "LiteLLM not installed",
                "model": self.model,
            }
            
        try:
            start = time.time()
            messages = [{"role": "user", "content": "test"}]

            await litellm.acompletion(
                model=self.model,
                messages=messages,
                max_tokens=5,
                api_key=self.api_key,
                **self.extra_params
            )

            latency = time.time() - start
            return {
                "success": True,
                "latency_ms": int(latency * 1000),
                "model": self.model,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": self.model,
            }
