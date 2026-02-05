"""Export wrapper for tools/export_character.sh."""

import subprocess
from pathlib import Path
from typing import Dict, Optional, Any


def export_character(
    character_name: str,
    source_dir: Path,
    model: Optional[str] = None,
    repo_root: Optional[Path] = None,
    preset_name: Optional[str] = None
) -> Dict[str, Any]:
    """Export character using the export script or a preset.

    Args:
        character_name: Character name
        source_dir: Directory containing pack files
        model: Optional model name for output directory
        repo_root: Repository root path
        preset_name: Optional preset name (e.g., "chubai", "tavernai")

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

    # If preset specified, use preset-based export
    if preset_name:
        return export_with_preset(
            character_name=character_name,
            source_dir=source_dir,
            preset_name=preset_name,
            model=model,
            repo_root=repo_root
        )

    # Otherwise use traditional export script
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


def export_with_preset(
    character_name: str,
    source_dir: Path,
    preset_name: str,
    model: Optional[str] = None,
    repo_root: Optional[Path] = None
) -> Dict[str, Any]:
    """Export character using an export preset.

    Args:
        character_name: Character name
        source_dir: Directory containing pack files
        preset_name: Preset name or path to preset file
        model: Optional model name
        repo_root: Repository root path

    Returns:
        Dict with export results (same format as export_character)
    """
    if repo_root is None:
        repo_root = Path.cwd()

    try:
        from .export_presets import load_preset, apply_preset, format_output, validate_preset
        from .pack_io import load_draft

        # Load preset
        preset_path = repo_root / "presets" / f"{preset_name}.toml"
        if not preset_path.exists():
            # Try as direct path
            preset_path = Path(preset_name)
        
        if not preset_path.exists():
            return {
                "success": False,
                "output": "",
                "errors": f"Preset not found: {preset_name}",
                "exit_code": 1,
                "output_dir": None,
            }

        preset = load_preset(preset_path)
        if not preset:
            return {
                "success": False,
                "output": "",
                "errors": f"Failed to load preset: {preset_name}",
                "exit_code": 1,
                "output_dir": None,
            }

        # Validate preset
        is_valid, errors = validate_preset(preset)
        if not is_valid:
            return {
                "success": False,
                "output": "",
                "errors": f"Invalid preset: {', '.join(errors)}",
                "exit_code": 1,
                "output_dir": None,
            }

        # Load assets
        assets = load_draft(source_dir)
        if not assets:
            return {
                "success": False,
                "output": "",
                "errors": f"No assets found in {source_dir}",
                "exit_code": 1,
                "output_dir": None,
            }

        # Apply preset
        export_data = apply_preset(assets, preset, character_name)

        # Format and save output
        output_dir = repo_root / "output"
        output_path = format_output(
            data=export_data,
            preset=preset,
            output_dir=output_dir,
            character_name=character_name,
            model=model or "unknown"
        )

        return {
            "success": True,
            "output": f"✓ Exported to {output_path} using {preset.name} preset",
            "errors": "",
            "exit_code": 0,
            "output_dir": output_path,
        }

    except Exception as e:
        return {
            "success": False,
            "output": "",
            "errors": f"Export failed: {str(e)}",
            "exit_code": 1,
            "output_dir": None,
        }
