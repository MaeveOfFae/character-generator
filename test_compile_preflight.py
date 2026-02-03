#!/usr/bin/env python3
"""Simple test to verify compile logic without TUI."""

import asyncio
from pathlib import Path
from bpui.config import Config
from bpui.llm.litellm_engine import LiteLLMEngine
from bpui.llm.openai_compat_engine import OpenAICompatEngine
from bpui.prompting import build_asset_prompt

async def test_compile():
    """Test compile without TUI."""
    config = Config()
    
    print("=" * 60)
    print("COMPILE DEBUG TEST")
    print("=" * 60)
    
    print(f"\nConfig:")
    print(f"  Engine: {config.engine}")
    print(f"  Model: {config.model}")
    print(f"  API Key: {'✓ configured' if config.api_key else '✗ NOT FOUND'}")
    
    if not config.api_key:
        print("\n❌ No API key found!")
        print("   Configure in .bpui.toml or Settings screen")
        return
    
    print(f"\n✓ Configuration valid")
    
    # Test creating engine
    print(f"\nCreating {config.engine} engine...")
    try:
        engine_config = {
            "model": config.model,
            "api_key": config.api_key,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        
        if config.engine == "litellm":
            engine = LiteLLMEngine(**engine_config)
        else:
            engine_config["base_url"] = config.base_url
            engine = OpenAICompatEngine(**engine_config)
        
        print("✓ Engine created successfully")
    except Exception as e:
        print(f"❌ Failed to create engine: {e}")
        return
    
    # Test building prompt
    print("\nBuilding test prompt...")
    try:
        system_prompt, user_prompt = build_asset_prompt(
            "system_prompt", 
            "A test character", 
            None, 
            {}
        )
        print(f"✓ Prompt built (system: {len(system_prompt)} chars, user: {len(user_prompt)} chars)")
    except Exception as e:
        print(f"❌ Failed to build prompt: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✓ All pre-flight checks passed!")
    print("=" * 60)
    print("\nThe TUI should work. If it still hangs:")
    print("  1. Check network connectivity")
    print("  2. Verify API key is valid")
    print("  3. Check if LLM provider is accessible")
    print("  4. Look at the output log in TUI for error messages")

if __name__ == "__main__":
    asyncio.run(test_compile())
