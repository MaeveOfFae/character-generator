#!/usr/bin/env python3
"""Diagnostic tool for testing agent chatbox functionality."""

import sys
from pathlib import Path

# Add bpui to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all agent modules can be imported."""
    print("=" * 60)
    print("Testing Agent Module Imports")
    print("=" * 60)

    try:
        from bpui.gui.agent_chatbox import AgentChatbox, AgentWorker
        print("✓ Agent chatbox imports successfully")
    except Exception as e:
        print(f"✗ Failed to import AgentChatbox: {e}")
        return False

    try:
        from bpui.gui.agent_actions import AgentActionHandler, AGENT_TOOLS
        print(f"✓ Agent actions import successfully ({len(AGENT_TOOLS)} tools)")
    except Exception as e:
        print(f"✗ Failed to import agent actions: {e}")
        return False

    try:
        from bpui.gui.conversation_manager import ConversationManager
        print("✓ Conversation manager imports successfully")
    except Exception as e:
        print(f"✗ Failed to import ConversationManager: {e}")
        return False

    try:
        from bpui.gui.personality_manager import PersonalityManager
        print("✓ Personality manager imports successfully")
    except Exception as e:
        print(f"✗ Failed to import PersonalityManager: {e}")
        return False

    return True


def test_tools():
    """Test that all agent tools are properly defined."""
    print("\n" + "=" * 60)
    print("Testing Agent Tools")
    print("=" * 60)

    try:
        from bpui.gui.agent_actions import AGENT_TOOLS

        print(f"\nFound {len(AGENT_TOOLS)} agent tools:\n")
        for tool in AGENT_TOOLS:
            func = tool.get("function", {})
            name = func.get("name", "unknown")
            desc = func.get("description", "No description")
            print(f"  • {name}")
            print(f"    {desc}")

        return True
    except Exception as e:
        print(f"✗ Error inspecting tools: {e}")
        return False


def test_personalities():
    """Test that personalities can be loaded."""
    print("\n" + "=" * 60)
    print("Testing Personalities")
    print("=" * 60)

    try:
        from bpui.gui.personality_manager import PersonalityManager

        manager = PersonalityManager()
        personalities = manager.list_personalities()

        print(f"\nFound {len(personalities)} personalities:\n")
        for p in personalities:
            # Handle both dict and object formats
            if isinstance(p, dict):
                name = p.get("name", "Unknown")
                pid = p.get("id", "unknown")
                desc = p.get("description", "No description")
                temp = p.get("temperature", 0.7)
                max_tok = p.get("max_tokens", 1000)
            else:
                name = p.name
                pid = p.id
                desc = p.description
                temp = p.temperature
                max_tok = p.max_tokens

            print(f"  • {name} ({pid})")
            print(f"    {desc}")
            print(f"    Temp: {temp}, Max tokens: {max_tok}")

        return True
    except Exception as e:
        print(f"✗ Error loading personalities: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test that config loads correctly."""
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)

    try:
        from bpui.core.config import Config

        config = Config()
        print(f"✓ Config loaded from: {config.config_path}")
        print(f"  Model: {config.model}")
        print(f"  Engine: {config.engine}")

        # Check API key (without exposing it)
        api_key = config.api_key
        if api_key:
            print(f"  API Key: ***{api_key[-8:]}")
        else:
            print(f"  ⚠ Warning: No API key configured")

        return True
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_engine():
    """Test that LLM engine can be created."""
    print("\n" + "=" * 60)
    print("Testing LLM Engine")
    print("=" * 60)

    try:
        from bpui.core.config import Config
        from bpui.llm.factory import create_engine

        config = Config()
        engine = create_engine(config)

        print(f"✓ Engine created successfully")
        print(f"  Type: {type(engine).__name__}")
        print(f"  Model: {engine.model}")

        return True
    except Exception as e:
        print(f"✗ Error creating engine: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all diagnostic tests."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "Agent Chatbox Diagnostic" + " " * 19 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    results = []

    results.append(("Module Imports", test_imports()))
    results.append(("Agent Tools", test_tools()))
    results.append(("Personalities", test_personalities()))
    results.append(("Configuration", test_config()))
    results.append(("LLM Engine", test_llm_engine()))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\nPassed: {total_passed}/{total_tests}")

    if total_passed == total_tests:
        print("\n✓ All diagnostics passed! The agent should be working correctly.")
        return 0
    else:
        print(f"\n✗ {total_tests - total_passed} diagnostic(s) failed. See errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
