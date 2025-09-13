#!/usr/bin/env python3
"""
Enhanced Import Path Standardization Script
===========================================

Fixes all legacy vpn_merger imports to use streamline_vpn consistently.
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ImportStandardizer:
    """Enhanced standardizer for import paths across the project."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.replacements = [
            # Primary package name replacements
            (r"from vpn_merger\.", "from streamline_vpn."),
            (r"import vpn_merger\.", "import streamline_vpn."),
            (r"from vpn_merger import", "from streamline_vpn import"),
            (r"import vpn_merger", "import streamline_vpn"),
            
            # Specific legacy module paths that need updating
            (r"from vpn_merger\.core\.output\.manager", "from streamline_vpn.core.output_manager"),
            (
                r"from vpn_merger\.core\.merger import VPNSubscriptionMerger",
                "from streamline_vpn.core.merger import StreamlineVPNMerger",
            ),
            
            # Class name standardization
            (r"VPNSubscriptionMerger", "StreamlineVPNMerger"),
            (r"CleanConfigs-SubMerger", "StreamlineVPN"),
            
            # Remove outdated try/except import fallbacks
            (
                r"try:\s*from streamline_vpn\.core\.output_manager.*?\nexcept ImportError:.*?from streamline_vpn\.core\.output\.manager.*?\n",
                "from streamline_vpn.core.output_manager import OutputManager\n",
            ),
            
            # Documentation and comment references
            (r"vpn_merger_main\.py", "streamline_vpn_main.py"),
            (r"python -m vpn_merger", "python -m streamline_vpn"),
            (r"VPN_MERGER_", "STREAMLINE_"),
        ]

        self.files_to_fix: List[Path] = []
        self.backup_dir = self.project_root / "import_backup"

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project, excluding virtual environments."""
        python_files: List[Path] = []
        
        # Include both .py files and common config files
        for pattern in ["*.py", "*.yml", "*.yaml", "*.md", "*.txt"]:
            python_files.extend(self.project_root.rglob(pattern))

        # Exclude directories that shouldn't be modified
        excluded_dirs = {
            "venv", ".venv", "env", "build", "dist", "__pycache__",
            "import_backup", ".git", "node_modules", ".pytest_cache"
        }

        filtered_files = []
        for file in python_files:
            if not any(excluded in file.parts for excluded in excluded_dirs):
                filtered_files.append(file)

        return filtered_files

    def check_file(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """Check a file for import issues and return list of (line_number, old, new)."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            # Skip binary files or files we can't read
            return issues
            
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for old_pattern, new_replacement in self.replacements:
                if re.search(old_pattern, line):
                    new_line = re.sub(old_pattern, new_replacement, line)
                    if new_line != line:
                        issues.append((i, line.strip(), new_line.strip()))
        
        return issues

    def fix_file(self, file_path: Path) -> bool:
        """Fix import issues in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            return False

        # Create backup
        if self.backup_dir:
            backup_file = self.backup_dir / file_path.relative_to(self.project_root)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)

        # Apply all replacements
        modified = False
        new_content = content
        
        for old_pattern, new_replacement in self.replacements:
            old_content = new_content
            new_content = re.sub(old_pattern, new_replacement, new_content)
            if old_content != new_content:
                modified = True

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
            
        return False

    def run_analysis(self) -> Dict[str, Any]:
        """Run analysis to find all import issues."""
        print("Analyzing files for import issues...")

        python_files = self.find_python_files()
        print(f"Found {len(python_files)} files to analyze")

        all_issues: Dict[str, List[Tuple[int, str, str]]] = {}

        for file_path in python_files:
            issues = self.check_file(file_path)
            if issues:
                all_issues[str(file_path)] = issues

        return {
            "total_files": len(python_files),
            "files_with_issues": len(all_issues),
            "total_issues": sum(len(issues) for issues in all_issues.values()),
            "issues_by_file": all_issues,
        }

    def run_fix(self, dry_run: bool = False) -> Dict[str, Any]:
        """Fix all import issues."""
        print(f"{'[DRY RUN] ' if dry_run else ''}Fixing import issues...")

        if not dry_run:
            self.backup_dir.mkdir(exist_ok=True)

        python_files = self.find_python_files()
        fixed_files = []

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


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Standardize import paths in StreamlineVPN project")
    parser.add_argument("--analyze", action="store_true", help="Analyze files for issues")
    parser.add_argument("--fix", action="store_true", help="Fix import issues")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without making changes")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    
    args = parser.parse_args()
    
    standardizer = ImportStandardizer(args.project_root)
    
    if args.analyze or (not args.fix and not args.dry_run):
        # Default to analysis if no specific action specified
        report = standardizer.run_analysis()
        print(f"\nAnalysis Results:")
        print(f"Total files: {report['total_files']}")
        print(f"Files with issues: {report['files_with_issues']}")
        print(f"Total issues: {report['total_issues']}")
        
        if report['issues_by_file']:
            print(f"\nFiles requiring fixes:")
            for file_path, issues in report['issues_by_file'].items():
                print(f"  {file_path}: {len(issues)} issues")
                for line_num, old_line, new_line in issues[:3]:  # Show first 3 issues
                    print(f"    Line {line_num}: {old_line} -> {new_line}")
                if len(issues) > 3:
                    print(f"    ... and {len(issues) - 3} more issues")
    
    if args.fix or args.dry_run:
        result = standardizer.run_fix(dry_run=args.dry_run)
        print(f"\nFix Results ({result['mode']}):")
        print(f"Total files processed: {result['total_files']}")
        print(f"Files {'that would be ' if args.dry_run else ''}fixed: {result['fixed_files']}")
        
        if result['files']:
            print(f"\nFixed files:")
            for file_path in result['files'][:10]:  # Show first 10
                print(f"  {file_path}")
            if len(result['files']) > 10:
                print(f"  ... and {len(result['files']) - 10} more files")


if __name__ == "__main__":
    main()

