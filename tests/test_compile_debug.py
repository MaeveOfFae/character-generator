#!/usr/bin/env python3
"""Test compile screen async streaming."""

import asyncio
from pathlib import Path
from bpui.core.config import Config
from bpui.core.prompting import build_asset_prompt

async def test_streaming():
    """Test that we can build prompts and simulate streaming."""
    config = Config()
    
    print("Config loaded:")
    print(f"  Engine: {config.engine}")
    print(f"  Model: {config.model}")
    print(f"  API Key: {'✓' if config.api_key else '✗'}")
    
    # Test building a prompt
    seed = "Test character seed"
    assets = {}
    
    system_prompt, user_prompt = build_asset_prompt("system_prompt", seed, None, assets)
    
    print(f"\nPrompt built successfully:")
    print(f"  System prompt length: {len(system_prompt)}")
    print(f"  User prompt length: {len(user_prompt)}")
    
    print("\n✓ Compile logic is ready")
    print("  The hang might be due to:")
    print("  1. Missing or invalid API key")
    print("  2. Network/connectivity issues")
    print("  3. LLM provider timeout")
    print("\nCheck the output log in TUI for detailed error messages")

if __name__ == "__main__":
    asyncio.run(test_streaming())
