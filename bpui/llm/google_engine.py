"""Google Generative AI engine adapter."""

import asyncio
import time
import random
from typing import AsyncIterator, Dict, Any, TYPE_CHECKING, List, cast
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import google.generativeai as genai  # type: ignore

try:
    import google.generativeai as genai  # type: ignore
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    genai = None  # type: ignore

from .base import LLMEngine


class GoogleEngine(LLMEngine):
    """Google Generative AI adapter for Gemini models."""

    # Default safety settings (BLOCK_NONE for all categories)
    DEFAULT_SAFETY_SETTINGS = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    def __init__(self, *args, max_retries: int = 3, safety_settings: List[Dict] = None, **kwargs):
        """Initialize Google Generative AI engine.

        Args:
            max_retries: Maximum number of retry attempts for transient failures
            safety_settings: List of safety setting dicts (uses permissive defaults if not provided)
            **kwargs: Additional generation config parameters (top_k, top_p, etc.)
        """
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "Google Generative AI SDK not installed. Install with: pip install google-generativeai"
            )
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries

        # Configure API key
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            raise ValueError("API key required for GoogleEngine")

        # Safety settings
        self.safety_settings = safety_settings or self.DEFAULT_SAFETY_SETTINGS

        # Extract generation config parameters
        self.generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }

        # Add optional parameters from kwargs
        for param in ["top_k", "top_p", "candidate_count"]:
            if param in self.extra_params:
                self.generation_config[param] = self.extra_params.pop(param)

        # Create model instance
        self.model_instance = genai.GenerativeModel(
            model_name=self.model,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )

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
            "quota",
            "overloaded",
        ]
        return any(pattern in error_str for pattern in transient_patterns)

    def _prepare_messages_for_google(
        self, system_prompt: str = None, user_prompt: str = None, messages: list = None
    ) -> List[Dict[str, str]]:
        """Prepare messages for Google's format.

        Google doesn't have a native system role, so we prepend system prompts
        to the first user message.

        Args:
            system_prompt: Optional system prompt
            user_prompt: Optional user prompt
            messages: Optional full message list (for chat)

        Returns:
            List of messages in Google's format
        """
        if messages:
            # Convert from standard format to Google format
            google_messages = []
            system_content = ""

            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")

                if role == "system":
                    # Accumulate system messages
                    system_content += content + "\n\n"
                elif role == "user":
                    # Prepend accumulated system content to first user message
                    if system_content:
                        content = system_content + content
                        system_content = ""
                    google_messages.append({"role": "user", "parts": [content]})
                elif role == "assistant":
                    google_messages.append({"role": "model", "parts": [content]})

            return google_messages

        # Simple case: system + user prompt
        content = user_prompt or ""
        if system_prompt:
            content = f"{system_prompt}\n\n{content}"

        return [{"role": "user", "parts": [content]}]

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate completion (non-streaming)."""
        if not GOOGLE_AVAILABLE or genai is None:
            raise RuntimeError("Google Generative AI SDK not available")

        async def _generate():
            # Prepare content
            content = user_prompt
            if system_prompt:
                content = f"{system_prompt}\n\n{content}"

            # Generate content
            response = await asyncio.to_thread(
                self.model_instance.generate_content,
                content,
            )

            # Extract text from response
            if not response or not response.text:
                raise ValueError("Empty response from Google API")

            return cast(str, response.text)

        return await self._retry_with_backoff(_generate(), "Google generation")

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
        if not GOOGLE_AVAILABLE or genai is None:
            raise RuntimeError("Google Generative AI SDK not available")

        # Prepare content
        content = user_prompt
        if system_prompt:
            content = f"{system_prompt}\n\n{content}"

        try:
            # Generate streaming response in thread to avoid blocking
            response = await asyncio.to_thread(
                self.model_instance.generate_content,
                content,
                stream=True,
            )

            # Stream chunks
            for chunk in response:
                if chunk and chunk.text:
                    yield chunk.text

        except asyncio.CancelledError:
            logger.warning("Streaming cancelled by user")
            raise
        except Exception as e:
            logger.error(f"Google streaming error: {e}")
            raise

    async def generate_chat(
        self,
        messages: list[dict],
    ) -> str:
        """Generate completion from full messages list (multi-turn chat)."""
        if not GOOGLE_AVAILABLE or genai is None:
            raise RuntimeError("Google Generative AI SDK not available")

        async def _generate_chat():
            # Prepare messages for Google
            google_messages = self._prepare_messages_for_google(None, None, messages)

            # Start chat session
            chat = self.model_instance.start_chat(history=google_messages[:-1] if len(google_messages) > 1 else [])

            # Send last message
            last_message_content = google_messages[-1]["parts"][0] if google_messages else ""
            response = await asyncio.to_thread(
                chat.send_message,
                last_message_content,
            )

            if not response or not response.text:
                raise ValueError("Empty response from Google chat")

            return cast(str, response.text)

        return await self._retry_with_backoff(_generate_chat(), "Google chat generation")

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
        if not GOOGLE_AVAILABLE or genai is None:
            raise RuntimeError("Google Generative AI SDK not available")

        try:
            # Prepare messages for Google
            google_messages = self._prepare_messages_for_google(None, None, messages)

            # Start chat session
            chat = self.model_instance.start_chat(history=google_messages[:-1] if len(google_messages) > 1 else [])

            # Send last message with streaming
            last_message_content = google_messages[-1]["parts"][0] if google_messages else ""
            response = await asyncio.to_thread(
                chat.send_message,
                last_message_content,
                stream=True,
            )

            # Stream chunks
            for chunk in response:
                if chunk and chunk.text:
                    yield chunk.text

        except asyncio.CancelledError:
            logger.warning("Chat streaming cancelled by user")
            raise
        except Exception as e:
            logger.error(f"Google chat streaming error: {e}")
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status."""
        if not GOOGLE_AVAILABLE or genai is None:
            return {
                "success": False,
                "error": "Google Generative AI SDK not installed",
                "model": self.model,
            }

        try:
            start = time.time()

            # Simple test generation
            response = await asyncio.to_thread(
                self.model_instance.generate_content,
                "test",
            )

            if not response or not response.text:
                raise ValueError("Empty response from test")

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
    async def list_models(api_key: str, timeout: float = 30.0) -> list[str]:
        """List available Google Gemini models.

        Args:
            api_key: Google API key for authentication
            timeout: Request timeout in seconds

        Returns:
            List of model IDs available from Google

        Raises:
            Exception: If API request fails or SDK not available
        """
        if not GOOGLE_AVAILABLE or genai is None:
            raise ImportError("Google Generative AI SDK not installed. Install with: pip install google-generativeai")

        import asyncio

        try:
            # Configure API key
            genai.configure(api_key=api_key)

            # Fetch models in a thread to avoid blocking
            def _fetch_models():
                return list(genai.list_models())

            models_list = await asyncio.to_thread(_fetch_models)

            # Extract model names and filter for chat models
            models = []
            for model in models_list:
                # Filter for chat models (contain "generateContent" capability)
                model_name = model.name.replace("models/", "")
                # Only include models that support generation
                if "generateContent" in model.supported_generation_methods:
                    models.append(model_name)

            # Sort models alphabetically
            return sorted(models)

        except Exception as e:
            raise Exception(f"Failed to list Google models: {e}") from e
