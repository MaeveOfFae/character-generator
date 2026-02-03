"""Validation wrapper for tools/validate_pack.py."""

import subprocess
from pathlib import Path
from typing import Dict, Optional, Any


def validate_pack(pack_dir: Path, repo_root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate a pack directory.

    Args:
        pack_dir: Directory containing pack files
        repo_root: Repository root path

    Returns:
        Dict with validation results:
            - success: bool
            - output: str (stdout)
            - errors: str (stderr)
            - exit_code: int
    """
    if repo_root is None:
        repo_root = Path.cwd()

    validator_path = repo_root / "tools" / "validate_pack.py"
    if not validator_path.exists():
        return {
            "success": False,
            "output": "",
            "errors": f"Validator not found: {validator_path}",
            "exit_code": 1,
        }

    try:
        result = subprocess.run(
            ["python3", str(validator_path), str(pack_dir)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "errors": "Validation timed out after 30 seconds",
            "exit_code": 124,
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "errors": str(e),
            "exit_code": 1,
        }
