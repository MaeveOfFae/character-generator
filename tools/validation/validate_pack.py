#!/usr/bin/env python3

"""Validate a generated Blueprint Pack directory.

This script is intentionally heuristic: it is meant to catch the most common
workspace-breaking failures (missing files, leftover placeholders, mode
inconsistencies) without requiring external dependencies.

Usage:
  python tools/validate_pack.py path/to/dir

Exit codes:
  0 = ok
  1 = validation failed
  2 = invalid invocation
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from bpui.core.content_validation import validate_file_content


REQUIRED_FILES = [
    "system_prompt.txt",
    "post_history.txt",
    "character_sheet.txt",
    "intro_scene.txt",
    "intro_page.md",
    "a1111_prompt.txt",
    "suno_prompt.txt",
]

OPTIONAL_FILES = [
    "a1111_sdxl_prompt.txt",
]


@dataclass
class Finding:
    path: Path
    message: str


def iter_files(base_dir: Path) -> Iterable[Path]:
    for rel in REQUIRED_FILES + OPTIONAL_FILES:
        p = base_dir / rel
        if p.exists():
            yield p


def validate_required_files(base_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel in REQUIRED_FILES:
        p = base_dir / rel
        if not p.is_file():
            findings.append(Finding(p, f"Missing required file: {rel}"))
    return findings


def validate_placeholders(base_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for file_path in iter_files(base_dir):
        labels = validate_file_content(file_path)
        for label in sorted(set(labels)):
            findings.append(Finding(file_path, f"Found validation issue: {label}"))

    return findings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate a Blueprint Pack output directory")
    parser.add_argument("dir", help="Directory containing exported pack files")
    args = parser.parse_args(argv)

    base_dir = Path(args.dir).expanduser().resolve()
    if not base_dir.is_dir():
        print(f"ERROR: Not a directory: {base_dir}")
        return 2

    findings: list[Finding] = []
    findings.extend(validate_required_files(base_dir))
    # Only run content checks if the required set exists.
    if not any(f.message.startswith("Missing required file") for f in findings):
        findings.extend(validate_placeholders(base_dir))
        # Note: validate_a1111_mode removed - [Content: SFW|NSFW] is now optional

    if findings:
        print("VALIDATION FAILED")
        for f in findings:
            print(f"- {f.path}: {f.message}")
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
