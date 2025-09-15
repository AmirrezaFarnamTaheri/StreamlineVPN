#!/usr/bin/env python3
"""
Comprehensive Project Validator
===============================

Final validation script that ensures all fixes have been applied correctly
and the StreamlineVPN project is complete, consistent, and production-ready.
"""

import json
import os
import re
import sys
import ast
import yaml
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import subprocess
import importlib.util


class ComprehensiveValidator:
    """Comprehensive project validation with detailed reporting."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "validator_version": "2.0.0",
            "checks": {},
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "critical_errors": 0,
                "recommendations": []
            }
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """Run comprehensive validation suite."""
        print("🔍 Starting comprehensive project validation...")
        print("=" * 80)
        
        # Core structure validation
        self._validate_project_structure()
        self._validate_essential_files()
        self._validate_runner_scripts()
        
        # Code quality validation
        self._validate_backend_integration()
        self._validate_frontend_integration()
        self._validate_api_consistency()
        
        # Configuration validation
        self._validate_configuration_completeness()
        self._validate_environment_setup()
        self._validate_dependency_management()
        
        # Documentation validation
        self._validate_documentation_completeness()
        self._validate_api_documentation()
        
        # Deployment validation
        self._validate_docker_setup()
        self._validate_production_readiness()
        
        # Testing validation
        self._validate_test_coverage()
        self._validate_test_configuration()
        
        # Security validation
        self._validate_security_measures()
        
        # Performance validation
        self._validate_performance_configurations()
        
        # Calculate final summary
        self._calculate_final_summary()
        
        return self.validation_results
    
    def _validate_project_structure(self):
        """Validate project directory structure."""
        check_name = "project_structure"
        check = {"name": "Project Structure", "status": "checking", "issues": []}
        
        # Essential directories
        required_dirs = {
            "src/streamline_vpn": "Main package directory",
            "src/streamline_vpn/core": "Core processing modules",
            "src/streamline_vpn/web": "Web interface modules", 
            "src/streamline_vpn/models": "Data models",
            "src/streamline_vpn/utils": "Utility modules",
            "docs": "Documentation and frontend",
            "docs/assets": "Static assets",
            "docs/assets/css": "Stylesheets",
            "docs/assets/js": "JavaScript files",
            "config": "Configuration files",
            "tests": "Test suite",
            "scripts": "Utility scripts",
            "logs": "Log directory (can be created at runtime)"
        }
        
        # Essential files
        required_files = {
            "README.md": "Project documentation",
            "requirements.txt": "Python dependencies",
            "pyproject.toml": "Modern Python project config",
            "setup.py": "Backwards compatible setup",
            ".env.example": "Environment variables template",
            ".gitignore": "Git ignore rules",
            "run_unified.py": "Unified server runner",
            "run_api.py": "API server runner",
            "run_web.py": "Web server runner",
            "src/streamline_vpn/__init__.py": "Package initialization",
            "src/streamline_vpn/cli.py": "Command line interface",
            "config/sources.yaml": "VPN sources configuration",
            "docs/index.html": "Main landing page",
            "docs/interactive.html": "Control panel",
            "docs/config_generator.html": "Configuration generator",
            "docs/troubleshooting.html": "Troubleshooting guide",
            "docs/api-base.js": "Frontend API library",
            "docs/assets/js/main.js": "Main application JavaScript",
            "docs/assets/css/style.css": "Main stylesheet"
        }
        
        # Check directories
        for dir_path, description in required_dirs.items():
            full_path = self.project_root / dir_path
            if not full_path.exists():
                if dir_path == "logs":  # Logs directory is optional
                    check["issues"].append({
                        "type": "optional_directory_missing",
                        "severity": "info",
                        "path": dir_path,
                        "description": f"Optional directory missing: {description}"
                    })
                else:
                    check["issues"].append({
                        "type": "required_directory_missing",
                        "severity": "error",
                        "path": dir_path,
                        "description": f"Required directory missing: {description}"
                    })
        
        # Check files
        for file_path, description in required_files.items():
            full_path = self.project_root / file_path
            if not full_path.exists():
                check["issues"].append({
                    "type": "required_file_missing",
                    "severity": "error",
                    "path": file_path,
                    "description": f"Required file missing: {description}"
                })
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_essential_files(self):
        """Validate that essential files have proper content."""
        check_name = "essential_files"
        check = {"name": "Essential Files Content", "status": "checking", "issues": []}
        
        # Check README.md
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            try:
                readme_content = readme_path.read_text(encoding='utf-8')
                required_sections = [
                    "StreamlineVPN", "Features", "Installation", "Usage", "Configuration"
                ]
                for section in required_sections:
                    if section not in readme_content:
                        check["issues"].append({
                            "type": "missing_readme_section",
                            "severity": "warning",
                            "description": f"README missing section: {section}"
                        })
                
                if len(readme_content) < 2000:
                    check["issues"].append({
                        "type": "incomplete_readme",
                        "severity": "warning", 
                        "description": "README appears incomplete (too short)"
                    })
            except Exception as e:
                check["issues"].append({
                    "type": "readme_read_error",
                    "severity": "error",
                    "description": f"Could not read README.md: {e}"
                })
        
        # Check sources.yaml
        sources_path = self.project_root / "config" / "sources.yaml"
        if sources_path.exists():
            try:
                with open(sources_path, 'r', encoding='utf-8') as f:
                    sources_data = yaml.safe_load(f)
                
                if 'sources' not in sources_data:
                    check["issues"].append({
                        "type": "invalid_sources_config",
                        "severity": "error",
                        "description": "sources.yaml missing 'sources' section"
                    })
                
                source_count = 0
                for tier_data in sources_data.get('sources', {}).values():
                    if isinstance(tier_data, dict) and 'sources' in tier_data:
                        source_count += len(tier_data['sources'])
                
                if source_count < 10:
                    check["issues"].append({
                        "type": "insufficient_sources",
                        "severity": "warning",
                        "description": f"Only {source_count} sources configured, recommend more"
                    })
                
            except yaml.YAMLError as e:
                check["issues"].append({
                    "type": "sources_yaml_error",
                    "severity": "error",
                    "description": f"sources.yaml YAML error: {e}"
                })
            except Exception as e:
                check["issues"].append({
                    "type": "sources_validation_error",
                    "severity": "error",
                    "description": f"Could not validate sources.yaml: {e}"
                })
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_runner_scripts(self):
        """Validate runner scripts are complete and executable."""
        check_name = "runner_scripts"
        check = {"name": "Runner Scripts", "status": "checking", "issues": []}
        
        runners = ["run_unified.py", "run_api.py", "run_web.py"]
        
        for runner in runners:
            runner_path = self.project_root / runner
            if runner_path.exists():
                try:
                    content = runner_path.read_text(encoding='utf-8')
                    
                    # Check for essential components
                    required_patterns = [
                        r'import.*uvicorn',
                        r'def main\(',
                        r'if __name__ == ["\']__main__["\']:',
                    ]
                    
                    for pattern in required_patterns:
                        if not re.search(pattern, content):
                            check["issues"].append({
                                "type": "incomplete_runner",
                                "severity": "warning",
                                "file": runner,
                                "description": f"Runner may be incomplete - missing pattern: {pattern}"
                            })
                
                except Exception as e:
                    check["issues"].append({
                        "type": "runner_validation_error",
                        "severity": "error",
                        "file": runner,
                        "description": f"Could not validate runner: {e}"
                    })
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_backend_integration(self):
        """Validate backend components integration."""
        check_name = "backend_integration"
        check = {"name": "Backend Integration", "status": "checking", "issues": []}
        
        # Key backend files to check
        backend_files = {
            "src/streamline_vpn/web/unified_api.py": ["FastAPI", "StreamlineVPNMerger", "create_unified_app"],
            "src/streamline_vpn/core/merger.py": ["class.*StreamlineVPNMerger", "async.*def"],
            "src/streamline_vpn/cli.py": ["click", "@main.command", "StreamlineVPNCLI"],
        }
        
        for file_path, patterns in backend_files.items():
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    
                    for pattern in patterns:
                        if not re.search(pattern, content, re.IGNORECASE):
                            check["issues"].append({
                                "type": "missing_backend_component",
                                "severity": "warning",
                                "file": file_path,
                                "description": f"Missing expected pattern: {pattern}"
                            })
                    
                    # Check for common issues
                    if "TODO" in content or "FIXME" in content or "XXX" in content:
                        check["issues"].append({
                            "type": "unfinished_code",
                            "severity": "warning",
                            "file": file_path,
                            "description": "Contains TODO/FIXME comments"
                        })
                    
                except Exception as e:
                    check["issues"].append({
                        "type": "backend_validation_error",
                        "severity": "error",
                        "file": file_path,
                        "description": f"Could not validate backend file: {e}"
                    })
            else:
                check["issues"].append({
                    "type": "missing_backend_file",
                    "severity": "error",
                    "file": file_path,
                    "description": "Required backend file missing"
                })
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_frontend_integration(self):
        """Validate frontend integration."""
        check_name = "frontend_integration"
        check = {"name": "Frontend Integration", "status": "checking", "issues": []}
        
        # Check api-base.js
        api_base_path = self.project_root / "docs" / "api-base.js"
        if api_base_path.exists():
            try:
                content = api_base_path.read_text(encoding='utf-8')
                
                required_components = [
                    "window.API",
                    "request:",
                    "get:",
                    "post:",
                    "url:",
                    "init:",
                ]
                
                for component in required_components:
                    if component not in content:
                        check["issues"].append({
                            "type": "incomplete_api_base",
                            "severity": "error",
                            "description": f"api-base.js missing: {component}"
                        })
                
                # Check for syntax errors (basic)
                if content.count('{') != content.count('}'):
                    check["issues"].append({
                        "type": "syntax_error",
                        "severity": "error",
                        "file": "docs/api-base.js",
                        "description": "Mismatched braces in JavaScript"
                    })
                
            except Exception as e:
                check["issues"].append({
                    "type": "api_base_validation_error",
                    "severity": "error",
                    "description": f"Could not validate api-base.js: {e}"
                })
        else:
            check["issues"].append({
                "type": "missing_api_base",
                "severity": "error",
                "description": "Missing docs/api-base.js file"
            })
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_api_consistency(self):
        """Validate API consistency between backend and frontend."""
        check_name = "api_consistency"
        check = {"name": "API Consistency", "status": "checking", "issues": []}
        
        try:
            # Check for common API endpoints in documentation
            api_docs_path = self.project_root / "docs" / "api" / "index.html"
            if api_docs_path.exists():
                content = api_docs_path.read_text(encoding='utf-8')
                
                expected_endpoints = [
                    "/health",
                    "/api/v1/sources",
                    "/api/v1/configurations", 
                    "/api/v1/pipeline/run",
                    "/api/statistics"
                ]
                
                for endpoint in expected_endpoints:
                    if endpoint not in content:
                        check["issues"].append({
                            "type": "missing_api_documentation",
                            "severity": "warning",
                            "description": f"API endpoint not documented: {endpoint}"
                        })
            else:
                check["issues"].append({
                    "type": "missing_api_docs",
                    "severity": "warning",
                    "description": "API documentation not found"
                })
                
        except Exception as e:
            check["issues"].append({
                "type": "api_consistency_check_error",
                "severity": "warning",
                "description": f"Could not check API consistency: {e}"
            })
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_configuration_completeness(self):
        """Validate configuration completeness."""
        check_name = "configuration_completeness"
        check = {"name": "Configuration Completeness", "status": "checking", "issues": []}
        
        # Check .env.example
        env_example_path = self.project_root / ".env.example"
        if env_example_path.exists():
            try:
                content = env_example_path.read_text(encoding='utf-8')
                
                required_vars = [
                    "STREAMLINE_ENV",
                    "API_HOST",
                    "API_PORT", 
                    "WEB_HOST",
                    "WEB_PORT",
                    "STREAMLINE_LOG_LEVEL",
                    "CACHE_ENABLED",
                    "VPN_TIMEOUT",
                    "VPN_CONCURRENT_LIMIT"
                ]
                
                for var in required_vars:
                    if var not in content:
                        check["issues"].append({
                            "type": "missing_env_var",
                            "severity": "warning",
                            "description": f"Missing environment variable in .env.example: {var}"
                        })
                
            except Exception as e:
                check["issues"].append({
                    "type": "env_example_validation_error",
                    "severity": "error",
                    "description": f"Could not validate .env.example: {e}"
                })
        else:
            check["issues"].append({
                "type": "missing_env_example",
                "severity": "error",
                "description": ".env.example file missing"
            })
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_environment_setup(self):
        """Validate environment setup scripts and configurations."""
        check_name = "environment_setup"
        check = {"name": "Environment Setup", "status": "checking", "issues": []}
        
        # Check for proper gitignore
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            try:
                content = gitignore_path.read_text(encoding='utf-8')
                
                required_patterns = [
                    "__pycache__",
                    "*.pyc",
                    ".env",
                    ".venv",
                    "venv/",
                    "logs/",
                    ".DS_Store"
                ]
                
                for pattern in required_patterns:
                    if pattern not in content:
                        check["issues"].append({
                            "type": "missing_gitignore_pattern",
                            "severity": "info",
                            "description": f"Consider adding to .gitignore: {pattern}"
                        })
                
            except Exception as e:
                check["issues"].append({
                    "type": "gitignore_validation_error",
                    "severity": "warning",
                    "description": f"Could not validate .gitignore: {e}"
                })
        
        check["status"] = "passed"  # This check doesn't have critical failures
        self.validation_results["checks"][check_name] = check
    
    def _validate_dependency_management(self):
        """Validate dependency management."""
        check_name = "dependency_management"
        check = {"name": "Dependency Management", "status": "checking", "issues": []}
        
        # Check requirements.txt
        req_path = self.project_root / "requirements.txt"
        if req_path.exists():
            try:
                content = req_path.read_text(encoding='utf-8')
                lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
                
                if len(lines) < 10:
                    check["issues"].append({
                        "type": "insufficient_dependencies",
                        "severity": "warning",
                        "description": f"Only {len(lines)} dependencies listed, may be incomplete"
                    })
                
                # Check for essential dependencies
                essential_deps = ["fastapi", "uvicorn", "pydantic", "aiohttp", "redis", "PyYAML"]
                for dep in essential_deps:
                    if not any(dep.lower() in line.lower() for line in lines):
                        check["issues"].append({
                            "type": "missing_essential_dependency",
                            "severity": "warning", 
                            "description": f"Missing essential dependency: {dep}"
                        })
                
            except Exception as e:
                check["issues"].append({
                    "type": "requirements_validation_error",
                    "severity": "error",
                    "description": f"Could not validate requirements.txt: {e}"
                })
        else:
            check["issues"].append({
                "type": "missing_requirements",
                "severity": "error",
                "description": "requirements.txt file missing"
            })
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_documentation_completeness(self):
        """Validate documentation completeness."""
        check_name = "documentation_completeness"
        check = {"name": "Documentation Completeness", "status": "checking", "issues": []}
        
        # Check troubleshooting.html
        troubleshooting_path = self.project_root / "docs" / "troubleshooting.html"
        if troubleshooting_path.exists():
            try:
                content = troubleshooting_path.read_text(encoding='utf-8')
                
                expected_sections = [
                    "Installation Issues",
                    "API Issues", 
                    "Performance",
                    "Network",
                    "Diagnostics"
                ]
                
                for section in expected_sections:
                    if section not in content:
                        check["issues"].append({
                            "type": "missing_troubleshooting_section",
                            "severity": "info",
                            "description": f"Troubleshooting guide missing section: {section}"
                        })
                
                if len(content) < 5000:
                    check["issues"].append({
                        "type": "incomplete_troubleshooting",
                        "severity": "warning",
                        "description": "Troubleshooting guide appears incomplete"
                    })
                
            except Exception as e:
                check["issues"].append({
                    "type": "troubleshooting_validation_error",
                    "severity": "warning",
                    "description": f"Could not validate troubleshooting guide: {e}"
                })
        else:
            check["issues"].append({
                "type": "missing_troubleshooting_guide",
                "severity": "warning",
                "description": "Troubleshooting guide missing"
            })
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_api_documentation(self):
        """Validate API documentation."""
        check_name = "api_documentation"
        check = {"name": "API Documentation", "status": "checking", "issues": []}
        
        api_docs_path = self.project_root / "docs" / "api" / "index.html"
        if api_docs_path.exists():
            try:
                content = api_docs_path.read_text(encoding='utf-8')
                
                # Check for comprehensive sections
                expected_sections = [
                    "Authentication",
                    "Endpoints", 
                    "Error Codes",
                    "Rate Limits",
                    "Examples"
                ]
                
                for section in expected_sections:
                    if section not in content:
                        check["issues"].append({
                            "type": "missing_api_doc_section",
                            "severity": "warning",
                            "description": f"API documentation missing section: {section}"
                        })
                
                # Check for placeholder content
                if "Documentation In Progress" in content:
                    check["issues"].append({
                        "type": "api_docs_incomplete",
                        "severity": "warning", 
                        "description": "API documentation contains placeholder content"
                    })
                
                if len(content) < 10000:
                    check["issues"].append({
                        "type": "insufficient_api_documentation",
                        "severity": "info",
                        "description": "API documentation appears brief, consider expanding"
                    })
                
            except Exception as e:
                check["issues"].append({
                    "type": "api_docs_validation_error",
                    "severity": "error",
                    "description": f"Could not validate API documentation: {e}"
                })
    else:
            check["issues"].append({
                "type": "missing_api_documentation",
                "severity": "error",
                "description": "API documentation missing"
            })
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_docker_setup(self):
        """Validate Docker configuration."""
        check_name = "docker_setup"
        check = {"name": "Docker Setup", "status": "checking", "issues": []}
        
        # Check docker-compose files
        compose_files = ["docker-compose.yml", "docker-compose.production.yml", "docker-compose.dev.yml"]
        for compose_file in compose_files:
            compose_path = self.project_root / compose_file
            if compose_path.exists():
                try:
                    content = compose_path.read_text(encoding='utf-8')
                    
                    # Basic validation
                    if "version:" not in content or "services:" not in content:
                        check["issues"].append({
                            "type": "invalid_compose_file",
                            "severity": "error",
                            "file": compose_file,
                            "description": "Docker Compose file appears invalid"
                        })
                    
                except Exception as e:
                    check["issues"].append({
                        "type": "compose_validation_error",
                        "severity": "warning",
                        "file": compose_file,
                        "description": f"Could not validate compose file: {e}"
                    })
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_production_readiness(self):
        """Validate production readiness."""
        check_name = "production_readiness"
        check = {"name": "Production Readiness", "status": "checking", "issues": []}
        
        # Check for production configurations
        prod_files = [
            "docker-compose.production.yml",
            "config/nginx",
            ".env.production.example"
        ]
        
        for prod_file in prod_files:
            if not (self.project_root / prod_file).exists():
                check["issues"].append({
                    "type": "missing_production_file",
                    "severity": "info",
                    "file": prod_file,
                    "description": f"Production file missing: {prod_file}"
                })
        
        check["status"] = "passed"  # This check is informational
        self.validation_results["checks"][check_name] = check
    
    def _validate_test_coverage(self):
        """Validate test coverage."""
        check_name = "test_coverage"
        check = {"name": "Test Coverage", "status": "checking", "issues": []}
        
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.glob("test_*.py"))
            
            if len(test_files) < 5:
                check["issues"].append({
                    "type": "insufficient_tests",
                    "severity": "warning",
                    "description": f"Only {len(test_files)} test files found, consider adding more"
                })
    else:
            check["issues"].append({
                "type": "missing_tests_directory",
                "severity": "error",
                "description": "Tests directory missing"
            })
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_test_configuration(self):
        """Validate test configuration."""
        check_name = "test_configuration"
        check = {"name": "Test Configuration", "status": "checking", "issues": []}
        
        # Check conftest.py
        conftest_path = self.project_root / "tests" / "conftest.py"
        if conftest_path.exists():
            try:
                content = conftest_path.read_text(encoding='utf-8')
                
                # Check for async test support
                if "pytest_asyncio" not in content and "asyncio" not in content:
                    check["issues"].append({
                        "type": "missing_async_test_support",
                        "severity": "info",
                        "description": "Consider adding async test support in conftest.py"
                    })
                
            except Exception as e:
                check["issues"].append({
                    "type": "conftest_validation_error",
                    "severity": "warning",
                    "description": f"Could not validate conftest.py: {e}"
                })
        
        check["status"] = "passed"  # This check is informational
        self.validation_results["checks"][check_name] = check
    
    def _validate_security_measures(self):
        """Validate security measures."""
        check_name = "security_measures"
        check = {"name": "Security Measures", "status": "checking", "issues": []}
        
        # Check for .env in .gitignore
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            try:
                content = gitignore_path.read_text(encoding='utf-8')
                if ".env" not in content:
                    check["issues"].append({
                        "type": "env_not_ignored",
                        "severity": "warning",
                        "description": "Ensure .env is in .gitignore to prevent secret leaks"
                    })
            except Exception:
                pass
        
        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check
    
    def _validate_performance_configurations(self):
        """Validate performance configurations."""
        check_name = "performance_configurations"
        check = {"name": "Performance Configurations", "status": "checking", "issues": []}
        
        # Check .env.example for performance settings
        env_example_path = self.project_root / ".env.example"
        if env_example_path.exists():
            try:
                content = env_example_path.read_text(encoding='utf-8')
                
                perf_settings = [
                    "VPN_CONCURRENT_LIMIT",
                    "VPN_TIMEOUT", 
                    "CACHE_ENABLED",
                    "CACHE_TTL"
                ]
                
                for setting in perf_settings:
                    if setting not in content:
                        check["issues"].append({
                            "type": "missing_performance_setting",
                            "severity": "info",
                            "description": f"Consider adding performance setting: {setting}"
                        })
                
            except Exception:
                pass
        
        check["status"] = "passed"  # This check is informational
        self.validation_results["checks"][check_name] = check
    
    def _calculate_final_summary(self):
        """Calculate final validation summary."""
        total_checks = len(self.validation_results["checks"])
        passed = sum(1 for check in self.validation_results["checks"].values() if check["status"] == "passed")
        failed = total_checks - passed
        
        # Count issues by severity
    warnings = 0
        critical_errors = 0
        
        for check in self.validation_results["checks"].values():
            for issue in check.get("issues", []):
                if issue["severity"] == "warning":
                warnings += 1
                elif issue["severity"] == "error":
                    critical_errors += 1
        
        # Generate recommendations
        recommendations = []
        
        if critical_errors > 0:
            recommendations.append("Fix critical errors before deployment")
        
        if warnings > 5:
            recommendations.append("Consider addressing warnings for better quality")
        
        if failed > total_checks * 0.2:
            recommendations.append("Project needs significant cleanup before production use")
        elif failed == 0:
            recommendations.append("Project appears ready for production deployment")
        else:
            recommendations.append("Project is mostly ready with minor issues to address")
        
        # Update summary
        self.validation_results["summary"].update({
            "total_checks": total_checks,
            "passed": passed,
        "failed": failed,
        "warnings": warnings,
            "critical_errors": critical_errors,
            "recommendations": recommendations
        })
    
    def generate_report(self) -> str:
        """Generate a comprehensive validation report."""
        results = self.validation_results
        summary = results["summary"]
        
        report = f"""
