"""Validation helpers for character packs."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Optional, Dict, Any


def validate_pack(pack_dir: Path, repo_root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate a character pack directory using tools/validate_pack.py.

    Args:
        pack_dir: Directory to validate.
        repo_root: Repository root containing tools/validate_pack.py.

    Returns:
        Dict with keys: output, errors, exit_code, success.
    """
    if repo_root is None:
        repo_root = Path.cwd()

    validator = repo_root / "tools" / "validate_pack.py"
    if not validator.exists():
        return {
            "output": "",
            "errors": f"Validator not found: {validator}",
            "exit_code": 1,
            "success": False,
        }

    try:
        result = subprocess.run(
            ["python3", str(validator), str(pack_dir)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(repo_root),
        )
        return {
            "output": result.stdout,
            "errors": result.stderr,
            "exit_code": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "output": "",
            "errors": "Validation timed out after 30 seconds",
            "exit_code": 124,
            "success": False,
        }
    except Exception as exc:
        return {
            "output": "",
            "errors": str(exc),
            "exit_code": 1,
            "success": False,
        }
