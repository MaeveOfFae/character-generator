#!/usr/bin/env python3
"""Quick test script to verify bpui installation."""

import sys


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        import bpui
        print("✓ bpui")
    except ImportError as e:
        print(f"✗ bpui: {e}")
        return False

    try:
        from bpui.core.config import Config
        print("✓ bpui.config")
    except ImportError as e:
        print(f"✗ bpui.config: {e}")
        return False

    try:
        from bpui.llm.base import LLMEngine
        print("✓ bpui.llm.base")
    except ImportError as e:
        print(f"✗ bpui.llm.base: {e}")
        return False

    try:
        from bpui.llm.openai_compat_engine import OpenAICompatEngine
        print("✓ bpui.llm.openai_compat_engine")
    except ImportError as e:
        print(f"✗ bpui.llm.openai_compat_engine: {e}")
        return False

    try:
        from bpui.llm.litellm_engine import LiteLLMEngine
        print("✓ bpui.llm.litellm_engine (optional)")
    except ImportError as e:
        print(f"⚠ bpui.llm.litellm_engine (optional): {e}")
        print("  Install with: pip install litellm")

    try:
        from bpui.core.prompting import build_orchestrator_prompt
        print("✓ bpui.prompting")
    except ImportError as e:
        print(f"✗ bpui.prompting: {e}")
        return False

    try:
        from bpui.core.parse_blocks import parse_blueprint_output
        print("✓ bpui.parse_blocks")
    except ImportError as e:
        print(f"✗ bpui.parse_blocks: {e}")
        return False

    try:
        from bpui.utils.file_io.pack_io import create_draft_dir
        print("✓ bpui.pack_io")
    except ImportError as e:
        print(f"✗ bpui.pack_io: {e}")
        return False

    try:
        from bpui.utils.file_io.validate import validate_pack
        print("✓ bpui.validate")
    except ImportError as e:
        print(f"✗ bpui.validate: {e}")
        return False

    try:
        from bpui.features.export.export import export_character
        print("✓ bpui.export")
    except ImportError as e:
        print(f"✗ bpui.export: {e}")
        return False

    try:
        from bpui.tui.app import BlueprintUI
        print("✓ bpui.tui.app")
    except ImportError as e:
        print(f"✗ bpui.tui.app: {e}")
        return False

    print("\n✓ All core modules imported successfully!")
    return True


def test_config():
    """Test config loading."""
    print("\nTesting config...")

    try:
        from bpui.core.config import Config

        config = Config()
        print(f"✓ Config loaded")
        print(f"  Engine: {config.engine}")
        print(f"  Model: {config.model}")
        print(f"  Temperature: {config.temperature}")
        print(f"  Max tokens: {config.max_tokens}")
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False


def test_parser():
    """Test codeblock parser."""
    print("\nTesting parser...")

    try:
        from bpui.core.parse_blocks import extract_codeblocks, parse_blueprint_output

        # Test codeblock extraction
        test_text = """
Some text before.

```
First block
```

```
Second block
```
"""
        blocks = extract_codeblocks(test_text)
        assert len(blocks) == 2, f"Expected 2 blocks, got {len(blocks)}"
        print(f"✓ Codeblock extraction works")

        # Test 7-block parsing
        test_output = "\n".join([f"```\nBlock {i}\n```" for i in range(1, 8)])
        assets = parse_blueprint_output(test_output)
        assert len(assets) == 7, f"Expected 7 assets, got {len(assets)}"
        print(f"✓ 7-block parsing works")

        return True
    except Exception as e:
        print(f"✗ Parser test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=== BPUI Installation Test ===\n")

    tests = [
        test_imports,
        test_config,
        test_parser,
    ]

    results = [test() for test in tests]

    print("\n=== Summary ===")
    if all(results):
        print("✓ All tests passed!")
        print("\nYou can now run: bpui")
        return 0
    else:
        print("✗ Some tests failed")
        print("\nPlease check the errors above and:")
        print("  1. Ensure dependencies are installed: pip install -e .")
        print("  2. For LiteLLM support: pip install -e '.[litellm]'")
        return 1


if __name__ == "__main__":
    sys.exit(main())
