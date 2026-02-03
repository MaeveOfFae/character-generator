"""Base LLM interface for Blueprint UI."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional


class LLMEngine(ABC):
    """Base class for LLM engines."""

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ):
        """Initialize engine."""
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Generate completion (non-streaming)."""
        pass

    @abstractmethod
    def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:
        """Generate completion with streaming."""
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status."""
        pass
