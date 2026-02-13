"""OpenAI engine adapter using official OpenAI SDK."""

import asyncio
import time
import random
from typing import AsyncIterator, Dict, Any, TYPE_CHECKING, List, cast, Optional
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import openai  # type: ignore

try:
    from openai import AsyncOpenAI  # type: ignore
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None  # type: ignore

from .base import LLMEngine


class OpenAIEngine(LLMEngine):
    """OpenAI adapter using official SDK."""

    def __init__(self, *args, max_retries: int = 3, **kwargs):
        """Initialize OpenAI engine.

        Args:
            max_retries: Maximum numberof retry attempts for transient failures
            **kwargs: Additional parameters (seed, response_format, etc.)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK not installed. Install with: pip install openai>=1.0.0"
            )
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries

        # Validate API key
        if not self.api_key:
            raise ValueError("API key required for OpenAIEngine")
        if not self.api_key.startswith("sk-"):
            logger.warning(f"API key does not start with 'sk-', may be invalid")

        # Create client
        self.client = AsyncOpenAI(api_key=self.api_key)

        # Extract OpenAI-specific parameters
        self.seed = self.extra_params.pop("seed", None)
        self.response_format = self.extra_params.pop("response_format", None)

    async def _retry_with_backoff(self, coro, operation_name: str) -> Any:
        """Execute coroutine with exponential backoff retry.

        Args:
            coro: Coroutine to execute
            operation_name: Name of operation for logging

        Returns:
            Result of coroutine

        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return await coro
            except Exception as e:
                last_exception = e
                # Check if this is a transient error worth retrying
                is_transient = self._is_transient_error(e)

                if attempt < self.max_retries - 1 and is_transient:
                    base_wait = 2 ** attempt  # Exponential backoff: 2^n seconds
                    jitter = random.uniform(0.8, 1.2)  # 20% jitter
                    wait_time = base_wait * jitter
                    logger.warning(
                        f"{operation_name} failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception

    def _is_transient_error(self, error: Exception) -> bool:
        """Check if error is transient (worth retrying).

        Args:
            error: Exception to check

        Returns:
            True if error is transient
        """
        error_str = str(error).lower()
        # Common transient error patterns
        transient_patterns = [
            "timeout",
            "connection",
            "network",
            "rate limit",
            "429",
            "503",
            "502",
            "504",
            "temporarily unavailable",
            "overloaded",
        ]
        return any(pattern in error_str for pattern in transient_patterns)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate completion (non-streaming)."""
        if not OPENAI_AVAILABLE or self.client is None:
            raise RuntimeError("OpenAI SDK not available")

        async def _generate():
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Build request parameters
            request_params: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

            # Add optional parameters
            if self.seed is not None:
                request_params["seed"] = self.seed
            if self.response_format:
                request_params["response_format"] = {"type": self.response_format}

            # Add any remaining extra params
            request_params.update(self.extra_params)

            response = await self.client.chat.completions.create(**request_params)

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Response content is None")
            return cast(str, content)

        return await self._retry_with_backoff(_generate(), "OpenAI generation")

    def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:
        """Generate completion with streaming (no retry for streaming)."""
        return self._generate_stream_impl(system_prompt, user_prompt)

    async def _generate_stream_impl(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:
        """Internal streaming implementation."""
        if not OPENAI_AVAILABLE or self.client is None:
            raise RuntimeError("OpenAI SDK not available")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Build request parameters
        request_params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }

        # Add optional parameters
        if self.seed is not None:
            request_params["seed"] = self.seed
        if self.response_format:
            request_params["response_format"] = {"type": self.response_format}

        # Add any remaining extra params
        request_params.update(self.extra_params)

        try:
            stream = await self.client.chat.completions.create(**request_params)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except asyncio.CancelledError:
            logger.warning("Streaming cancelled by user")
            raise
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise

    async def generate_chat(
        self,
        messages: list[dict],
    ) -> str:
        """Generate completion from full messages list (multi-turn chat)."""
        if not OPENAI_AVAILABLE or self.client is None:
            raise RuntimeError("OpenAI SDK not available")

        async def _generate_chat():
            # Build request parameters
            request_params: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

            # Add optional parameters
            if self.seed is not None:
                request_params["seed"] = self.seed
            if self.response_format:
                request_params["response_format"] = {"type": self.response_format}

            # Add any remaining extra params
            request_params.update(self.extra_params)

            response = await self.client.chat.completions.create(**request_params)

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Response content is None")
            return cast(str, content)

        return await self._retry_with_backoff(_generate_chat(), "OpenAI chat generation")

    def generate_chat_stream(
        self,
        messages: list[dict],
    ) -> AsyncIterator[str]:
        """Generate completion from full messages list with streaming (no retry)."""
        return self._generate_chat_stream_impl(messages)

    async def _generate_chat_stream_impl(
        self,
        messages: list[dict],
    ) -> AsyncIterator[str]:
        """Internal streaming implementation for chat."""
        if not OPENAI_AVAILABLE or self.client is None:
            raise RuntimeError("OpenAI SDK not available")

        # Build request parameters
        request_params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }

        # Add optional parameters
        if self.seed is not None:
            request_params["seed"] = self.seed
        if self.response_format:
            request_params["response_format"] = {"type": self.response_format}

        # Add any remaining extra params
        request_params.update(self.extra_params)

        try:
            stream = await self.client.chat.completions.create(**request_params)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except asyncio.CancelledError:
            logger.warning("Chat streaming cancelled by user")
            raise
        except Exception as e:
            logger.error(f"OpenAI chat streaming error: {e}")
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status."""
        if not OPENAI_AVAILABLE or self.client is None:
            return {
                "success": False,
                "error": "OpenAI SDK not installed",
                "model": self.model,
            }

        try:
            start = time.time()
            messages = [{"role": "user", "content": "test"}]

            await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=5,
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

    @staticmethod
    def list_models() -> List[str]:
        """List available OpenAI models.

        Returns:
            List of model names
        """
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4-1106-preview",
            "gpt-4-0125-preview",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "o1-preview",
            "o1-mini",
        ]
