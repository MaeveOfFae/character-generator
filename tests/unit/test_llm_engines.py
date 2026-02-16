"""Tests for bpui/llm/ engines."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bpui.llm.base import LLMEngine
from bpui.llm.openai_compat_engine import OpenAICompatEngine


class MockLLMEngine(LLMEngine):
    """Mock implementation for testing base class."""
    
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        return "mock response"
    
    def generate_stream(self, system_prompt: str, user_prompt: str):
        async def _stream():
            yield "mock"
            yield " stream"
        return _stream()

    async def generate_chat(self, messages: list[dict]) -> str:
        return "mock chat response"

    def generate_chat_stream(self, messages: list[dict]):
        async def _stream():
            yield "mock"
            yield " chat"
            yield " stream"
        return _stream()
    
    async def test_connection(self):
        return {"success": True}


class TestLLMEngineBase:
    """Tests for LLMEngine base class."""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        engine = MockLLMEngine(model="test-model")
        
        assert engine.model == "test-model"
        assert engine.api_key is None
        assert engine.temperature == 0.7
        assert engine.max_tokens == 4096
        assert engine.extra_params == {}
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        engine = MockLLMEngine(
            model="custom-model",
            api_key="sk-test123",
            temperature=0.9,
            max_tokens=2048,
            custom_param="value"
        )
        
        assert engine.model == "custom-model"
        assert engine.api_key == "sk-test123"
        assert engine.temperature == 0.9
        assert engine.max_tokens == 2048
        assert engine.extra_params == {"custom_param": "value"}
    
    def test_init_with_extra_kwargs(self):
        """Test that extra kwargs are stored."""
        engine = MockLLMEngine(
            model="test",
            foo="bar",
            baz=123
        )
        
        assert engine.extra_params == {"foo": "bar", "baz": 123}
    
    @pytest.mark.asyncio
    async def test_generate_abstract(self):
        """Test that generate is abstract."""
        engine = MockLLMEngine(model="test")
        result = await engine.generate("system", "user")
        
        assert result == "mock response"
    
    @pytest.mark.asyncio
    async def test_generate_stream_abstract(self):
        """Test that generate_stream is abstract."""
        engine = MockLLMEngine(model="test")
        stream = engine.generate_stream("system", "user")
        
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        
        assert chunks == ["mock", " stream"]
    
    @pytest.mark.asyncio
    async def test_test_connection_abstract(self):
        """Test that test_connection is abstract."""
        engine = MockLLMEngine(model="test")
        result = await engine.test_connection()
        
        assert result == {"success": True}



class TestOpenAICompatEngine:
    """Tests for OpenAICompatEngine."""
    
    def test_init_without_base_url(self):
        """Test that ValueError is raised without base_url."""
        with pytest.raises(ValueError, match="base_url is required"):
            OpenAICompatEngine(model="test", base_url="")
    
    def test_init_with_base_url(self):
        """Test initialization with base_url."""
        engine = OpenAICompatEngine(
            model="test-model",
            base_url="http://localhost:8000"
        )
        
        assert engine.model == "test-model"
        assert engine.base_url == "http://localhost:8000"
    
    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base_url."""
        engine = OpenAICompatEngine(
            model="test",
            base_url="http://localhost:8000/"
        )
        
        assert engine.base_url == "http://localhost:8000"
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        engine = OpenAICompatEngine(
            model="test",
            base_url="http://localhost:8000",
            api_key="sk-test123"
        )
        
        assert engine.api_key == "sk-test123"
    
    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful generation."""
        engine = OpenAICompatEngine(
            model="test-model",
            base_url="http://localhost:8000"
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated text"}}]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await engine.generate("You are helpful", "Hello")
            
            assert result == "Generated text"
            mock_client.return_value.__aenter__.return_value.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_with_api_key(self):
        """Test generation with API key in headers."""
        engine = OpenAICompatEngine(
            model="test",
            base_url="http://localhost:8000",
            api_key="sk-test123"
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "response"}}]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            await engine.generate("system", "user")
            
            # Check that Authorization header was included
            call_kwargs = mock_post.call_args[1]
            assert "Authorization" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Authorization"] == "Bearer sk-test123"
    
    @pytest.mark.asyncio
    async def test_generate_http_error(self):
        """Test generation with HTTP error."""
        engine = OpenAICompatEngine(
            model="test",
            base_url="http://localhost:8000"
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Connection error")
            )
            
            with pytest.raises(Exception, match="Connection error"):
                await engine.generate("system", "user")
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """Test successful connection test."""
        engine = OpenAICompatEngine(
            model="test-model",
            base_url="http://localhost:8000"
        )
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await engine.test_connection()
            
            assert result["success"] is True
            assert "latency_ms" in result
            assert result["model"] == "test-model"
            assert result["base_url"] == "http://localhost:8000"
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """Test connection test with failure."""
        engine = OpenAICompatEngine(
            model="test-model",
            base_url="http://localhost:8000"
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Network error")
            )
            
            result = await engine.test_connection()
            
            assert result["success"] is False
            assert "error" in result
            assert "Network error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """Test streaming generation."""
        engine = OpenAICompatEngine(
            model="test",
            base_url="http://localhost:8000"
        )
        
        # Mock streaming response
        stream_data = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            'data: {"choices":[{"delta":{"content":" world"}}]}',
            'data: [DONE]',
        ]
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        async def mock_aiter_lines():
            for line in stream_data:
                yield line
        
        mock_response.aiter_lines = mock_aiter_lines
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_stream = MagicMock()
            mock_stream.__aenter__.return_value = mock_response
            mock_stream.__aexit__.return_value = AsyncMock()
            mock_client.return_value.__aenter__.return_value.stream = MagicMock(
                return_value=mock_stream
            )
            
            chunks = []
            stream = engine.generate_stream("system", "user")
            async for chunk in stream:
                chunks.append(chunk)
            
            assert chunks == ["Hello", " world"]
    
    @pytest.mark.asyncio
    async def test_generate_stream_with_api_key(self):
        """Test streaming with API key."""
        engine = OpenAICompatEngine(
            model="test",
            base_url="http://localhost:8000",
            api_key="sk-test123"
        )
        
        stream_data = [
            'data: {"choices":[{"delta":{"content":"test"}}]}',
            'data: [DONE]',
        ]
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        async def mock_aiter_lines():
            for line in stream_data:
                yield line
        
        mock_response.aiter_lines = mock_aiter_lines
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_stream_context = MagicMock()
            mock_stream_context.__aenter__.return_value = mock_response
            mock_stream_context.__aexit__.return_value = AsyncMock()
            
            mock_stream = MagicMock(return_value=mock_stream_context)
            mock_client.return_value.__aenter__.return_value.stream = mock_stream
            
            stream = engine.generate_stream("system", "user")
            async for _ in stream:
                pass
            
            # Verify Authorization header was set
            call_kwargs = mock_stream.call_args[1]
            assert "headers" in call_kwargs
            assert call_kwargs["headers"]["Authorization"] == "Bearer sk-test123"
    
    @pytest.mark.asyncio
    async def test_generate_stream_invalid_json(self):
        """Test streaming with invalid JSON (should skip)."""
        engine = OpenAICompatEngine(
            model="test",
            base_url="http://localhost:8000"
        )
        
        stream_data = [
            'data: invalid json',
            'data: {"choices":[{"delta":{"content":"valid"}}]}',
            'data: [DONE]',
        ]
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        
        async def mock_aiter_lines():
            for line in stream_data:
                yield line
        
        mock_response.aiter_lines = mock_aiter_lines
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_stream = MagicMock()
            mock_stream.__aenter__.return_value = mock_response
            mock_stream.__aexit__.return_value = AsyncMock()
            mock_client.return_value.__aenter__.return_value.stream = MagicMock(
                return_value=mock_stream
            )
            
            chunks = []
            stream = engine.generate_stream("system", "user")
            async for chunk in stream:
                chunks.append(chunk)
            
            # Should skip invalid JSON and only get valid chunk
            assert chunks == ["valid"]