# StreamlineVPN Project Validation Report
Generated: {results['timestamp']}
Validator Version: {results['validator_version']}
Project Root: {results['project_root']}

## Summary
- Total Checks: {summary['total_checks']}
- Passed: {summary['passed']}
- Failed: {summary['failed']} 
- Warnings: {summary['warnings']}
- Critical Errors: {summary['critical_errors']}
- Overall Status: {'✅ PASS' if summary['failed'] == 0 else '❌ FAIL' if summary['critical_errors'] > 0 else '⚠️ NEEDS ATTENTION'}

## Recommendations
"""
        
        for rec in summary["recommendations"]:
            report += f"- {rec}\n"
        
        report += "\n## Detailed Results\n\n"
        
        for check_name, check_data in results["checks"].items():
            status_icon = "✅" if check_data["status"] == "passed" else "❌"
            report += f"### {status_icon} {check_data['name']}\n"
            
            if check_data.get("issues"):
                for issue in check_data["issues"]:
                    severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(issue["severity"], "⚪")
                    report += f"- {severity_icon} **{issue['severity'].upper()}**: {issue['description']}\n"
                    if "file" in issue:
                        report += f"  - File: `{issue['file']}`\n"
            else:
                report += "- No issues found\n"
            
            report += "\n"
        
        return report


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive StreamlineVPN Project Validator")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output", help="Output file for validation report")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    
    args = parser.parse_args()
    
    # Run validation
    validator = ComprehensiveValidator(args.project_root)
    results = validator.validate_all()
    
    # Generate output
    if args.format == "json":
        output = json.dumps(results, indent=2)
    else:
        output = validator.generate_report()
    
    # Save or print results
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Validation report saved to: {args.output}")
    else:
        print(output)
    
    # Exit with appropriate code
    summary = results["summary"]
    if summary["critical_errors"] > 0:
        sys.exit(2)  # Critical errors
    elif summary["failed"] > 0:
        sys.exit(1)  # Some failures
        else:
        sys.exit(0)  # Success


if __name__ == "__main__":
    main()