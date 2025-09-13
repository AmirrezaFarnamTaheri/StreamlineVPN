#!/usr/bin/env python3
"""
Import Path Standardization Script - FIXED
==========================================

Fixes all legacy vpn_merger imports to use streamline_vpn.
"""

import re
import argparse
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ImportStandardizer:
    """Standardizes import paths across the project."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.replacements = [
            # Package name replacements
            (r"from vpn_merger\.", "from streamline_vpn."),
            (r"import streamline_vpn\.", "import streamline_vpn."),
            (r"from streamline_vpn import", "from streamline_vpn import"),
            (r"import streamline_vpn", "import streamline_vpn"),
            # Legacy module paths
            (
                r"from vpn_merger\.core\.output\.manager import",
                "from streamline_vpn.core.output_manager import",
            ),
            (
                r"from vpn_merger\.core\.merger import StreamlineVPNMerger",
                "from streamline_vpn.core.merger import StreamlineVPNMerger",
            ),
            # Class name updates
            (r"StreamlineVPNMerger", "StreamlineVPNMerger"),
            (r"StreamlineVPN", "StreamlineVPN"),
            # Documentation references
            (r"streamline-vpn-web", "streamline-vpn-web"),
            (r"vpn_merger\.log", "streamline_vpn.log"),
        ]

        self.files_to_fix: List[Path] = []
        self.backup_dir = self.project_root / "import_backup"

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files: List[Path] = []

        for ext in ["*.py", "*.md", "*.html", "*.js"]:
            python_files.extend(self.project_root.rglob(ext))

        # Exclude virtual environments and build directories
        excluded_dirs = [
            "venv", ".venv", "env", "build", "dist", "__pycache__",
            "import_backup", ".git", "node_modules"
        ]

        filtered_files: List[Path] = []
        for file in python_files:
            if not any(excluded in file.parts for excluded in excluded_dirs):
                filtered_files.append(file)

        return filtered_files

    def check_file(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """Check a file for import issues."""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for pattern, replacement in self.replacements:
                    if re.search(pattern, line):
                        issues.append((line_num, line.strip(), f"Replace: {pattern}"))

        except Exception as e:
            print(f"Error checking {file_path}: {e}")

        return issues

    def fix_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """Fix import issues in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            for pattern, replacement in self.replacements:
                content = re.sub(pattern, replacement, content)

            if content != original_content:
                if not dry_run:
                    # Create backup
                    self.backup_dir.mkdir(exist_ok=True)
                    backup_path = self.backup_dir / f"{file_path.name}.bak"
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)

                    # Write fixed content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                print(f"{'[DRY RUN] ' if dry_run else ''}Fixed: {file_path}")
                return True

        except Exception as e:
            print(f"Error fixing {file_path}: {e}")

        return False

    def run_analysis(self) -> Dict[str, Any]:
        """Run analysis without making changes."""
        files = self.find_python_files()
        report = {
            "total_files": len(files),
            "files_with_issues": 0,
            "total_issues": 0,
            "issues_by_file": {}
        }

        for file_path in files:
            issues = self.check_file(file_path)
            if issues:
                report["files_with_issues"] += 1
                report["total_issues"] += len(issues)
                report["issues_by_file"][str(file_path)] = issues

        return report

    def run_fix(self, dry_run: bool = False) -> Dict[str, Any]:
        """Fix all import issues."""
        files = self.find_python_files()
        result = {
            "total_files": len(files),
            "fixed_files": 0
        }

        for file_path in files:
            if self.fix_file(file_path, dry_run):
                result["fixed_files"] += 1

        return result

    def restore_backups(self) -> None:
        """Restore files from backup."""
        if not self.backup_dir.exists():
            print("No backup directory found")
            return

        for backup_file in self.backup_dir.glob("*.bak"):
            original_name = backup_file.name.replace(".bak", "")
            original_files = list(self.project_root.rglob(original_name))

            if original_files:
                original_path = original_files[0]
                with open(backup_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(original_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Restored: {original_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Standardize import paths in StreamlineVPN project"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze files without making changes",
    )
    parser.add_argument("--fix", action="store_true", help="Fix import issues")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes",
    )
    parser.add_argument(
        "--restore", action="store_true", help="Restore files from backup"
    )
    parser.add_argument("--root", default=".", help="Project root directory")

    args = parser.parse_args()

    standardizer = ImportStandardizer(args.root)

    if args.restore:
        standardizer.restore_backups()
    elif args.analyze:
        report = standardizer.run_analysis()
        print("\n=== Import Analysis Report ===")
        print(f'Total files: {report["total_files"]}')
        print(f'Files with issues: {report["files_with_issues"]}')
        print(f'Total issues: {report["total_issues"]}')

        if report["issues_by_file"]:
            print("\n=== Issues by File ===")
            for file_path, issues in list(report["issues_by_file"].items())[:5]:
                print(f"\n{file_path}:")
                for line_num, line, issue_type in issues[:3]:
                    print(f"  Line {line_num}: {issue_type}")
                    print(f"    {line.strip()}")
                if len(issues) > 3:
                    print(f"  ... and {len(issues) - 3} more issues")
    elif args.fix or args.dry_run:
        result = standardizer.run_fix(dry_run=args.dry_run)
        print(f"\n=== {'Dry Run' if args.dry_run else 'Fix'} Complete ===")
        print(f"Total files: {result['total_files']}")
        print(
            f"{'Would fix' if args.dry_run else 'Fixed'}: {result['fixed_files']} files"
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
