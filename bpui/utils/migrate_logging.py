"""Migration script for converting print() to logging.

Run this to migrate remaining print() statements to structured logging.
"""

import re
from pathlib import Path


def migrate_file(file_path: Path) -> int:
    """Migrate print statements in a file to logging.
    
    Returns:
        Number of print statements migrated
    """
    content = file_path.read_text(encoding='utf-8')
    original = content
    
    # Add logger import if not present
    if "from .logging_config import get_logger" not in content and "logger = logging.getLogger" not in content:
        # Find first import block
        lines = content.split("\n")
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_idx = i + 1
            elif insert_idx > 0 and not line.strip().startswith(("import", "from", "#")):
                break
        
        lines.insert(insert_idx, "import logging")
        content = "\n".join(lines)
    
    # Add logger instance at module level if not present
    if "logger = logging.getLogger(__name__)" not in content:
        # Find first function def
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("def ") or line.startswith("class "):
                lines.insert(i, "\nlogger = logging.getLogger(__name__)\n")
                break
        content = "\n".join(lines)
    
    # Migrate print statements
    migrations = 0
    
    # Pattern: print(f"...")
    pattern1 = r'print\(f"([^"]+)"\)'
    matches = list(re.finditer(pattern1, content))
    for match in reversed(matches):
        text = match.group(1)
        # Convert f-string to % formatting
        log_text = text.replace("{", "%(").replace("}", ")s")
        
        # Determine log level based on content
        if any(x in text.lower() for x in ["error", "✗", "failed", "exception"]):
            level = "error"
        elif any(x in text.lower() for x in ["warning", "⚠"]):
            level = "warning"
        elif any(x in text.lower() for x in ["debug", "→"]):
            level = "debug"
        else:
            level = "info"
        
        replacement = f'logger.{level}("{log_text}")'
        content = content[:match.start()] + replacement + content[match.end():]
        migrations += 1
    
    # Pattern: print("...")
    pattern2 = r'print\("([^"]+)"\)'
    matches = list(re.finditer(pattern2, content))
    for match in reversed(matches):
        text = match.group(1)
        
        # Determine log level
        if any(x in text.lower() for x in ["error", "✗", "failed"]):
            level = "error"
        elif any(x in text.lower() for x in ["warning", "⚠"]):
            level = "warning"
        else:
            level = "info"
        
        replacement = f'logger.{level}("{text}")'
        content = content[:match.start()] + replacement + content[match.end():]
        migrations += 1
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
    
    return migrations


def main():
    """Run migration on bpui package."""
    bpui_dir = Path(__file__).parent
    
    total_migrations = 0
    files_modified = 0
    
    for py_file in bpui_dir.rglob("*.py"):
        if "test" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        migrations = migrate_file(py_file)
        if migrations > 0:
            print(f"✓ {py_file.relative_to(bpui_dir.parent)}: {migrations} migrations")
            total_migrations += migrations
            files_modified += 1
    
    print(f"\nTotal: {total_migrations} print statements migrated in {files_modified} files")


if __name__ == "__main__":
    main()
