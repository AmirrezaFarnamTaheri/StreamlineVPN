"""
Project structure validation.
"""

from pathlib import Path
from typing import Dict, Any
from .base_validator import BaseValidator


class StructureValidator(BaseValidator):
    """Validates project structure and organization."""
    
    def validate_project_structure(self):
        """Validate core project structure."""
        print("📁 Validating project structure...")
        
        # Essential directories
        essential_dirs = [
            ("src", "Source code"),
            ("tests", "Test suite"),
            ("config", "Configuration files"),
            ("docs", "Documentation"),
            ("scripts", "Utility scripts"),
            ("src/streamline_vpn", "Main package"),
            ("src/streamline_vpn/core", "Core modules"),
            ("src/streamline_vpn/api", "API modules"),
            ("src/streamline_vpn/web", "Web interface"),
            ("src/streamline_vpn/utils", "Utility modules"),
            ("src/streamline_vpn/security", "Security modules"),
            ("src/streamline_vpn/monitoring", "Monitoring modules"),
            ("src/streamline_vpn/jobs", "Job management"),
            ("src/streamline_vpn/caching", "Caching modules"),
            ("src/streamline_vpn/fetcher", "Data fetching"),
            ("src/streamline_vpn/discovery", "Source discovery")
        ]
        
        for dir_path, description in essential_dirs:
            self._check_directory_exists(dir_path, description)
        
        # Check for __init__.py files
        init_files = [
            "src/streamline_vpn/__init__.py",
            "src/streamline_vpn/core/__init__.py",
            "src/streamline_vpn/api/__init__.py",
            "src/streamline_vpn/web/__init__.py",
            "src/streamline_vpn/utils/__init__.py",
            "src/streamline_vpn/security/__init__.py",
            "src/streamline_vpn/monitoring/__init__.py",
            "src/streamline_vpn/jobs/__init__.py",
            "src/streamline_vpn/caching/__init__.py",
            "src/streamline_vpn/fetcher/__init__.py",
            "src/streamline_vpn/discovery/__init__.py"
        ]
        
        for init_file in init_files:
            self._check_file_exists(init_file, f"Package init file: {init_file}")
        
        # Check for main entry points
        entry_points = [
            "src/streamline_vpn/__main__.py",
            "run_unified.py",
            "run_api.py", 
            "run_web.py"
        ]
        
        for entry_point in entry_points:
            self._check_file_exists(entry_point, f"Entry point: {entry_point}")
    
    def validate_essential_files(self):
        """Validate essential project files."""
        print("📄 Validating essential files...")
        
        essential_files = [
            ("setup.py", "Package setup"),
            ("pyproject.toml", "Modern Python packaging"),
            ("requirements.txt", "Production dependencies"),
            ("requirements-dev.txt", "Development dependencies"),
            ("README.md", "Project documentation"),
            ("LICENSE", "License file"),
            (".gitignore", "Git ignore rules"),
            ("config/sources.yaml", "Source configuration"),
            (".env.example", "Environment template"),
            ("docker-compose.yml", "Docker composition"),
            ("Dockerfile", "Docker configuration"),
            ("nginx.conf", "Nginx configuration")
        ]
        
        for file_path, description in essential_files:
            self._check_file_exists(file_path, description)
        
        # Check for test configuration
        test_files = [
            "pytest.ini",
            "conftest.py",
            "tests/conftest.py"
        ]
        
        for test_file in test_files:
            if self._check_file_exists(test_file, f"Test config: {test_file}"):
                # Validate pytest configuration
                self._validate_pytest_config(test_file)
    
    def _validate_pytest_config(self, config_file: str):
        """Validate pytest configuration file."""
        content = self._read_file_content(config_file)
        if not content:
            return
        
        # Check for basic pytest configuration
        if "pytest" in content.lower() or "testpaths" in content.lower():
            self._add_check_result(
                f"pytest_config_{config_file}",
                "PASS",
                f"Pytest configuration found in {config_file}"
            )
        else:
            self._add_check_result(
                f"pytest_config_{config_file}",
                "WARN",
                f"Pytest configuration may be incomplete in {config_file}"
            )

