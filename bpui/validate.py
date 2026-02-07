"""Validation wrapper for tools/validate_pack.py."""

import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Any


VALIDATION_TIMEOUT = int(os.getenv("BPUI_VALIDATION_TIMEOUT", "30"))


def validate_pack(pack_dir: Path, repo_root: Optional[Path] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
    """Validate a pack directory.

    Args:
        pack_dir: Directory containing pack files
        repo_root: Repository root path
        timeout: Timeout in seconds (uses BPUI_VALIDATION_TIMEOUT if None)

    Returns:
        Dict with validation results:
            - success: bool
            - output: str (stdout)
            - errors: str (stderr)
            - exit_code: int
    """
    if repo_root is None:
        repo_root = Path.cwd()
    
    if timeout is None:
        timeout = VALIDATION_TIMEOUT

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
            timeout=timeout,
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
            "errors": f"Validation timed out after {timeout} seconds. "
                      f"The pack may be too large or the validator may be stuck. "
                      f"Try increasing BPUI_VALIDATION_TIMEOUT environment variable.",
            "exit_code": 124,
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "errors": str(e),
            "exit_code": 1,
        }
