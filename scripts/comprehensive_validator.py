#!/usr/bin/env python3
"""
Comprehensive Project Validator for StreamlineVPN
=================================================

This script runs a series of checks to ensure the project is correctly
configured, all necessary files are present, and the code is syntactically valid.
"""

import os
import sys
import yaml
from pathlib import Path
import argparse
from typing import List, Tuple, Callable


class ProjectValidator:
    """A comprehensive validator for the StreamlineVPN project."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.errors = []
        self.warnings = []

    def run_all_checks(self) -> bool:
        """Run all validation checks and print a report."""
        print(f"🔍 Starting validation for project at: {self.project_root}")
        print("-" * 80)

        checks: List[Tuple[str, Callable[[], bool]]] = [
            ("File & Directory Completeness", self.check_file_completeness),
            ("Python Syntax Validity", self.check_python_syntax),
            ("Key Module Importability", self.check_imports),
            ("Configuration File Validity", self.check_configurations),
            ("Runner Scripts Executability", self.check_runner_scripts),
        ]

        for name, check_func in checks:
            try:
                if check_func():
                    print(f"✅ {name}: PASSED")
                else:
                    # The check function will have already added to self.errors
                    print(f"❌ {name}: FAILED")
            except Exception as e:
                self.errors.append(f"An unexpected error occurred during '{name}': {e}")
                print(f"💥 {name}: CRASHED")

        print("-" * 80)
        self._print_report()
        return not self.errors

    def _print_report(self):
        """Prints a summary of all errors and warnings."""
        if not self.errors and not self.warnings:
            print("🎉 Validation successful! No critical issues found.")
            return

        if self.errors:
            print(f"\n❌ Found {len(self.errors)} critical error(s):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        if self.warnings:
            print(f"\n⚠️ Found {len(self.warnings)} warning(s):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

    def check_file_completeness(self) -> bool:
        """Check if all essential files and directories are present."""
        essential_items = [
            "src/streamline_vpn",
            "docs/assets/js/main.js",
            "config/sources.yaml",
            ".env.example",
            "requirements.txt",
            "pyproject.toml",
            "docker-compose.production.yml",
            "run_unified.py",
        ]
        missing = []
        for item_path in essential_items:
            if not (self.project_root / item_path).exists():
                missing.append(item_path)

        if missing:
            self.errors.append(f"Missing essential files/directories: {', '.join(missing)}")
            return False
        return True

    def check_python_syntax(self) -> bool:
        """Check all Python files for syntax errors."""
        python_files = list(self.project_root.rglob("*.py"))
        syntax_errors = []
        for py_file in python_files:
            if "backup_" in str(py_file) or "__pycache__" in str(py_file):
                continue
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), py_file, 'exec')
            except SyntaxError as e:
                syntax_errors.append(f"Syntax error in {py_file.relative_to(self.project_root)}: {e}")
            except Exception:
                # Ignore non-syntax errors for this check
                pass
        if syntax_errors:
            self.errors.extend(syntax_errors)
            return False
        return True

    def check_imports(self) -> bool:
        """Check if key modules can be imported."""
        # This is a basic check. A more advanced one would run a subprocess.
        try:
            sys.path.insert(0, str(self.project_root / "src"))
            from streamline_vpn import cli  # noqa
            from streamline_vpn import settings  # noqa
        except ImportError as e:
            self.errors.append(f"Failed to import a key module: {e}")
            return False
        finally:
            if str(self.project_root / "src") in sys.path:
                sys.path.pop(0)
        return True

    def check_configurations(self) -> bool:
        """Validate the syntax of YAML configuration files."""
        try:
            with open(self.project_root / "config/sources.yaml", 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except (yaml.YAMLError, FileNotFoundError) as e:
            self.errors.append(f"Configuration error in config/sources.yaml: {e}")
            return False
        return True

    def check_runner_scripts(self) -> bool:
        """Check if runner scripts are executable (on non-Windows systems)."""
        if os.name == 'nt':
            self.warnings.append("Skipping runner script executability check on Windows.")
            return True

        not_executable = []
        for script_name in ["run_unified.py", "run_api.py", "run_web.py"]:
            script_path = self.project_root / script_name
            if not os.access(script_path, os.X_OK):
                not_executable.append(script_name)

        if not_executable:
            self.warnings.append(f"Runner scripts are not executable: {', '.join(not_executable)}. Use 'chmod +x <script>'.")
        return True


def main():
    parser = argparse.ArgumentParser(description="StreamlineVPN Comprehensive Project Validator.")
    parser.add_argument(
        "--output",
        type=str,
        help="Path to save the validation report.",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="The root directory of the StreamlineVPN project.",
    )
    args = parser.parse_args()

    validator = ProjectValidator(project_root=args.project_root)
    is_valid = validator.run_all_checks()

    if args.output:
        report_path = Path(args.output)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("StreamlineVPN Validation Report\n")
            f.write("=" * 30 + "\n")
            if validator.errors:
                f.write(f"Errors ({len(validator.errors)}):\n")
                for err in validator.errors:
                    f.write(f"- {err}\n")
            if validator.warnings:
                f.write(f"\nWarnings ({len(validator.warnings)}):\n")
                for warn in validator.warnings:
                    f.write(f"- {warn}\n")
            if not validator.errors:
                f.write("\nResult: Success\n")
            else:
                f.write("\nResult: Failed\n")
        print(f"\n📄 Validation report saved to: {report_path}")

    # Exit with a non-zero code if errors were found
    if not is_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
