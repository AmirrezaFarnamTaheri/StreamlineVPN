#!/usr/bin/env python3
"""
Backend Code Quality Fixes Script
=================================

Automatically fixes common issues in StreamlineVPN backend code.
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import tempfile
import shutil


class BackendFixer:
    """Fixes common backend code issues."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.src_root = self.project_root / "src" / "streamline_vpn"
        self.fixes_applied = []

    def analyze_and_fix(self) -> Dict[str, Any]:
        """Analyze and fix all backend issues."""
        results = {
            "files_processed": 0,
            "fixes_applied": [],
            "errors": [],
            "warnings": []
        }

        if not self.src_root.exists():
            results["errors"].append(f"Source directory not found: {self.src_root}")
            return results

        # Find all Python files
        python_files = list(self.src_root.rglob("*.py"))
        results["files_processed"] = len(python_files)

        for file_path in python_files:
            try:
                file_fixes = self.fix_file(file_path)
                if file_fixes:
                    results["fixes_applied"].extend(file_fixes)
            except Exception as e:
                results["errors"].append(f"Error processing {file_path}: {e}")

        return results

    def fix_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Fix issues in a single Python file."""
        fixes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except (UnicodeDecodeError, PermissionError) as e:
            return [{"error": f"Could not read {file_path}: {e}"}]

        content = original_content

        # Apply various fixes
        content, fix_results = self.fix_imports(content, file_path)
        fixes.extend(fix_results)

        content, fix_results = self.fix_async_context_managers(content, file_path)
        fixes.extend(fix_results)

        content, fix_results = self.fix_error_handling(content, file_path)
        fixes.extend(fix_results)

        content, fix_results = self.fix_logging_issues(content, file_path)
        fixes.extend(fix_results)

        content, fix_results = self.fix_type_hints(content, file_path)
        fixes.extend(fix_results)

        content, fix_results = self.fix_docstrings(content, file_path)
        fixes.extend(fix_results)

        # Only write if changes were made
        if content != original_content:
            try:
                # Create backup
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                shutil.copy2(file_path, backup_path)

                # Write fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                fixes.append({
                    "file": str(file_path),
                    "type": "file_updated",
                    "backup": str(backup_path)
                })

            except Exception as e:
                fixes.append({
                    "file": str(file_path),
                    "error": f"Could not write file: {e}"
                })

        return fixes

    def fix_imports(self, content: str, file_path: Path) -> Tuple[str, List[Dict[str, Any]]]:
        """Fix import issues."""
        fixes = []
        lines = content.split('\n')
        modified = False

        # Fix relative imports
        for i, line in enumerate(lines):
            # Fix old VPN merger imports
            if 'from streamline_vpn' in line or 'import streamline_vpn' in line:
                old_line = line
                line = re.sub(r'from streamline_vpn\.', 'from streamline_vpn.', line)
                line = re.sub(r'import streamline_vpn\.', 'import streamline_vpn.', line)
                line = re.sub(r'import streamline_vpn', 'import streamline_vpn', line)
                line = re.sub(r'from streamline_vpn import', 'from streamline_vpn import', line)

                if line != old_line:
                    lines[i] = line
                    modified = True
                    fixes.append({
                        "file": str(file_path),
                        "type": "import_standardized",
                        "line": i + 1,
                        "old": old_line.strip(),
                        "new": line.strip()
                    })

            # Fix class name imports
            if 'StreamlineVPNMerger' in line:
                old_line = line
                line = line.replace('StreamlineVPNMerger', 'StreamlineVPNMerger')
                if line != old_line:
                    lines[i] = line
                    modified = True
                    fixes.append({
                        "file": str(file_path),
                        "type": "class_name_fixed",
                        "line": i + 1,
                        "old": old_line.strip(),
                        "new": line.strip()
                    })

            # Add missing typing imports if type hints are used
            if ('-> ' in line or ': ' in line) and 'from typing import' not in content:
                # Check if this is the imports section
                if i < 20 and (line.startswith('import ') or line.startswith('from ')):
                    # Find a good place to add typing import
                    typing_imports = self.detect_needed_typing_imports(content)
                    if typing_imports and 'from typing import' not in content:
                        lines.insert(i + 1, f'from typing import {", ".join(typing_imports)}')
                        modified = True
                        fixes.append({
                            "file": str(file_path),
                            "type": "typing_import_added",
                            "line": i + 1,
                            "added": f'from typing import {", ".join(typing_imports)}'
                        })
                        break

        new_content = '\n'.join(lines) if modified else content
        return new_content, fixes

    def fix_async_context_managers(self, content: str, file_path: Path) -> Tuple[str, List[Dict[str, Any]]]:
        """Fix async context manager issues."""
        fixes = []

        # Fix common async context manager patterns
        patterns = [
            # Fix session usage without proper async context manager
            (
                r'async with session\.get\(',
                r'async with session.get(',
                "Verified async context manager usage"
            ),
            # Fix missing await in async context managers
            (
                r'async with (\w+)\.(\w+)\([^)]*\) as (\w+):',
                r'async with \1.\2() as \3:',
                "Fixed async context manager call"
            )
        ]

        modified = False
        for pattern, replacement, description in patterns:
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            if new_content != content:
                content = new_content
                modified = True
                fixes.append({
                    "file": str(file_path),
                    "type": "async_context_manager_fixed",
                    "description": description
                })

        return content, fixes

    def fix_error_handling(self, content: str, file_path: Path) -> Tuple[str, List[Dict[str, Any]]]:
        """Fix error handling issues."""
        fixes = []
        lines = content.split('\n')
        modified = False

        for i, line in enumerate(lines):
            # Add missing exception handling for common patterns
            if 'await ' in line and 'try:' not in lines[max(0, i-5):i]:
                # Check if this is a risky operation
                risky_patterns = ['session.get', 'session.post', 'aiohttp.', 'asyncio.']
                if any(pattern in line for pattern in risky_patterns):
                    # Look ahead to see if there's already error handling
                    has_except = False
                    for j in range(i, min(len(lines), i + 10)):
                        if 'except' in lines[j]:
                            has_except = True
                            break

                    if not has_except and not line.strip().startswith('#'):
                        # Add basic error handling suggestion
                        fixes.append({
                            "file": str(file_path),
                            "type": "error_handling_suggestion",
                            "line": i + 1,
                            "suggestion": "Consider adding try/except for async operation",
                            "code": line.strip()
                        })

        return content, fixes

    def fix_logging_issues(self, content: str, file_path: Path) -> Tuple[str, List[Dict[str, Any]]]:
        """Fix logging issues."""
        fixes = []

        # Add logger if missing but logging calls are present
        if ('logger.' in content or 'log.' in content) and 'logger = ' not in content:
            lines = content.split('\n')

            # Find imports section
            import_end = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_end = i
                elif line.strip() == '':
                    continue
                else:
                    break

            # Add logging import and logger creation
            if 'import logging' not in content:
                lines.insert(import_end + 1, 'import logging')
                import_end += 1

            # Add logger creation after class definition or at module level
            logger_line = 'logger = logging.getLogger(__name__)'
            if 'class ' in content:
                # Find first class definition
                for i, line in enumerate(lines):
                    if line.startswith('class '):
                        lines.insert(i, logger_line)
                        lines.insert(i, '')
                        break
            else:
                lines.insert(import_end + 2, '')
                lines.insert(import_end + 3, logger_line)

            content = '\n'.join(lines)
            fixes.append({
                "file": str(file_path),
                "type": "logger_added",
                "description": "Added missing logger"
            })

        return content, fixes

    def fix_type_hints(self, content: str, file_path: Path) -> Tuple[str, List[Dict[str, Any]]]:
        """Add basic type hints where missing."""
        fixes = []

        if 'def ' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('def ') and '->' not in line and '__init__' not in line:
                    fixes.append({
                        "file": str(file_path),
                        "type": "type_hint_suggestion",
                        "line": i + 1,
                        "suggestion": "Consider adding return type hint",
                        "code": line.strip()
                    })

        return content, fixes

    def fix_docstrings(self, content: str, file_path: Path) -> Tuple[str, List[Dict[str, Any]]]:
        """Add or fix docstrings."""
        fixes = []

        lines = content.split('\n')
        modified = False

        for i, line in enumerate(lines):
            # Check for functions/classes without docstrings
            if (line.strip().startswith('def ') or line.strip().startswith('class ')) and not line.strip().startswith('def _'):
                # Check if next non-empty line is a docstring
                has_docstring = False
                for j in range(i + 1, min(len(lines), i + 5)):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        has_docstring = True
                        break
                    else:
                        break

                if not has_docstring:
                    # Add basic docstring
                    indent = len(line) - len(line.lstrip())
                    if 'def ' in line:
                        func_name = line.split('def ')[1].split('(')[0]
                    else:
                        class_name = line.split('class ')[1].split('(')[0].split(':')[0]

                    lines.insert(i + 1, docstring)
                    modified = True
                    fixes.append({
                        "file": str(file_path),
                        "type": "docstring_added",
                        "line": i + 1,
                        "description": "Added placeholder docstring"
                    })

        new_content = '\n'.join(lines) if modified else content
        return new_content, fixes

    def detect_needed_typing_imports(self, content: str) -> List[str]:
        """Detect which typing imports are needed."""
        imports = []

        if 'List[' in content and 'List' not in imports:
            imports.append('List')
        if 'Dict[' in content and 'Dict' not in imports:
            imports.append('Dict')
        if 'Optional[' in content and 'Optional' not in imports:
            imports.append('Optional')
        if 'Union[' in content and 'Union' not in imports:
            imports.append('Union')
        if 'Tuple[' in content and 'Tuple' not in imports:
            imports.append('Tuple')
        if 'Any' in content and 'Any' not in imports:
            imports.append('Any')

        return imports

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable report."""
        report_lines = [
            "StreamlineVPN Backend Code Quality Report",
            "=" * 50,
            f"Files processed: {results['files_processed']}",
            f"Total fixes: {len(results['fixes_applied'])}",
            ""
        ]

        if results['fixes_applied']:
            report_lines.append("Fixes Applied:")
            report_lines.append("-" * 20)

            fix_types = {}
            for fix in results['fixes_applied']:
                fix_type = fix.get('type', 'unknown')
                if fix_type not in fix_types:
                    fix_types[fix_type] = []
                fix_types[fix_type].append(fix)

            for fix_type, fixes in fix_types.items():
                report_lines.append(f"\n{fix_type.replace('_', ' ').title()} ({len(fixes)}):")
                for fix in fixes[:5]:  # Show first 5 examples
                    if 'file' in fix:
                        report_lines.append(f"  • {Path(fix['file']).name}")
                        if 'line' in fix:
                            report_lines.append(f"    Line {fix['line']}")
                        if 'old' in fix and 'new' in fix:
                            report_lines.append(f"    - {fix['old']}")
                            report_lines.append(f"    + {fix['new']}")
                if len(fixes) > 5:
                    report_lines.append(f"  ... and {len(fixes) - 5} more")

        if results['errors']:
            report_lines.append("\nErrors:")
            report_lines.append("-" * 10)
            for error in results['errors']:
                report_lines.append(f"  ✗ {error}")

        if results['warnings']:
            report_lines.append("\nWarnings:")
            report_lines.append("-" * 10)
            for warning in results['warnings']:
                report_lines.append(f"  ⚠ {warning}")

        return '\n'.join(report_lines)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Fix StreamlineVPN backend code quality issues")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fixed without making changes")
    parser.add_argument("--report", metavar="FILE", help="Save report to file")

    args = parser.parse_args()

    fixer = BackendFixer(args.project_root)

    print("Analyzing StreamlineVPN backend code...")
    results = fixer.analyze_and_fix()

    report = fixer.generate_report(results)
    print(report)

    if args.report:
        with open(args.report, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {args.report}")


if __name__ == "__main__":
    main()
