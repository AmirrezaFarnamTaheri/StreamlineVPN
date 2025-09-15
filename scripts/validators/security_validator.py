"""
Security validation.
"""

from pathlib import Path
from typing import Dict, Any
from .base_validator import BaseValidator


class SecurityValidator(BaseValidator):
    """Validates security measures and configurations."""
    
    def validate_security_measures(self):
        """Validate security implementations."""
        print("🔒 Validating security measures...")
        
        # Check security modules
        security_files = [
            "src/streamline_vpn/security/manager.py",
            "src/streamline_vpn/security/validator.py",
            "src/streamline_vpn/security/threat_analyzer.py"
        ]
        
        for security_file in security_files:
            if self._check_file_exists(security_file, f"Security module: {security_file}"):
                self._validate_security_module(security_file)
        
        # Check for security configurations
        self._validate_security_configs()
    
    def validate_docker_setup(self):
        """Validate Docker setup."""
        print("🐳 Validating Docker setup...")
        
        # Check Docker files
        docker_files = [
            "Dockerfile",
            "docker-compose.yml",
            ".dockerignore"
        ]
        
        for docker_file in docker_files:
            if self._check_file_exists(docker_file, f"Docker file: {docker_file}"):
                self._validate_docker_file(docker_file)
    
    def validate_production_readiness(self):
        """Validate production readiness."""
        print("🚀 Validating production readiness...")
        
        # Check for production configurations
        prod_configs = [
            "config/nginx/nginx.conf",
            "docker-compose.prod.yml",
            ".env.prod"
        ]
        
        for config_file in prod_configs:
            if self._check_file_exists(config_file, f"Production config: {config_file}"):
                self._validate_production_config(config_file)
        
        # Check for logging configuration
        self._validate_logging_config()
    
    def _validate_security_module(self, security_file: str):
        """Validate security module content."""
        content = self._read_file_content(security_file)
        if not content:
            return
        
        # Check for security-related patterns
        has_encryption = any(keyword in content.lower() for keyword in [
            "encrypt", "hash", "cipher", "crypto", "secure"
        ])
        
        has_validation = any(keyword in content.lower() for keyword in [
            "validate", "sanitize", "clean", "filter"
        ])
        
        if has_encryption or has_validation:
            self._add_check_result(
                f"security_content_{security_file.replace('/', '_')}",
                "PASS",
                f"Security module {security_file} contains security logic"
            )
        else:
            self._add_check_result(
                f"security_content_{security_file.replace('/', '_')}",
                "WARN",
                f"Security module {security_file} may be missing security logic"
            )
    
    def _validate_security_configs(self):
        """Validate security configurations."""
        # Check for security-related environment variables
        env_example = self._read_file_content(".env.example")
        if env_example:
            security_vars = [
                "SECRET_KEY",
                "API_KEY",
                "JWT_SECRET",
                "ENCRYPTION_KEY"
            ]
            
            found_vars = [var for var in security_vars if var in env_example]
            
            if found_vars:
                self._add_check_result(
                    "security_env_vars",
                    "PASS",
                    f"Found security environment variables: {', '.join(found_vars)}"
                )
            else:
                self._add_check_result(
                    "security_env_vars",
                    "WARN",
                    "No security environment variables found in .env.example"
                )
    
    def _validate_docker_file(self, docker_file: str):
        """Validate Docker file."""
        content = self._read_file_content(docker_file)
        if not content:
            return
        
        # Check for security best practices
        has_user = "USER " in content
        has_workdir = "WORKDIR " in content
        has_expose = "EXPOSE " in content
        
        security_score = sum([has_user, has_workdir, has_expose])
        
        if security_score >= 2:
            self._add_check_result(
                f"docker_security_{docker_file.replace('/', '_')}",
                "PASS",
                f"Docker file {docker_file} follows security best practices"
            )
        else:
            self._add_check_result(
                f"docker_security_{docker_file.replace('/', '_')}",
                "WARN",
                f"Docker file {docker_file} may need security improvements"
            )
    
    def _validate_production_config(self, config_file: str):
        """Validate production configuration."""
        content = self._read_file_content(config_file)
        if not content:
            return
        
        # Check for production-specific settings
        has_ssl = "ssl" in content.lower() or "https" in content.lower()
        has_logging = "log" in content.lower()
        has_monitoring = any(keyword in content.lower() for keyword in [
            "monitor", "metrics", "health", "status"
        ])
        
        prod_features = sum([has_ssl, has_logging, has_monitoring])
        
        if prod_features >= 2:
            self._add_check_result(
                f"prod_config_{config_file.replace('/', '_')}",
                "PASS",
                f"Production config {config_file} has production features"
            )
        else:
            self._add_check_result(
                f"prod_config_{config_file.replace('/', '_')}",
                "WARN",
                f"Production config {config_file} may need more production features"
            )
    
    def _validate_logging_config(self):
        """Validate logging configuration."""
        # Check for logging in Python files
        python_files = list(self.project_root.rglob("*.py"))
        logging_files = []
        
        for py_file in python_files:
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue
            
            content = self._read_file_content(str(py_file.relative_to(self.project_root)))
            if content and ("import logging" in content or "logger" in content.lower()):
                logging_files.append(str(py_file.relative_to(self.project_root)))
        
        if logging_files:
            self._add_check_result(
                "logging_implementation",
                "PASS",
                f"Found logging in {len(logging_files)} files"
            )
        else:
            self._add_check_result(
                "logging_implementation",
                "WARN",
                "No logging implementation found"
            )
