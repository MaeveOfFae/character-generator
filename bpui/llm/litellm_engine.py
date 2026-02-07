"""LiteLLM engine adapter."""

import asyncio
import time
import random
from typing import AsyncIterator, Dict, Any, TYPE_CHECKING, cast
import logging

if TYPE_CHECKING:
    from litellm import acompletion
else:
    acompletion = None  # type: ignore

logger = logging.getLogger(__name__)

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

    def __init__(self, *args, max_retries: int = 3, **kwargs):
        """Initialize LiteLLM engine.
        
        Args:
            max_retries: Maximum number of retry attempts for transient failures
        """
        if not LITELLM_AVAILABLE:
            raise ImportError(
                "LiteLLM not installed. Install with: pip install litellm"
            )
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries

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
                    base_wait = 2 ** attempt  # Exponential backoff base: 2^n seconds
                    jitter = random.uniform(0.8, 1.2)  # 20% jitter to prevent thundering herd
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
        ]
        return any(pattern in error_str for pattern in transient_patterns)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate completion (non-streaming)."""
        if not LITELLM_AVAILABLE or litellm is None:
            raise RuntimeError("LiteLLM not available")
        litellm_client: Any = litellm
            
        async def _generate():
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            response = await litellm_client.acompletion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=self.api_key,
                stream=False,
                **self.extra_params
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Response content is None")
            return cast(str, content)
        
        return await self._retry_with_backoff(_generate(), "LiteLLM generation")

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
        if not LITELLM_AVAILABLE or litellm is None:
            raise RuntimeError("LiteLLM not available")
        litellm_client: Any = litellm
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Streaming doesn't use retry mechanism due to async generator complexity
        # Connection errors will be handled by caller if needed
        try:
            response = await litellm_client.acompletion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=self.api_key,
                stream=True,
                **self.extra_params
            )

            async for chunk in response:
                if chunk and hasattr(chunk, 'choices') and chunk.choices:
                    if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta:
                        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
        except asyncio.CancelledError:
            logger.warning("Streaming cancelled by user")
            raise
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise

    async def generate_chat(
        self,
        messages: list[dict],
    ) -> str:
        """Generate completion from full messages list (multi-turn chat)."""
        if not LITELLM_AVAILABLE or litellm is None:
            raise RuntimeError("LiteLLM not available")
        litellm_client: Any = litellm

        async def _generate_chat():
            response = await litellm_client.acompletion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=self.api_key,
                stream=False,
                **self.extra_params
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Response content is None")
            return cast(str, content)
        
        return await self._retry_with_backoff(_generate_chat(), "LiteLLM chat generation")

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
        if not LITELLM_AVAILABLE or litellm is None:
            raise RuntimeError("LiteLLM not available")
        litellm_client: Any = litellm

        # Streaming doesn't use retry mechanism due to async generator complexity
        try:
            response = await litellm_client.acompletion(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                api_key=self.api_key,
                stream=True,
                **self.extra_params
            )

            async for chunk in response:
                if chunk and hasattr(chunk, 'choices') and chunk.choices:
                    if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta:
                        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
        except asyncio.CancelledError:
            logger.warning("Chat streaming cancelled by user")
            raise
        except Exception as e:
            logger.error(f"Chat streaming error: {e}")
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status."""
        if not LITELLM_AVAILABLE or litellm is None:
            return {
                "success": False,
                "error": "LiteLLM not installed",
                "model": self.model,
            }
        litellm_client: Any = litellm
            
        try:
            start = time.time()
            messages = [{"role": "user", "content": "test"}]

            await litellm_client.acompletion(
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