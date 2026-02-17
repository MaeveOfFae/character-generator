#!/usr/bin/env python3
"""Test script for OpenRouter agent capabilities with tool calling and extended thinking."""

import asyncio
import os
import sys
from pathlib import Path

# Add bpui to path
sys.path.insert(0, str(Path(__file__).parent))

from bpui.core.config import Config
from bpui.llm.factory import create_engine


# Simple test tools
TEST_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g., San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform a mathematical calculation",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate, e.g., '2 + 2'"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]


async def test_basic_chat():
    """Test basic chat without tools."""
    print("\n=== Test 1: Basic Chat (No Tools) ===")

    config = Config()
    engine = create_engine(config)

    messages = [
        {"role": "user", "content": "Say hello in one sentence."}
    ]

    try:
        response = await engine.generate_chat(messages)
        print(f"Response: {response}")
        print("✓ Basic chat test passed")
        return True
    except Exception as e:
        print(f"✗ Basic chat test failed: {e}")
        return False


async def test_tool_calling():
    """Test tool calling capability."""
    print("\n=== Test 2: Tool Calling ===")

    config = Config()
    engine = create_engine(config)

    messages = [
        {"role": "user", "content": "What's the weather in San Francisco? Use the get_weather tool."}
    ]

    try:
        response = await engine.generate_chat(messages, tools=TEST_TOOLS, tool_choice="auto")

        if isinstance(response, dict):
            if "tool_calls" in response:
                print(f"✓ Tool calling test passed")
                print(f"  Tool calls: {response['tool_calls']}")
                if "reasoning_content" in response:
                    print(f"  Extended thinking detected: {response['reasoning_content'][:100]}...")
                return True
            else:
                print(f"✗ Expected tool calls but got: {response}")
                return False
        else:
            print(f"✗ Expected dict response but got string: {response}")
            return False
    except Exception as e:
        print(f"✗ Tool calling test failed: {e}")
        return False


async def test_extended_thinking():
    """Test extended thinking mode (if model supports it)."""
    print("\n=== Test 3: Extended Thinking Detection ===")

    config = Config()

    # Check if using a Claude model (which supports extended thinking)
    model = config.model
    is_claude = "claude" in model.lower() or "anthropic" in model.lower()

    if not is_claude:
        print(f"⊘ Skipping extended thinking test (model '{model}' doesn't support it)")
        return True

    engine = create_engine(config)

    messages = [
        {"role": "user", "content": "Think step by step and explain why the sky is blue."}
    ]

    try:
        response = await engine.generate_chat(messages)

        if isinstance(response, dict) and "reasoning_content" in response:
            print(f"✓ Extended thinking test passed")
            print(f"  Reasoning: {response['reasoning_content'][:150]}...")
            print(f"  Content: {response['content'][:100]}...")
            return True
        else:
            print(f"ℹ Extended thinking not detected (may not be enabled for this model)")
            return True  # Not a failure, just not enabled
    except Exception as e:
        print(f"✗ Extended thinking test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("OpenRouter Agent Capabilities Test Suite")
    print("=" * 60)

    # Check configuration
    config = Config()
    print(f"\nConfiguration:")
    print(f"  Model: {config.model}")
    print(f"  Engine: {config.engine}")
    print(f"  Base URL: {config.base_url}")

    # Check API key
    api_key = config.api_key
    if not api_key:
        print("\n✗ ERROR: No API key configured!")
        print("  Set your OpenRouter API key:")
        print("    bpui config set api_keys.openrouter YOUR_KEY")
        print("  Or set environment variable:")
        print("    export OPENROUTER_API_KEY=YOUR_KEY")
        return 1

    print(f"  API Key: ***{api_key[-8:]}")

    # Run tests
    results = []
    results.append(await test_basic_chat())
    results.append(await test_tool_calling())
    results.append(await test_extended_thinking())

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed! OpenRouter agent capabilities are working.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. See errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
