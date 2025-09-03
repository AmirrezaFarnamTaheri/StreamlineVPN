#!/usr/bin/env python3
"""
Comprehensive Test Runner for VPN Subscription Merger
Runs all tests with coverage reporting and performance metrics.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any


def run_command(command: list[str], cwd: str = None) -> dict[str, Any]:
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=300)
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "returncode": -1, "stdout": "", "stderr": "Command timed out"}
    except Exception as e:
        return {"success": False, "returncode": -1, "stdout": "", "stderr": str(e)}


def run_pytest_tests(test_files: list[str]) -> dict[str, Any]:
    """Run pytest tests with coverage."""
    print("Running pytest tests with coverage...")

    # Install test dependencies if needed
    install_result = run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "pytest",
            "pytest-cov",
            "pytest-asyncio",
            "pytest-mock",
        ]
    )

    if not install_result["success"]:
        print(f"Warning: Failed to install test dependencies: {install_result['stderr']}")

    # Run tests with coverage
    test_command = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=vpn_merger",
        "--cov-report=html",
        "--cov-report=term",
        "--cov-report=json",
        "-v",
        "--tb=short",
    ] + test_files

    result = run_command(test_command)

    return result


def run_unit_tests() -> dict[str, Any]:
    """Run unit tests."""
    print("Running unit tests...")

    unit_test_files = [
        "tests/test_sources_comprehensive.py",
        "tests/test_core_components.py",
        "tests/test_parsers.py",
        "tests/test_ml_components.py",
        "tests/test_security_manager.py",
    ]

    return run_pytest_tests(unit_test_files)


def run_integration_tests() -> dict[str, Any]:
    """Run integration tests."""
    print("Running integration tests...")

    integration_test_files = [
        "tests/test_e2e.py",
        "tests/test_performance.py",
        "tests/test_security.py",
    ]

    return run_pytest_tests(integration_test_files)


def run_all_tests() -> dict[str, Any]:
    """Run all tests."""
    print("Running all tests...")

    all_test_files = [
        "tests/test_sources_comprehensive.py",
        "tests/test_core_components.py",
        "tests/test_parsers.py",
        "tests/test_ml_components.py",
        "tests/test_security_manager.py",
        "tests/test_e2e.py",
        "tests/test_performance.py",
        "tests/test_security.py",
    ]

    return run_pytest_tests(all_test_files)


def generate_test_report(results: dict[str, Any]) -> str:
    """Generate a test report."""
    report = []
    report.append("# Test Report")
    report.append("=" * 50)
    report.append("")

    for test_type, result in results.items():
        report.append(f"## {test_type.title()} Tests")
        report.append("")

        if result["success"]:
            report.append("✅ **PASSED**")
        else:
            report.append("❌ **FAILED**")

        report.append(f"Return code: {result['returncode']}")
        report.append("")

        if result["stdout"]:
            report.append("### Output:")
            report.append("```")
            report.append(result["stdout"])
            report.append("```")
            report.append("")

        if result["stderr"]:
            report.append("### Errors:")
            report.append("```")
            report.append(result["stderr"])
            report.append("```")
            report.append("")

    return "\n".join(report)


def main():
    """Main test runner function."""
    print("VPN Subscription Merger - Test Runner")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("vpn_merger.py").exists():
        print("Error: vpn_merger.py not found. Please run from the project root.")
        sys.exit(1)

    # Run tests
    results = {}

    # Unit tests
    print("\n1. Running unit tests...")
    results["unit"] = run_unit_tests()

    # Integration tests
    print("\n2. Running integration tests...")
    results["integration"] = run_integration_tests()

    # All tests
    print("\n3. Running all tests...")
    results["all"] = run_all_tests()

    # Generate report
    report = generate_test_report(results)

    # Save report
    with open("test_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print("=" * 50)

    for test_type, result in results.items():
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{test_type.title()} Tests: {status}")

    print("\nDetailed report saved to: test_report.md")

    # Check if all tests passed
    all_passed = all(result["success"] for result in results.values())

    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the report for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
