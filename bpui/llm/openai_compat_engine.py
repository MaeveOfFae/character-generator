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
        
        # Check if this is OpenRouter
        self.is_openrouter = "openrouter.ai" in self.base_url.lower()
    
    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for requests.
        
        Returns:
            Dictionary of HTTP headers, including OpenRouter-specific headers if needed
        """
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # OpenRouter requires these headers
        if self.is_openrouter:
            headers["HTTP-Referer"] = "https://github.com/maeveoffae/character-generator"
            headers["X-Title"] = "Blueprint Character Generator"
        
        return headers

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

        headers = self._build_headers()

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                # Try to extract error details from response
                error_detail = ""
                try:
                    error_body = e.response.json()
                    error_detail = f" - {error_body.get('error', {}).get('message', error_body)}"
                except:
                    error_detail = f" - {e.response.text[:200]}"
                raise Exception(
                    f"Chat API request failed with status {e.response.status_code}{error_detail}"
                ) from e

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

        headers = self._build_headers()

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

    async def generate_chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
    ) -> str | dict:
        """Generate completion from full messages list (multi-turn chat).

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tool definitions for function calling
            tool_choice: Optional tool choice strategy ("auto", "none", or specific tool)

        Returns:
            Either a string (text response) or dict (with tool_calls if tools were used)
        """
        headers = self._build_headers()

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        # Add tools if provided
        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice

        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                # Check if response contains tool calls
                choice = data["choices"][0]
                message = choice.get("message", {})

                # Preserve extended thinking content if present (for Claude models)
                result_message = {}
                if "content" in message:
                    result_message["content"] = message["content"]
                if "reasoning_content" in message:
                    result_message["reasoning_content"] = message["reasoning_content"]
                if "tool_calls" in message and message["tool_calls"]:
                    result_message["tool_calls"] = message["tool_calls"]

                # Return based on what's in the response
                if "tool_calls" in result_message:
                    # Return full message dict with tool calls (and optionally reasoning)
                    return result_message
                elif "reasoning_content" in result_message:
                    # Return dict with both content and reasoning
                    return result_message
                else:
                    # Return just the text content
                    return message.get("content", "")
            except httpx.HTTPStatusError as e:
                # Try to extract error details from response
                error_detail = ""
                try:
                    error_body = e.response.json()
                    error_detail = f" - {error_body.get('error', {}).get('message', error_body)}"
                except:
                    error_detail = f" - {e.response.text[:200]}"
                raise Exception(
                    f"Chat API request failed with status {e.response.status_code}{error_detail}"
                ) from e

    def generate_chat_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
    ) -> AsyncIterator[str | dict]:
        """Generate completion from full messages list with streaming.

        Args:
            messages: List of message dicts with role and content
            tools: Optional list of tool definitions for function calling
            tool_choice: Optional tool choice strategy ("auto", "none", or specific tool)

        Returns:
            AsyncIterator yielding either strings (text chunks) or dicts (tool calls)
        """
        return self._generate_chat_stream_impl(messages, tools, tool_choice)

    async def _generate_chat_stream_impl(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
    ) -> AsyncIterator[str | dict]:
        """Internal streaming implementation for chat."""
        headers = self._build_headers()

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }

        # Add tools if provided
        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice

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
                                # Yield content if present
                                if "content" in delta:
                                    yield delta["content"]
                                # Yield tool calls if present
                                elif "tool_calls" in delta:
                                    yield {"tool_calls": delta["tool_calls"]}
                        except json.JSONDecodeError:
                            continue

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return status."""
        try:
            start = time.time()
            messages = [{"role": "user", "content": "test"}]

            headers = self._build_headers()

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
        except httpx.HTTPStatusError as e:
            # Try to extract error details from response
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_body = e.response.json()
                if isinstance(error_body.get('error'), dict):
                    error_detail += f": {error_body['error'].get('message', '')}"
                elif error_body.get('error'):
                    error_detail += f": {error_body['error']}"
            except:
                error_detail += f": {e.response.text[:200]}"
            
            return {
                "success": False,
                "error": error_detail,
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

    @staticmethod
    async def list_models(base_url: str, api_key: str | None = None, timeout: float = 30.0) -> list[str]:
        """List available models from OpenAI-compatible API.

        Args:
            base_url: Base URL of the OpenAI-compatible API
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds

        Returns:
            List of model IDs available from the API

        Raises:
            Exception: If API request fails
        """
        import asyncio

        base_url = base_url.rstrip("/")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # OpenRouter requires these headers
        if "openrouter.ai" in base_url.lower():
            headers["HTTP-Referer"] = "https://github.com/maeveoffae/character-generator"
            headers["X-Title"] = "Blueprint Character Generator"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    f"{base_url}/models",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

            # Parse response - OpenAI format has "data" array with "id" field
            if "data" in data:
                models = [model["id"] for model in data["data"]]
                # Sort models alphabetically
                return sorted(models)
            else:
                # Fallback: try to extract models from response
                return []

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # /models endpoint not available, return empty list
                return []
            raise Exception(f"Failed to list models: {e}") from e
        except Exception as e:
            raise Exception(f"Failed to list models: {e}") from e
