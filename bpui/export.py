"""Export wrapper for tools/export_character.sh."""

import subprocess
from pathlib import Path
from typing import Dict, Optional, Any


def export_character(
    character_name: str,
    source_dir: Path,
    model: Optional[str] = None,
    repo_root: Optional[Path] = None
) -> Dict[str, Any]:
    """Export character using the export script.

    Args:
        character_name: Character name
        source_dir: Directory containing pack files
        model: Optional model name for output directory
        repo_root: Repository root path

    Returns:
        Dict with export results:
            - success: bool
            - output: str (stdout)
            - errors: str (stderr)
            - exit_code: int
            - output_dir: Optional[Path] (if successful)
    """
    if repo_root is None:
        repo_root = Path.cwd()

    export_script = repo_root / "tools" / "export_character.sh"
    if not export_script.exists():
        return {
            "success": False,
            "output": "",
            "errors": f"Export script not found: {export_script}",
            "exit_code": 1,
            "output_dir": None,
        }

    # Build command
    cmd = [str(export_script), character_name, str(source_dir)]
    if model:
        cmd.append(model)

    try:
        result = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Parse output directory from stdout if successful
        output_dir = None
        if result.returncode == 0:
            # Look for "exported to <path>/" in output
            for line in result.stdout.split("\n"):
                if "exported to" in line.lower():
                    # Extract path
                    parts = line.split("to")
                    if len(parts) > 1:
                        path_str = parts[1].strip().rstrip("/")
                        output_dir = repo_root / path_str

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "exit_code": result.returncode,
            "output_dir": output_dir,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "errors": "Export timed out after 30 seconds",
            "exit_code": 124,
            "output_dir": None,
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "errors": str(e),
            "exit_code": 1,
            "output_dir": None,
        }
