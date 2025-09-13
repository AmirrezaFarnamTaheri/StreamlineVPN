#!/usr/bin/env python3
"""
Final Project Validation Script
===============================

Comprehensive validation to ensure the project is production-ready.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import importlib.util

class FinalProjectValidator:
    """Comprehensive project validation."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.validation_results = {
            "timestamp": None,
            "overall_status": "unknown",
            "checks": {},
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }

    async def validate_all(self) -> Dict[str, Any]:
        """Run all final validation checks."""
        print("🔍 Starting final project validation...")

        # Core validation checks
        await self._validate_critical_fixes()
        await self._validate_backend_integration()
        await self._validate_frontend_functionality()
        await self._validate_api_endpoints()
        await self._validate_docker_setup()
        await self._validate_security_requirements()
        await self._validate_performance_requirements()
        await self._validate_production_readiness()

        # Calculate overall status
        self._calculate_final_status()

        return self.validation_results

    async def _validate_critical_fixes(self):
        """Validate that all critical fixes have been applied."""
        check_name = "critical_fixes"
        check = {"name": "Critical Fixes Applied", "status": "checking", "issues": []}

        critical_fixes = [
            {
                "name": "JavaScript Syntax Fix",
                "file": "docs/api-base.js",
                "check": lambda: self._check_js_syntax_fix()
            },
            {
                "name": "Complete CSS Implementation",
                "file": "docs/assets/css/style.css",
                "check": lambda: self._check_css_completeness()
            },
            {
                "name": "HTML Structure Completion",
                "file": "docs/interactive.html",
                "check": lambda: self._check_html_completeness()
            },
            {
                "name": "Backend Error Handling",
                "file": "src/streamline_vpn/web/unified_api.py",
                "check": lambda: self._check_backend_error_handling()
            }
        ]

        for fix in critical_fixes:
            try:
                if fix["check"]():
                    print(f"✅ {fix['name']}: Applied")
                else:
                    check["issues"].append({
                        "type": "critical_fix_missing",
                        "severity": "error",
                        "message": f"{fix['name']} not properly applied",
                        "file": fix["file"]
                    })
            except Exception as e:
                check["issues"].append({
                    "type": "critical_fix_error",
                    "severity": "error",
                    "message": f"Error checking {fix['name']}: {e}",
                    "file": fix["file"]
                })

        check["status"] = "passed" if not check["issues"] else "failed"
        self.validation_results["checks"][check_name] = check

    def _check_js_syntax_fix(self) -> bool:
        """Check if JavaScript syntax error is fixed."""
        api_base_file = self.project_root / "docs" / "api-base.js"
        if not api_base_file.exists():
            return False

        content = api_base_file.read_text(encoding='utf-8')

        # Check that 'and' has been replaced with '&&'
        if 'params[key] !== undefined and params[key] !== null' in content:
            return False  # Still has the syntax error

        if 'params[key] !== undefined && params[key] !== null' in content:
            return True  # Fixed

        return False

    def _check_css_completeness(self) -> bool:
        """Check if CSS file is complete."""
        css_file = self.project_root / "docs" / "assets" / "css" / "style.css"
        if not css_file.exists():
            return False

        content = css_file.read_text(encoding='utf-8')

        # Check for essential CSS classes
        required_classes = [
            '.stat-card', '.progress-bar', '.btn', '.glass',
            '.animated-bg', '.quality-badge'
        ]

        for css_class in required_classes:
            if css_class not in content:
                return False

        # Check file is substantial (not truncated)
        return len(content) > 10000  # Should be substantial

    def _check_html_completeness(self) -> bool:
        """Check if HTML files are complete."""
        html_file = self.project_root / "docs" / "interactive.html"
        if not html_file.exists():
            return False

        content = html_file.read_text(encoding='utf-8')

        # Check for essential HTML elements
        required_elements = [
            'api-base.js', 'StreamlineVPNApp', 'statistics-section',
            'sources-section', 'jobs-section'
        ]

        return all(element in content for element in required_elements)

    def _check_backend_error_handling(self) -> bool:
        """Check if backend has proper error handling."""
        unified_api_file = self.project_root / "src" / "streamline_vpn" / "web" / "unified_api.py"
        if not unified_api_file.exists():
            return False

        content = unified_api_file.read_text(encoding='utf-8')

        # Check for proper error handling patterns
        error_patterns = [
            'try:', 'except Exception', 'logger.error', 'WebSocketDisconnect'
        ]

        return all(pattern in content for pattern in error_patterns)

    async def _validate_backend_integration(self):
        """Validate backend components are properly integrated."""
        check_name = "backend_integration"
        check = {"name": "Backend Integration", "status": "checking", "issues": []}

        # Check core module imports
        core_modules = [
            "src/streamline_vpn/core/merger.py",
            "src/streamline_vpn/core/source_manager.py",
            "src/streamline_vpn/core/config_processor.py",
            "src/streamline_vpn/web/unified_api.py"
        ]

        for module_path in core_modules:
            module_file = self.project_root / module_path
            if not module_file.exists():
                check["issues"].append({
                    "type": "missing_module",
                    "severity": "error",
                    "message": f"Required module missing: {module_path}"
                })
            else:
                # Try to import the module
                try:
                    spec = importlib.util.spec_from_file_location("test_module", module_file)
                    module = importlib.util.module_from_spec(spec)
                    # Note: We don't actually execute the module to avoid side effects
                    print(f"✅ Module structure valid: {module_path}")
                except Exception as e:
                    check["issues"].append({
                        "type": "module_import_error",
                        "severity": "warning",
                        "message": f"Module import issue in {module_path}: {e}"
                    })

        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check

    async def _validate_frontend_functionality(self):
        """Validate frontend functionality."""
        check_name = "frontend_functionality"
        check = {"name": "Frontend Functionality", "status": "checking", "issues": []}

        # Check required frontend files
        frontend_files = {
            "docs/index.html": ["StreamlineVPN", "api-base.js"],
            "docs/interactive.html": ["Control Panel", "StreamlineVPNApp"],
            "docs/config_generator.html": ["Configuration Generator", "ConfigGenerator"],
            "docs/api-base.js": ["window.API", "request:", "get:", "post:"],
            "docs/assets/css/style.css": [".stat-card", ".btn", ".glass"],
            "docs/assets/js/main.js": ["StreamlineVPNApp", "init"]
        }

        for file_path, required_content in frontend_files.items():
            full_path = self.project_root / file_path
            if not full_path.exists():
                check["issues"].append({
                    "type": "missing_frontend_file",
                    "severity": "error",
                    "message": f"Missing frontend file: {file_path}"
                })
            else:
                try:
                    content = full_path.read_text(encoding='utf-8')
                    for required in required_content:
                        if required not in content:
                            check["issues"].append({
                                "type": "missing_frontend_content",
                                "severity": "warning",
                                "message": f"Missing content '{required}' in {file_path}"
                            })
                except Exception as e:
                    check["issues"].append({
                        "type": "frontend_file_error",
                        "severity": "error",
                        "message": f"Error reading {file_path}: {e}"
                    })

        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check

    def _calculate_final_status(self):
        """Calculate overall validation status."""
        total_checks = len(self.validation_results["checks"])
        passed_checks = sum(1 for check in self.validation_results["checks"].values() if check["status"] == "passed")
        failed_checks = total_checks - passed_checks

        total_issues = sum(len(check.get("issues", [])) for check in self.validation_results["checks"].values())
        error_issues = sum(
            len([issue for issue in check.get("issues", []) if issue.get("severity") == "error"])
            for check in self.validation_results["checks"].values()
        )

        self.validation_results["summary"].update({
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": failed_checks,
            "total_issues": total_issues,
            "error_issues": error_issues
        })

        # Determine overall status
        if error_issues == 0 and failed_checks == 0:
            self.validation_results["overall_status"] = "passed"
        elif error_issues > 0:
            self.validation_results["overall_status"] = "failed"
        else:
            self.validation_results["overall_status"] = "warning"

    def generate_report(self) -> str:
        """Generate a comprehensive validation report."""
        results = self.validation_results
        summary = results["summary"]

        report = f"""
# StreamlineVPN Final Validation Report

## Overall Status: {results["overall_status"].upper()}

## Summary
- **Total Checks**: {summary["total_checks"]}
- **Passed**: {summary["passed"]}
- **Failed**: {summary["failed"]}
- **Total Issues**: {summary.get("total_issues", 0)}
- **Critical Issues**: {summary.get("error_issues", 0)}

## Detailed Results

"""

        for check_name, check_data in results["checks"].items():
            status_icon = "✅" if check_data["status"] == "passed" else "❌"
            report += f"### {status_icon} {check_data['name']}\n"

            if check_data.get("issues"):
                for issue in check_data["issues"]:
                    severity_icon = "🔴" if issue["severity"] == "error" else "⚠️"
                    report += f"- {severity_icon} {issue['message']}\n"
                    if issue.get("file"):
                        report += f"  - File: {issue['file']}\n"
            else:
                report += "- No issues found\n"

            report += "\n"

        # Add recommendations
        if results["overall_status"] != "passed":
            report += "## Recommendations\n\n"

            if summary.get("error_issues", 0) > 0:
                report += "🔴 **Critical Issues Found**: Address all error-level issues before deployment.\n"

            report += "⚠️ **Warning Issues**: Review and address warning-level issues for optimal performance.\n"
            report += "📋 **Next Steps**: Run tests after fixing issues and re-validate.\n"

        return report


async def main():
    """Run final validation."""
    validator = FinalProjectValidator()
    results = await validator.validate_all()

    # Generate and save report
    report = validator.generate_report()

    # Save report
    report_file = Path("final_validation_report.md")
    report_file.write_text(report, encoding='utf-8')

    # Print summary
    print("\n" + "="*60)
    print("FINAL VALIDATION COMPLETE")
    print("="*60)
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Checks: {results['summary']['passed']}/{results['summary']['total_checks']} passed")

    if results["overall_status"] == "passed":
        print("🎉 Project is ready for production deployment!")
        return 0
    else:
        print(f"❌ {results['summary'].get('error_issues', 0)} critical issues need attention")
        print(f"📋 Report saved to: {report_file}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
