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
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


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


PLACEHOLDER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("{PLACEHOLDER}", re.compile(r"\{PLACEHOLDER\}")),
    ("Suno {TITLE}", re.compile(r"\{TITLE\}")),
    ("Suno other {..}", re.compile(r"\{GENRE\}|\{STYLE\}|\{MOOD\}|\{ENERGY\}|\{TEMPO\}|\{BPM\}|\{TEXTURE\}|\{Remaster Style\}")),
    ("A1111 slot ((...))", re.compile(r"\(\(\.\.\.\)\)")),
    ("A1111 any slot ((...something...)) left", re.compile(r"\(\([^\)]*\.\.\.[^\)]*\)\)")),
    ("Character sheet bracket placeholders", re.compile(r"\[[^\]]+\]")),
]


A1111_CONTENT_RE = re.compile(r"^\[Content:\s*(SFW|NSFW)\]\s*$", re.MULTILINE)


@dataclass
class Finding:
    path: Path
    message: str


def iter_files(base_dir: Path) -> Iterable[Path]:
    for rel in REQUIRED_FILES + OPTIONAL_FILES:
        p = base_dir / rel
        if p.exists():
            yield p


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def validate_required_files(base_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for rel in REQUIRED_FILES:
        p = base_dir / rel
        if not p.is_file():
            findings.append(Finding(p, f"Missing required file: {rel}"))
    return findings


def validate_placeholders(base_dir: Path) -> list[Finding]:
    findings: list[Finding] = []

    # Character sheet is allowed to contain brackets in some normal prose, but in this
    # repo brackets are used as blueprint placeholders. We keep the check strict.
    for file_path in iter_files(base_dir):
        text = read_text(file_path)

        for label, pattern in PLACEHOLDER_PATTERNS:
            if label == "Character sheet bracket placeholders" and file_path.name != "character_sheet.txt":
                continue

            if pattern.search(text):
                findings.append(Finding(file_path, f"Found placeholder pattern: {label}"))
                break

    return findings


def detect_a1111_mode(text: str) -> str | None:
    m = A1111_CONTENT_RE.search(text)
    if not m:
        return None
    return m.group(1)


def validate_a1111_mode(base_dir: Path) -> list[Finding]:
    findings: list[Finding] = []

    a1111_path = base_dir / "a1111_prompt.txt"
    if not a1111_path.exists():
        return findings

    mode = detect_a1111_mode(read_text(a1111_path))
    if mode is None:
        findings.append(Finding(a1111_path, "Missing [Content: SFW|NSFW] line"))
        return findings

    sdxl_path = base_dir / "a1111_sdxl_prompt.txt"
    if sdxl_path.exists():
        sdxl_mode = detect_a1111_mode(read_text(sdxl_path))
        if sdxl_mode is None:
            findings.append(Finding(sdxl_path, "Missing [Content: SFW|NSFW] line"))
        elif sdxl_mode != mode:
            findings.append(
                Finding(
                    sdxl_path,
                    f"Content mode mismatch vs a1111_prompt.txt (expected {mode}, found {sdxl_mode})",
                )
            )

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
        findings.extend(validate_a1111_mode(base_dir))

    if findings:
        print("VALIDATION FAILED")
        for f in findings:
            print(f"- {f.path}: {f.message}")
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
