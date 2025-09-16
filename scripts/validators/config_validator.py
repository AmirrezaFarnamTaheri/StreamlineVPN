"""
Configuration validation.
"""

from pathlib import Path
from typing import Dict, Any
import yaml
import json
from .base_validator import BaseValidator


class ConfigValidator(BaseValidator):
    """Validates configuration files and environment setup."""
    
    def validate_configuration_completeness(self):
        """Validate configuration files are complete."""
        print("⚙️ Validating configuration completeness...")
        
        # Check YAML configuration
        yaml_configs = [
            "config/sources.yaml",
            "config/nginx/nginx.conf"
        ]
        
        for config_file in yaml_configs:
            if self._check_file_exists(config_file, f"Config file: {config_file}"):
                self._validate_yaml_config(config_file)
        
        # Check environment files
        env_files = [
            ".env.example",
            ".env"
        ]
        
        for env_file in env_files:
            if self._check_file_exists(env_file, f"Environment file: {env_file}"):
                self._validate_env_file(env_file)
    
    def validate_environment_setup(self):
        """Validate environment setup."""
        print("🌍 Validating environment setup...")
        
        # Check for required environment variables in .env.example
        env_example = self._read_file_content(".env.example")
        if env_example:
            required_vars = [
                "DATABASE_URL",
                "REDIS_URL", 
                "API_KEY",
                "SECRET_KEY"
            ]
            
            missing_vars = []
            for var in required_vars:
                if var not in env_example:
                    missing_vars.append(var)
            
            if missing_vars:
                self._add_check_result(
                    "env_variables",
                    "WARN",
                    f"Missing environment variables in .env.example: {', '.join(missing_vars)}"
                )
            else:
                self._add_check_result(
                    "env_variables",
                    "PASS",
                    "All required environment variables documented"
                )
    
    def validate_dependency_management(self):
        """Validate dependency management files."""
        print("📦 Validating dependency management...")
        
        # Check requirements files
        req_files = [
            "requirements.txt",
            "requirements-dev.txt"
        ]
        
        for req_file in req_files:
            if self._check_file_exists(req_file, f"Requirements file: {req_file}"):
                self._validate_requirements_file(req_file)
        
        # Check setup.py
        if self._check_file_exists("setup.py", "Package setup"):
            self._validate_setup_py()
        
        # Check pyproject.toml
        if self._check_file_exists("pyproject.toml", "Modern packaging config"):
            self._validate_pyproject_toml()
    
    def _validate_yaml_config(self, config_file: str):
        """Validate YAML configuration file."""
        content = self._read_file_content(config_file)
        if not content:
            return
        
        try:
            yaml.safe_load(content)
            self._add_check_result(
                f"yaml_syntax_{config_file.replace('/', '_')}",
                "PASS",
                f"YAML file {config_file} has valid syntax"
            )
        except yaml.YAMLError as e:
            self._add_check_result(
                f"yaml_syntax_{config_file.replace('/', '_')}",
                "FAIL",
                f"YAML file {config_file} has syntax errors: {str(e)}",
                critical=True
            )
    
    def _validate_env_file(self, env_file: str):
        """Validate environment file."""
        content = self._read_file_content(env_file)
        if not content:
            return
        
        # Check for basic env file format
        lines = content.strip().split('\n')
        valid_lines = 0
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                valid_lines += 1
        
        if valid_lines > 0:
            self._add_check_result(
                f"env_format_{env_file.replace('/', '_')}",
                "PASS",
                f"Environment file {env_file} has {valid_lines} valid entries"
            )
        else:
            self._add_check_result(
                f"env_format_{env_file.replace('/', '_')}",
                "WARN",
                f"Environment file {env_file} appears to be empty or malformed"
            )
    
    def _validate_requirements_file(self, req_file: str):
        """Validate requirements file."""
        content = self._read_file_content(req_file)
        if not content:
            return
        
        lines = content.strip().split('\n')
        valid_packages = 0
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Basic package name validation
                if any(char.isalnum() for char in line.split('==')[0].split('>=')[0].split('<=')[0]):
                    valid_packages += 1
        
        if valid_packages > 0:
            self._add_check_result(
                f"requirements_content_{req_file.replace('/', '_')}",
                "PASS",
                f"Requirements file {req_file} has {valid_packages} packages"
            )
        else:
            self._add_check_result(
                f"requirements_content_{req_file.replace('/', '_')}",
                "WARN",
                f"Requirements file {req_file} appears to be empty"
            )
    
    def _validate_setup_py(self):
        """Validate setup.py file."""
        content = self._read_file_content("setup.py")
        if not content:
            return
        
        # Check for essential setup.py elements
        has_name = "name=" in content
        has_version = "version=" in content
        has_install_requires = "install_requires=" in content
        
        if has_name and has_version and has_install_requires:
            self._add_check_result(
                "setup_py_complete",
                "PASS",
                "setup.py has essential elements"
            )
        else:
            missing = []
            if not has_name:
                missing.append("name")
            if not has_version:
                missing.append("version")
            if not has_install_requires:
                missing.append("install_requires")
            
            self._add_check_result(
                "setup_py_complete",
                "WARN",
                f"setup.py missing: {', '.join(missing)}"
            )
    
    def _validate_pyproject_toml(self):
        """Validate pyproject.toml file."""
        content = self._read_file_content("pyproject.toml")
        if not content:
            return
        
        try:
            # Try to parse as TOML (simplified check)
            if "[build-system]" in content or "[tool." in content:
                self._add_check_result(
                    "pyproject_toml_valid",
                    "PASS",
                    "pyproject.toml has valid structure"
                )
            else:
                self._add_check_result(
                    "pyproject_toml_valid",
                    "WARN",
                    "pyproject.toml may be incomplete"
                )
        except Exception:
            self._add_check_result(
                "pyproject_toml_valid",
                "WARN",
                "pyproject.toml may have syntax issues"
            )

