"""Strict codeblock parser for blueprint outputs."""

import re
from typing import Optional, Dict, List
from .profiler import profile


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

# Filename mapping
ASSET_FILENAMES = {
    "system_prompt": "system_prompt.txt",
    "post_history": "post_history.txt",
    "character_sheet": "character_sheet.txt",
    "intro_scene": "intro_scene.txt",
    "intro_page": "intro_page.md",
    "a1111": "a1111_prompt.txt",
    "suno": "suno_prompt.txt",
}


class ParseError(Exception):
    """Parse error."""
    pass


def extract_codeblocks(text: str) -> List[str]:
    """Extract all fenced codeblocks from text.

    Args:
        text: LLM output

    Returns:
        List of codeblock contents (without fence markers)
    """
    # Match ```...``` blocks (handles language tags)
    pattern = r"```(?:[a-z]*\n)?(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return [m.strip() for m in matches]


def parse_blueprint_output(text: str) -> Dict[str, str]:
    """Parse blueprint orchestrator output into assets.

    Args:
        text: LLM output containing codeblocks

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

    # Require exactly 7 asset blocks after adjustment note (if present)
    asset_blocks = blocks[start_idx:]
    if len(asset_blocks) != 7:
        raise ParseError(
            f"Expected 7 asset blocks, found {len(asset_blocks)}. "
            f"Required order: {', '.join(ASSET_ORDER)}"
        )

        # Map blocks to asset names
        assets = {}
        for i, asset_name in enumerate(ASSET_ORDER):
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
