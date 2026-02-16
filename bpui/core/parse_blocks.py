"""Strict codeblock parser for blueprint outputs."""

import re
from pathlib import Path
from typing import Optional, Dict, List, TYPE_CHECKING
from bpui.utils.profiler import profile

if TYPE_CHECKING:
    from .templates import Template


# Ordered asset names as they appear in output
ASSET_ORDER = [
    "system_prompt",
    "post_history",
    "character_sheet",
    "intro_scene",
    "intro_page",
    "a1111",
    "suno",
]

# Default filename mapping (can be overridden by templates)
DEFAULT_ASSET_FILENAMES = {
    "system_prompt": "system_prompt.txt",
    "post_history": "post_history.txt",
    "character_sheet": "character_sheet.txt",
    "intro_scene": "intro_scene.txt",
    "intro_page": "intro_page.md",
    "a1111": "a1111_prompt.txt",
    "suno": "suno_prompt.txt",
}

# Legacy alias for backward compatibility
ASSET_FILENAMES = DEFAULT_ASSET_FILENAMES


def get_asset_filename(asset_name: str, template: Optional['Template'] = None) -> str:
    """Get filename for an asset, considering template-specific overrides.
    
    Args:
        asset_name: Name of the asset
        template: Optional template with custom filename mapping
        
    Returns:
        Filename for the asset (e.g., 'system_prompt.txt')
    """
    # Check template for custom filename
    if template:
        for asset in template.assets:
            if asset.name == asset_name:
                # If blueprint_file is specified, use it as base for filename
                if asset.blueprint_file:
                    # Extract just the filename (basename) from path
                    blueprint_path = Path(asset.blueprint_file)
                    filename = blueprint_path.name
                    
                    # Keep .md extension if present, otherwise assume .txt
                    if filename.endswith('.md'):
                        return filename
                    elif filename.endswith('.txt'):
                        return filename
                    else:
                        # Blueprint file without extension, add .txt
                        return filename if '.' in filename else f"{filename}.txt"
                break
    
    # Fall back to default mapping
    if asset_name in DEFAULT_ASSET_FILENAMES:
        return DEFAULT_ASSET_FILENAMES[asset_name]
    
    # Generic fallback: asset_name.txt
    return f"{asset_name}.txt"


class ParseError(Exception):
    """Parse error."""
    pass


def extract_codeblocks(text: str) -> List[str]:
    """Extract all fenced codeblocks from text.

    Args:
        text: LLM output

    Returns:
        List of codeblock contents (without fence markers)
    
    Note:
        This parser uses a simple regex pattern that does NOT handle nested codeblocks
        (e.g., markdown codeblocks inside LLM-generated codeblocks). In the unlikely
        event that an LLM generates nested codeblocks, parsing will extract the
        outer codeblock content only. This is acceptable for the intended use case
        where LLMs generate simple, flat codeblock structures.
    """
    # Match ```...``` blocks (handles language tags)
    pattern = r"```(?:[a-z]*\n)?(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [m.strip() for m in matches]


def parse_blueprint_output(text: str, template: Optional['Template'] = None) -> Dict[str, str]:
    """Parse blueprint orchestrator output into assets.

    Args:
        text: LLM output containing codeblocks
        template: Optional template defining expected assets (uses official 7-asset if None)

    Returns:
        Dict mapping asset names to content

    Raises:
        ParseError: If output doesn't match expected structure
    """
    with profile("parse_blueprint_output", input_length=len(text)):
        blocks = extract_codeblocks(text)

        if len(blocks) == 0:
            raise ParseError("No codeblocks found in output")

        # Check for optional Adjustment Note
        start_idx = 0
        adjustment_note = None

        if blocks[0].strip().startswith("Adjustment Note:"):
            adjustment_note = blocks[0].strip()
            start_idx = 1

        asset_blocks = blocks[start_idx:]
        
        # Determine expected asset order from template or use default
        if not template:
            from bpui.features.templates.templates import TemplateManager
            manager = TemplateManager()
            template = manager.get_template("Official RPBotGenerator")
        
        if template:
            from .topological_sort import topological_sort
            try:
                expected_assets = topological_sort(template.assets)
            except ValueError:
                expected_assets = [asset.name for asset in template.assets]
            expected_count = len(expected_assets)
            template_name = template.name
        else:
            raise ParseError("Could not determine expected assets: No template provided and default not found.")

        # Validate asset count
        if len(asset_blocks) != expected_count:
            # Include preview of blocks for debugging
            block_previews = "\n".join(
                f"  Block {i}: {b[:75]}{'...' if len(b) > 75 else ''}"
                for i, b in enumerate(asset_blocks[:3])
            )
            if len(asset_blocks) > 3:
                block_previews += f"\n  ... and {len(asset_blocks) - 3} more blocks"
            
            raise ParseError(
                f"Template '{template_name}' expects {expected_count} asset blocks, found {len(asset_blocks)}. "
                f"Required order: {', '.join(expected_assets)}\n"
                f"Actual blocks found:\n{block_previews}"
            )

        # Map blocks to asset names
        assets = {}
        for i, asset_name in enumerate(expected_assets):
            assets[asset_name] = asset_blocks[i]

        return assets


def extract_single_asset(output: str, asset_name: str) -> str:
    """Extract a single asset from LLM output.

    Args:
        output: Raw LLM output (may contain adjustment note + codeblock)
        asset_name: Name of the asset to extract

    Returns:
        Asset content (text inside the codeblock)

    Raises:
        ParseError: If parsing fails
    """
    blocks = extract_codeblocks(output)

    if not blocks:
        raise ParseError(f"No codeblocks found for {asset_name}")

    # Check for adjustment note
    start_idx = 0
    if blocks[0].strip().startswith("Adjustment Note:"):
        start_idx = 1

    asset_blocks = blocks[start_idx:]
    if not asset_blocks:
        raise ParseError(f"No asset block found for {asset_name}")

    # Return the first (and should be only) asset block
    return asset_blocks[0]


def extract_character_name(character_sheet: str) -> Optional[str]:
    """Extract character name from character sheet.

    Args:
        character_sheet: Character sheet content

    Returns:
        Sanitized character name or None
    """
    # Look for "name: ..." line
    match = re.search(r"^name:\s*(.+)$", character_sheet, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None

    name = match.group(1).strip()
    # Sanitize using same logic as export script
    sanitized = re.sub(r"[^a-z0-9]+", "_", name.lower())
    sanitized = re.sub(r"_+", "_", sanitized)
    sanitized = sanitized.strip("_")
    return sanitized
