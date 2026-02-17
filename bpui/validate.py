"""Validation helpers for character packs."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Optional, Dict, Any


def _resolve_validator(repo_root: Path) -> Optional[Path]:
    """Resolve validator path, supporting legacy and new tool layouts."""
    candidates = [
        repo_root / "tools" / "validate_pack.py",
        repo_root / "tools" / "validation" / "validate_pack.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def validate_pack(pack_dir: Path, repo_root: Optional[Path] = None) -> Dict[str, Any]:
    """Validate a character pack directory using tools validator script.

    Args:
        pack_dir: Directory to validate.
        repo_root: Repository root containing validation tools.

    Returns:
        Dict with keys: output, errors, exit_code, success.
    """
    if repo_root is None:
        repo_root = Path.cwd()

    validator = _resolve_validator(repo_root)
    if not validator:
        return {
            "output": "",
            "errors": "Validator not found. Expected tools/validate_pack.py or tools/validation/validate_pack.py",
            "exit_code": 1,
            "success": False,
        }

    try:
        result = subprocess.run(
            [sys.executable, str(validator), str(pack_dir)],
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
