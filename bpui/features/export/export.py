"""Export wrapper for the shell-based character export script."""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional, Any


EXPORT_TIMEOUT = int(os.getenv("BPUI_EXPORT_TIMEOUT", "30"))


def _iter_exportable_draft_files(source_dir: Path) -> list[Path]:
    """Return top-level text/markdown asset files from a draft directory."""
    if not source_dir.exists() or not source_dir.is_dir():
        return []

    return sorted(
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix in {".txt", ".md"} and not path.name.startswith(".")
    )


def _export_raw_draft_layout(
    character_name: str,
    source_dir: Path,
    model: Optional[str],
    repo_root: Path,
) -> Dict[str, Any]:
    """Export the draft's current on-disk text/markdown layout as-is."""
    export_files = _iter_exportable_draft_files(source_dir)
    if not export_files:
        return {
            "success": False,
            "output": "",
            "errors": f"No exportable .txt or .md files found in {source_dir}",
            "exit_code": 1,
            "output_dir": None,
        }

    sanitize = lambda value: "_".join(
        "".join(ch.lower() if ch.isalnum() else "_" for ch in value).split("_")
    )
    output_name = sanitize(character_name or "character") or "character"
    if model:
        model_name = sanitize(model)
        if model_name:
            output_name = f"{output_name}({model_name})"

    output_dir = repo_root / "output" / output_name
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for file_path in export_files:
        shutil.copy2(file_path, output_dir / file_path.name)

    output_lines = [f"✓ Exported to {output_dir} using current draft layout"]
    output_lines.extend(f"  - {file_path.name}" for file_path in export_files)

    return {
        "success": True,
        "output": "\n".join(output_lines),
        "errors": "",
        "exit_code": 0,
        "output_dir": output_dir,
    }


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

    # Otherwise use traditional export script.
    # Prefer the current location under tools/generation, but keep the legacy
    # root-level tools path as a fallback for older local checkouts and tests.
    export_script = None
    for candidate in (
        repo_root / "tools" / "generation" / "export_character.sh",
        repo_root / "tools" / "export_character.sh",
    ):
        if candidate.exists():
            export_script = candidate
            break

    if export_script is None:
        return {
            "success": False,
            "output": "",
            "errors": (
                "Export script not found: "
                f"{repo_root / 'tools' / 'generation' / 'export_character.sh'}"
            ),
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
            timeout=EXPORT_TIMEOUT,
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
            "errors": f"Export timed out after {EXPORT_TIMEOUT} seconds",
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
        from .export_presets import apply_preset, format_output, load_preset, resolve_preset_path, validate_preset
        from bpui.utils.file_io.pack_io import load_draft

        # Load preset
        preset_path = resolve_preset_path(preset_name, repo_root / "presets")
        
        if not preset_path:
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

        if preset_path.stem == "raw":
            return _export_raw_draft_layout(
                character_name=character_name,
                source_dir=source_dir,
                model=model,
                repo_root=repo_root,
            )

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
