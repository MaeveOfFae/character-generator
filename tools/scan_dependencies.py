#!/usr/bin/env python3
"""Dependency security scanning script for Blueprint UI."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def check_pip_audit() -> bool:
    """Check if pip-audit is installed."""
    returncode, _, _ = run_command([sys.executable, "-m", "pip", "show", "pip-audit"])
    return returncode == 0


def install_pip_audit() -> bool:
    """Install pip-audit if not available."""
    print("Installing pip-audit...")
    returncode, stdout, stderr = run_command([sys.executable, "-m", "pip", "install", "pip-audit"])
    if returncode != 0:
        print(f"Failed to install pip-audit: {stderr}")
        return False
    print("✓ pip-audit installed successfully")
    return True


def run_pip_audit(requirements_file: Path) -> tuple[bool, str]:
    """Run pip-audit on requirements file."""
    print(f"\n{'='*60}")
    print(f"Scanning {requirements_file.name}...")
    print(f"{'='*60}\n")
    
    returncode, stdout, stderr = run_command([
        sys.executable, "-m", "pip", "audit",
        "-r", str(requirements_file),
        "--desc"
    ])
    
    return returncode == 0, stdout


def run_pip_check() -> tuple[bool, str]:
    """Run pip check for dependency conflicts."""
    print(f"\n{'='*60}")
    print("Checking for dependency conflicts...")
    print(f"{'='*60}\n")
    
    returncode, stdout, stderr = run_command([
        sys.executable, "-m", "pip", "check"
    ])
    
    return returncode == 0, stdout


def main() -> int:
    """Main entry point."""
    print("🔍 Blueprint UI Dependency Security Scanner")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    requirements_files = [
        project_root / "requirements.txt",
        project_root / "requirements-optional.txt",
    ]
    
    # Ensure pip-audit is available
    if not check_pip_audit():
        print("⚠️  pip-audit is not installed")
        response = input("Install pip-audit? (y/N): ").strip().lower()
        if response == "y":
            if not install_pip_audit():
                print("✗ Cannot proceed without pip-audit")
                return 1
        else:
            print("✗ Cannot proceed without pip-audit")
            return 1
    
    # Run pip check for conflicts
    check_ok, check_output = run_pip_check()
    if check_ok:
        print("✓ No dependency conflicts found")
    else:
        print("⚠️  Dependency conflicts detected:")
        print(check_output)
    
    # Scan each requirements file
    all_vulnerabilities = []
    for req_file in requirements_files:
        if req_file.exists():
            audit_ok, audit_output = run_pip_audit(req_file)
            
            if audit_ok:
                print("✓ No vulnerabilities found")
            else:
                print("⚠️  Vulnerabilities detected:")
                print(audit_output)
                all_vulnerabilities.append((req_file.name, audit_output))
        else:
            print(f"⊘ Skipping {req_file.name} (not found)")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}\n")
    
    if not check_ok:
        print("⚠️  Dependency conflicts were detected")
        print("   Run: pip check")
    
    if all_vulnerabilities:
        print(f"⚠️  Vulnerabilities found in {len(all_vulnerabilities)} file(s):")
        for name, _ in all_vulnerabilities:
            print(f"   • {name}")
        print("\nTo update vulnerable packages:")
        print("   pip install --upgrade <package-name>")
        print("\nFor more information, see:")
        print("   https://github.com/pypa/pip-audit")
        return 1
    else:
        print("✓ No security vulnerabilities found")
        print("✓ All dependency checks passed")
        return 0


if __name__ == "__main__":
    sys.exit(main())