#!/usr/bin/env python3
"""
Import Path Standardization Script
===================================

Fixes all legacy vpn_merger imports to use streamline_vpn.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ImportStandardizer:
    """Standardizes import paths across the project."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.replacements = [
            # Package name replacements
            (r"from vpn_merger\.", "from streamline_vpn."),
            (r"import vpn_merger\.", "import streamline_vpn."),
            (r"from vpn_merger import", "from streamline_vpn import"),
            (r"import vpn_merger", "import streamline_vpn"),
            # Legacy module paths
            (
                r"from vpn_merger\.core\.output\.manager import",
                "from streamline_vpn.core.output_manager import",
            ),
            (
                r"from vpn_merger\.core\.merger import VPNSubscriptionMerger",
                "from streamline_vpn.core.merger import StreamlineVPNMerger",
            ),
            # Class name updates
            (r"VPNSubscriptionMerger", "StreamlineVPNMerger"),
            (r"CleanConfigs-SubMerger", "StreamlineVPN"),
            # Remove try/except import fallbacks
            (
                r"try:\s*from streamline_vpn\.core\.output_manager.*?\nexcept ImportError:.*?from streamline_vpn\.core\.output\.manager.*?\n",
                "from streamline_vpn.core.output_manager import OutputManager\n",
            ),
        ]

        self.files_to_fix: List[Path] = []
        self.backup_dir = self.project_root / "import_backup"

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files: List[Path] = []

        for ext in ["*.py"]:
            python_files.extend(self.project_root.rglob(ext))

        # Exclude virtual environments and build directories
        excluded_dirs = [
            "venv",
            ".venv",
            "env",
            "build",
            "dist",
            "__pycache__",
            "import_backup",
        ]

        filtered_files: List[Path] = []
        for file in python_files:
            if not any(excluded in file.parts for excluded in excluded_dirs):
                filtered_files.append(file)

        return filtered_files

    def check_file(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """Check a file for import issues."""
        issues: List[Tuple[int, str, str]] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                # Check for vpn_merger imports
                if "vpn_merger" in line:
                    issues.append((i, line, "Legacy vpn_merger import"))

                # Check for try/except import patterns
                if "try:" in line and i < len(lines) - 2:
                    if (
                        "import" in lines[i]
                        and "except ImportError" in lines[i + 1]
                    ):
                        issues.append((i, line, "Try/except import fallback"))

                # Check for old class names
                if "VPNSubscriptionMerger" in line:
                    issues.append((i, line, "Legacy class name"))

        except Exception as e:  # pylint: disable=broad-except
            print(f"Error checking {file_path}: {e}")

        return issues

    def fix_file(self, file_path: Path) -> bool:
        """Fix import issues in a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            for pattern, replacement in self.replacements:
                content = re.sub(
                    pattern, replacement, content, flags=re.MULTILINE
                )

            if content != original_content:
                backup_path = self.backup_dir / file_path.relative_to(
                    self.project_root
                )
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(original_content)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                return True

            return False

        except Exception as e:  # pylint: disable=broad-except
            print(f"Error fixing {file_path}: {e}")
            return False

    def run_analysis(self) -> Dict[str, Any]:
        """Run analysis without making changes."""
        print("Analyzing Python files for import issues...")

        python_files = self.find_python_files()
        print(f"Found {len(python_files)} Python files")

        all_issues: Dict[str, List[Tuple[int, str, str]]] = {}

        for file_path in python_files:
            issues = self.check_file(file_path)
            if issues:
                all_issues[str(file_path)] = issues

        report: Dict[str, Any] = {
            "total_files": len(python_files),
            "files_with_issues": len(all_issues),
            "total_issues": sum(len(issues) for issues in all_issues.values()),
            "issues_by_file": all_issues,
        }

        return report

    def run_fix(self, dry_run: bool = False) -> Dict[str, Any]:
        """Fix all import issues."""
        print(f"{'[DRY RUN] ' if dry_run else ''}Fixing import issues...")

        if not dry_run:
            self.backup_dir.mkdir(exist_ok=True)

        python_files = self.find_python_files()
        fixed_files: List[str] = []

        for file_path in python_files:
            issues = self.check_file(file_path)
            if issues:
                if dry_run:
                    print(f"Would fix: {file_path} ({len(issues)} issues)")
                    fixed_files.append(str(file_path))
                else:
                    if self.fix_file(file_path):
                        print(f"Fixed: {file_path}")
                        fixed_files.append(str(file_path))

        return {
            "mode": "dry_run" if dry_run else "fixed",
            "total_files": len(python_files),
            "fixed_files": len(fixed_files),
            "files": fixed_files,
        }

    def restore_backups(self) -> None:
        """Restore files from backup."""
        if not self.backup_dir.exists():
            print("No backup directory found")
            return

        backup_files = list(self.backup_dir.rglob("*.py"))

        for backup_file in backup_files:
            original_path = self.project_root / backup_file.relative_to(
                self.backup_dir
            )

            with open(backup_file, "r", encoding="utf-8") as f:
                content = f.read()

            with open(original_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"Restored: {original_path}")

        print(f"Restored {len(backup_files)} files")


def main() -> None:
    """Main entry point."""
    import argparse

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
            for file_path, issues in report["issues_by_file"].items():
                print(f"\n{file_path}:")
                for line_num, line, issue_type in issues[
                    :3
                ]:  # Show first 3 issues
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
