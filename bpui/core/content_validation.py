"""Content validation helpers for generated assets."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


PLACEHOLDER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("{PLACEHOLDER}", re.compile(r"\{PLACEHOLDER\}")),
    ("Suno {TITLE}", re.compile(r"\{TITLE\}")),
    (
        "Suno other {..}",
        re.compile(r"\{GENRE\}|\{STYLE\}|\{MOOD\}|\{ENERGY\}|\{TEMPO\}|\{BPM\}|\{TEXTURE\}|\{Remaster Style\}"),
    ),
    ("A1111 slot ((...))", re.compile(r"\(\(\.\.\.\)\)")),
    (
        "A1111 any slot ((...something...)) left",
        re.compile(r"\(\([^\)]*\.\.\.[^\)]*\)\)"),
    ),
    (
        "Character sheet bracket placeholders",
        re.compile(r"\[(?![\"'])[A-Z][^\]]*\]"),
    ),
]


USER_AUTHORSHIP_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "Narrates {{user}} action/thought/consent",
        re.compile(
            r"\{\{user\}\}\s+(?:is|was|feels?|felt|thinks?|thought|decides?|decided|knows?|knew|"
            r"wants?|wanted|says?|said|nods?|smiles?|walks?|steps?|looks?|touches?|takes?|gives?|"
            r"allows?|consents?|agrees?|gasps?|moans?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Narrates {{user}} internal state",
        re.compile(
            r"\{\{user\}\}'s\s+(?:mind|thoughts?|feelings?|emotions?|desire|consent|decision|"
            r"reaction|actions?)\b",
            re.IGNORECASE,
        ),
    ),
]


CHARACTER_SHEET_FILENAME = "character_sheet.txt"


def detect_placeholder_issues(text: str, filename: str) -> list[str]:
    """Return placeholder-related validation issue labels for a file's content."""
    issues: list[str] = []
    for label, pattern in PLACEHOLDER_PATTERNS:
        if label == "Character sheet bracket placeholders" and filename != CHARACTER_SHEET_FILENAME:
            continue
        if pattern.search(text):
            issues.append(label)
    return issues


def detect_user_authorship_issues(text: str) -> list[str]:
    """Return user-authorship issue labels for content that narrates {{user}}."""
    issues: list[str] = []
    for label, pattern in USER_AUTHORSHIP_PATTERNS:
        if pattern.search(text):
            issues.append(label)
    return issues


def validate_asset_content(asset_name: str, content: str) -> list[str]:
    """Validate a generated asset's content and return issue labels."""
    filename = f"{asset_name}.txt"
    if asset_name == "intro_page":
        filename = "intro_page.md"
    if asset_name == "character_sheet":
        filename = CHARACTER_SHEET_FILENAME

    issues = detect_placeholder_issues(content, filename)
    issues.extend(detect_user_authorship_issues(content))
    return issues


def validate_assets_content(assets: dict[str, str]) -> dict[str, list[str]]:
    """Validate all generated assets and return {asset_name: issues} for failures."""
    failures: dict[str, list[str]] = {}
    for asset_name, content in assets.items():
        issues = validate_asset_content(asset_name, content)
        if issues:
            failures[asset_name] = issues
    return failures


def validate_file_content(path: Path) -> list[str]:
    """Validate one file on disk and return issue labels."""
    text = path.read_text(encoding="utf-8", errors="replace")
    issues = detect_placeholder_issues(text, path.name)
    issues.extend(detect_user_authorship_issues(text))
    return issues


def validate_files(paths: Iterable[Path]) -> dict[Path, list[str]]:
    """Validate multiple files on disk and return failures keyed by path."""
    failures: dict[Path, list[str]] = {}
    for path in paths:
        issues = validate_file_content(path)
        if issues:
            failures[path] = issues
    return failures
