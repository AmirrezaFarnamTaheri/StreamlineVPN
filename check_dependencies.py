#!/usr/bin/env python3
"""
check_dependencies.py
=====================

Comprehensive dependency and import checker for StreamlineVPN.
"""

import sys
import importlib
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple

def check_python_version() -> bool:
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Requires Python 3.8+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_required_packages() -> Tuple[bool, List[str]]:
    """Check if all required packages are installed."""
    print("\n📦 Checking required packages...")
    
    required_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"), 
        ("aiohttp", "aiohttp"),
        ("pyyaml", "yaml"),
        ("pydantic", "pydantic"),
        ("redis", "redis"),
        ("click", "click"),
        ("python-dotenv", "dotenv"),
        ("websockets", "websockets"),
        ("python-multipart", "multipart")
    ]
    
    missing_packages = []
    
    for display_name, import_name in required_packages:
        try:
            importlib.import_module(import_name)
            print(f"✅ {display_name}")
        except ImportError:
            print(f"❌ {display_name} - MISSING")
            missing_packages.append(display_name)
    
    return len(missing_packages) == 0, missing_packages

def check_optional_packages() -> Dict[str, bool]:
    """Check optional packages."""
    print("\n🔧 Checking optional packages...")
    
    optional_packages = {
        "numpy": "numpy",
        "pandas": "pandas", 
        "scikit-learn": "sklearn",
        "prometheus-client": "prometheus_client",
        "structlog": "structlog",
        "cryptography": "cryptography",
        "psycopg2": "psycopg2",
        "sqlalchemy": "sqlalchemy",
        "kubernetes": "kubernetes",
        "docker": "docker"
    }
    
    results = {}
    for display_name, import_name in optional_packages.items():
        try:
            importlib.import_module(import_name)
            print(f"✅ {display_name}")
            results[display_name] = True
        except ImportError:
            print(f"⚠️  {display_name} - Optional")
            results[display_name] = False
    
    return results

def check_module_imports() -> Tuple[bool, List[str]]:
    """Check if all StreamlineVPN modules can be imported."""
    print("\n🔍 Checking module imports...")
    
    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    modules_to_check = [
        "streamline_vpn",
        "streamline_vpn.core.merger",
        "streamline_vpn.core.config_processor", 
        "streamline_vpn.core.output_manager",
        "streamline_vpn.core.source_manager",
        "streamline_vpn.models.configuration",
        "streamline_vpn.models.source",
        "streamline_vpn.utils.logging",
        "streamline_vpn.web.unified_api",
        "streamline_vpn.jobs.models",
        "streamline_vpn.jobs.manager"
    ]
    
    failed_imports = []
    
    for module in modules_to_check:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module} - {e}")
            failed_imports.append(module)
        except Exception as e:
            print(f"⚠️  {module} - {e}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0, failed_imports

def check_file_structure() -> Tuple[bool, List[str]]:
    """Check if all required files exist."""
    print("\n📁 Checking file structure...")
    
    required_files = [
        "src/streamline_vpn/__init__.py",
        "src/streamline_vpn/web/unified_api.py",
        "docs/index.html",
        "docs/assets/js/main_fixed.js",
        "tests/test_fixed_suite.py",
        "requirements.txt",
        "env.example",
        "Dockerfile",
        "docker-compose.yml",
        "streamline_setup.py",
        "run_unified.py",
        "run_all.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    return len(missing_files) == 0, missing_files

def check_configuration() -> Tuple[bool, List[str]]:
    """Check configuration files."""
    print("\n⚙️  Checking configuration...")
    
    config_files = [
        "config/sources.yaml",
        ".env"
    ]
    
    missing_configs = []
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file}")
        else:
            print(f"⚠️  {config_file} - Not found (will be created)")
            missing_configs.append(config_file)
    
    return len(missing_configs) == 0, missing_configs

def check_duplicate_files() -> List[str]:
    """Check for duplicate or conflicting files."""
    print("\n🔄 Checking for duplicates...")
    
    potential_duplicates = [
        ("src/streamline_vpn/web/api.py", "src/streamline_vpn/web/unified_api.py"),
        ("run_server.py", "run_unified.py"),
        ("docs/assets/js/main.js", "docs/assets/js/main_fixed.js"),
        ("tests/test_*.py", "tests/test_fixed_suite.py")
    ]
    
    duplicates = []
    
    for file1, file2 in potential_duplicates:
        if Path(file1).exists() and Path(file2).exists():
            print(f"⚠️  Potential duplicate: {file1} and {file2}")
            duplicates.append((file1, file2))
        else:
            print(f"✅ No conflict between {file1} and {file2}")
    
    return duplicates

def run_basic_tests() -> bool:
    """Run basic functionality tests."""
    print("\n🧪 Running basic tests...")
    
    try:
        # Test unified API creation
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from streamline_vpn.web.unified_api import create_unified_app
        
        app = create_unified_app()
        if app is not None:
            print("✅ Unified API creation test passed")
            return True
        else:
            print("❌ Unified API creation test failed")
            return False
            
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False

def generate_report(results: Dict[str, Any]) -> str:
    """Generate a comprehensive report."""
    report = f"""
StreamlineVPN Dependency Check Report
====================================

Python Version: {'✅' if results['python_ok'] else '❌'}
Required Packages: {'✅' if results['packages_ok'] else '❌'}
Module Imports: {'✅' if results['imports_ok'] else '❌'}
File Structure: {'✅' if results['files_ok'] else '❌'}
Configuration: {'✅' if results['config_ok'] else '❌'}
Basic Tests: {'✅' if results['tests_ok'] else '❌'}

"""
    
    if results['missing_packages']:
        report += f"Missing Packages: {', '.join(results['missing_packages'])}\n"
    
    if results['failed_imports']:
        report += f"Failed Imports: {', '.join(results['failed_imports'])}\n"
    
    if results['missing_files']:
        report += f"Missing Files: {', '.join(results['missing_files'])}\n"
    
    if results['duplicates']:
        report += f"Duplicates Found: {len(results['duplicates'])} pairs\n"
    
    return report

def main():
    """Main dependency check function."""
    print("🔍 StreamlineVPN Dependency Checker")
    print("=" * 40)
    
    # Run all checks
    python_ok = check_python_version()
    packages_ok, missing_packages = check_required_packages()
    optional_packages = check_optional_packages()
    imports_ok, failed_imports = check_module_imports()
    files_ok, missing_files = check_file_structure()
    config_ok, missing_configs = check_configuration()
    duplicates = check_duplicate_files()
    tests_ok = run_basic_tests()
    
    # Compile results
    results = {
        'python_ok': python_ok,
        'packages_ok': packages_ok,
        'missing_packages': missing_packages,
        'optional_packages': optional_packages,
        'imports_ok': imports_ok,
        'failed_imports': failed_imports,
        'files_ok': files_ok,
        'missing_files': missing_files,
        'config_ok': config_ok,
        'missing_configs': missing_configs,
        'duplicates': duplicates,
        'tests_ok': tests_ok
    }
    
    # Generate and print report
    report = generate_report(results)
    print(report)
    
    # Overall status
    all_critical_ok = python_ok and packages_ok and imports_ok and files_ok and tests_ok
    
    if all_critical_ok:
        print("🎉 All critical checks passed! System is ready.")
        return 0
    else:
        print("❌ Some critical checks failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
