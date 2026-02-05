"""Export preset management for Blueprint UI."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore


@dataclass
class FieldMapping:
    """Mapping of an asset to a target field."""
    asset: str
    target: str
    wrapper: Optional[str] = None
    optional: bool = False


@dataclass
class ExportPreset:
    """Export preset configuration."""
    name: str
    format: str  # "text", "json", or "combined"
    description: str
    fields: list[FieldMapping] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    output_pattern: str = "{{character_name}}"
    
    @classmethod
    def from_dict(cls, data: dict) -> "ExportPreset":
        """Create preset from dictionary."""
        preset_data = data.get("preset", {})
        
        # Parse field mappings
        fields = []
        for field_data in data.get("fields", []):
            fields.append(FieldMapping(
                asset=field_data.get("asset", ""),
                target=field_data.get("target", ""),
                wrapper=field_data.get("wrapper"),
                optional=field_data.get("optional", False)
            ))
        
        # Get output pattern
        output_data = data.get("output", {})
        output_pattern = output_data.get("filename", "{{character_name}}")
        if "directory" in output_data:
            output_pattern = output_data["directory"]
        
        return cls(
            name=preset_data.get("name", "Unknown"),
            format=preset_data.get("format", "text"),
            description=preset_data.get("description", ""),
            fields=fields,
            metadata=data.get("metadata", {}),
            output_pattern=output_pattern
        )


def load_preset(preset_path: Path) -> Optional[ExportPreset]:
    """
    Load an export preset from a TOML file.
    
    Args:
        preset_path: Path to the preset TOML file
        
    Returns:
        ExportPreset object if successful, None otherwise
    """
    if not preset_path.exists():
        return None
    
    try:
        with open(preset_path, "rb") as f:
            data = tomllib.load(f)
        return ExportPreset.from_dict(data)
    except Exception as e:
        logger.error("Error loading preset from %s: %s", preset_path, e)
        return None


def list_presets(presets_dir: Optional[Path] = None) -> list[tuple[str, Path]]:
    """
    List available export presets.
    
    Args:
        presets_dir: Directory containing preset files
        
    Returns:
        List of (preset_name, preset_path) tuples
    """
    if presets_dir is None:
        presets_dir = Path(__file__).parent.parent / "presets"
    
    if not presets_dir.exists():
        return []
    
    presets = []
    for preset_file in presets_dir.glob("*.toml"):
        preset = load_preset(preset_file)
        if preset:
            presets.append((preset.name, preset_file))
    
    return presets


def apply_preset(assets: dict[str, str], preset: ExportPreset, character_name: str) -> dict[str, Any]:
    """
    Apply an export preset to a set of assets.
    
    Args:
        assets: Dictionary of asset_name -> content
        preset: Export preset to apply
        character_name: Name of the character (for {{char}} and {{character_name}})
        
    Returns:
        Dictionary ready for export in the preset's format
    """
    result = {}
    
    # Apply metadata
    result.update(preset.metadata)
    
    # Extract character name from character_sheet if not provided
    if not character_name and "character_sheet" in assets:
        # Try to extract name from character sheet
        for line in assets["character_sheet"].split("\n")[:20]:
            if line.strip().lower().startswith("name:"):
                character_name = line.split(":", 1)[1].strip()
                break
    
    # Apply field mappings
    for mapping in preset.fields:
        content = assets.get(mapping.asset, "")
        
        # Skip if optional and missing
        if not content and mapping.optional:
            continue
        
        # Apply wrapper if specified
        if mapping.wrapper:
            content = mapping.wrapper.replace("{{content}}", content)
            content = content.replace("{{char}}", character_name or "{{char}}")
            content = content.replace("{{user}}", "{{user}}")
        
        result[mapping.target] = content
    
    # Add character name if not already present
    if "name" not in result and character_name:
        result["name"] = character_name
    
    return result


def format_output(data: dict[str, Any], preset: ExportPreset, output_dir: Path, character_name: str, model: str = "") -> Path:
    """
    Format and save export data according to preset.
    
    Args:
        data: Export data from apply_preset()
        preset: Export preset used
        output_dir: Base output directory
        character_name: Character name (for filename templates)
        model: Model name (for filename templates)
        
    Returns:
        Path to the exported file/directory
    """
    # Apply template variables to output pattern
    output_name = preset.output_pattern.replace("{{character_name}}", character_name or "character")
    output_name = output_name.replace("{{model}}", model or "unknown")
    output_name = output_name.replace("{{timestamp}}", "")
    
    # Remove any double separators
    output_name = output_name.replace("()", "").replace("__", "_")
    
    # Create output path
    output_path = output_dir / output_name
    
    if preset.format == "text":
        # Create directory with separate text files
        output_path.mkdir(parents=True, exist_ok=True)
        
        for key, value in data.items():
            # Determine file extension
            ext = ".txt"
            if key.endswith(".md"):
                ext = ""
            elif key == "intro_page" or "page" in key:
                ext = ".md"
            
            file_path = output_path / f"{key}{ext}"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(value))
        
        return output_path
    
    elif preset.format == "json":
        # Create single JSON file
        if not output_name.endswith(".json"):
            output_name += ".json"
            output_path = output_dir / output_name
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        return output_path
    
    elif preset.format == "combined":
        # Create single combined text file
        if not output_name.endswith(".txt"):
            output_name += ".txt"
            output_path = output_dir / output_name
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            for key, value in data.items():
                f.write(f"=== {key.upper()} ===\n\n")
                f.write(str(value))
                f.write("\n\n")
        
        return output_path
    
    else:
        raise ValueError(f"Unknown preset format: {preset.format}")


def validate_preset(preset: ExportPreset) -> tuple[bool, list[str]]:
    """
    Validate a preset for completeness and correctness.
    
    Args:
        preset: Export preset to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not preset.name:
        errors.append("Preset name is required")
    
    if preset.format not in ["text", "json", "combined"]:
        errors.append(f"Invalid format: {preset.format}")
    
    if not preset.fields:
        errors.append("Preset must have at least one field mapping")
    
    valid_assets = {"system_prompt", "post_history", "character_sheet", "intro_scene", "intro_page", "a1111", "suno"}
    
    for mapping in preset.fields:
        if not mapping.asset:
            errors.append("Field mapping missing asset name")
        elif mapping.asset not in valid_assets:
            errors.append(f"Invalid asset name: {mapping.asset}")
        
        if not mapping.target:
            errors.append(f"Field mapping for {mapping.asset} missing target")
    
    return (len(errors) == 0, errors)
