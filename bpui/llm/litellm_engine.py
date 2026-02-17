"""Compatibility shim for legacy LiteLLM engine import path.

This project now uses provider-specific engines/factory logic. For backward
compatibility, expose `LiteLLMEngine` as an alias to `OpenAIEngine`.
"""

from bpui.llm.openai_engine import OpenAIEngine as LiteLLMEngine
