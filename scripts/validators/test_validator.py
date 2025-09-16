"""
Test validation and coverage checking.
"""

from pathlib import Path
from typing import Dict, Any
from .base_validator import BaseValidator


class TestValidator(BaseValidator):
    """Validates test suite and coverage."""
    
    def validate_test_coverage(self):
        """Validate test coverage."""
        print("🧪 Validating test coverage...")
        
        # Check if tests directory exists and has tests
        test_files = list((self.project_root / "tests").rglob("test_*.py"))
        
        if test_files:
            self._add_check_result(
                "test_files_exist",
                "PASS",
                f"Found {len(test_files)} test files"
            )
            
            # Check test file structure
            self._validate_test_files(test_files)
        else:
            self._add_check_result(
                "test_files_exist",
                "FAIL",
                "No test files found",
                critical=True
            )
    
    def validate_test_configuration(self):
        """Validate test configuration."""
        print("⚙️ Validating test configuration...")
        
        # Check pytest configuration
        pytest_configs = [
            "pytest.ini",
            "pyproject.toml",
            "setup.cfg"
        ]
        
        has_pytest_config = False
        for config_file in pytest_configs:
            if self._check_file_exists(config_file, f"Test config: {config_file}"):
                has_pytest_config = True
                self._validate_pytest_config(config_file)
        
        if not has_pytest_config:
            self._add_check_result(
                "pytest_configuration",
                "WARN",
                "No pytest configuration found"
            )
        
        # Check conftest.py
        conftest_files = [
            "conftest.py",
            "tests/conftest.py"
        ]
        
        for conftest in conftest_files:
            self._check_file_exists(conftest, f"Test fixtures: {conftest}")
    
    def validate_documentation_completeness(self):
        """Validate documentation completeness."""
        print("📚 Validating documentation...")
        
        # Check main documentation files
        doc_files = [
            "README.md",
            "docs/api/index.html",
            "docs/api/endpoints.md",
            "IMPLEMENTATION_GUIDE.md"
        ]
        
        for doc_file in doc_files:
            if self._check_file_exists(doc_file, f"Documentation: {doc_file}"):
                self._validate_documentation_content(doc_file)
    
    def validate_api_documentation(self):
        """Validate API documentation."""
        print("📖 Validating API documentation...")
        
        # Check API documentation files
        api_docs = [
            "docs/api/index.html",
            "docs/api/endpoints.md"
        ]
        
        for doc_file in api_docs:
            if self._check_file_exists(doc_file, f"API docs: {doc_file}"):
                self._validate_api_doc_content(doc_file)
    
    def _validate_test_files(self, test_files):
        """Validate individual test files."""
        for test_file in test_files:
            relative_path = test_file.relative_to(self.project_root)
            content = self._read_file_content(str(relative_path))
            
            if content:
                # Check for test functions
                has_test_functions = "def test_" in content
                has_imports = "import pytest" in content or "from pytest" in content
                
                if has_test_functions:
                    self._add_check_result(
                        f"test_functions_{str(relative_path).replace('/', '_')}",
                        "PASS",
                        f"Test file {relative_path} has test functions"
                    )
                else:
                    self._add_check_result(
                        f"test_functions_{str(relative_path).replace('/', '_')}",
                        "WARN",
                        f"Test file {relative_path} may be missing test functions"
                    )
                
                if has_imports:
                    self._add_check_result(
                        f"test_imports_{str(relative_path).replace('/', '_')}",
                        "PASS",
                        f"Test file {relative_path} imports pytest"
                    )
    
    def _validate_pytest_config(self, config_file: str):
        """Validate pytest configuration."""
        content = self._read_file_content(config_file)
        if not content:
            return
        
        # Check for common pytest settings
        has_testpaths = "testpaths" in content.lower()
        has_addopts = "addopts" in content.lower()
        
        if has_testpaths or has_addopts:
            self._add_check_result(
                f"pytest_config_{config_file.replace('/', '_')}",
                "PASS",
                f"Pytest configuration {config_file} has settings"
            )
        else:
            self._add_check_result(
                f"pytest_config_{config_file.replace('/', '_')}",
                "WARN",
                f"Pytest configuration {config_file} may be minimal"
            )
    
    def _validate_documentation_content(self, doc_file: str):
        """Validate documentation content."""
        content = self._read_file_content(doc_file)
        if not content:
            return
        
        # Basic content validation
        word_count = len(content.split())
        
        if word_count > 100:
            self._add_check_result(
                f"doc_content_{doc_file.replace('/', '_')}",
                "PASS",
                f"Documentation {doc_file} has substantial content ({word_count} words)"
            )
        else:
            self._add_check_result(
                f"doc_content_{doc_file.replace('/', '_')}",
                "WARN",
                f"Documentation {doc_file} may be too brief ({word_count} words)"
            )
    
    def _validate_api_doc_content(self, doc_file: str):
        """Validate API documentation content."""
        content = self._read_file_content(doc_file)
        if not content:
            return
        
        # Check for API-specific content
        has_endpoints = any(keyword in content.lower() for keyword in [
            "endpoint", "api", "route", "method", "response", "request"
        ])
        
        if has_endpoints:
            self._add_check_result(
                f"api_doc_content_{doc_file.replace('/', '_')}",
                "PASS",
                f"API documentation {doc_file} contains API-specific content"
            )
        else:
            self._add_check_result(
                f"api_doc_content_{doc_file.replace('/', '_')}",
                "WARN",
                f"API documentation {doc_file} may be missing API details"
            )

