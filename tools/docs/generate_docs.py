#!/usr/bin/env python3
"""Generate API documentation with pdoc3."""

import subprocess
import sys
from pathlib import Path


def main():
    """Generate API documentation."""
    repo_root = Path(__file__).parent.parent
    docs_dir = repo_root / "docs" / "api"
    
    # Create docs directory
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating API documentation...")
    print(f"Output directory: {docs_dir}")
    
    # Generate docs for bpui package
    cmd = [
        "pdoc",
        "--html",
        "--output-dir", str(docs_dir),
        "--force",
        "--config", "show_source_code=False",
        "bpui",
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n✓ Documentation generated successfully!")
            print(f"  Location: {docs_dir}/bpui/")
            print(f"\nTo view:")
            print(f"  python -m http.server --directory {docs_dir}/bpui")
            print(f"  Then open: http://localhost:8000")
            return 0
        else:
            print(f"\n✗ Documentation generation failed")
            print(f"\nSTDOUT:\n{result.stdout}")
            print(f"\nSTDERR:\n{result.stderr}")
            return 1
    
    except FileNotFoundError:
        print("\n✗ pdoc3 not found")
        print("Install with: pip install pdoc3")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
