#!/usr/bin/env python3
"""
StreamlineVPN Project Validator
===============================

Comprehensive validation script that checks all aspects of the StreamlineVPN project
for completeness, correctness, and adherence to best practices.
"""

import os
import sys
import json
import yaml
import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import tempfile
from datetime import datetime
import importlib.util


class ProjectValidator:
    """Comprehensive project validation system."""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.src_root = self.project_root / "src" / "streamline_vpn"
        self.docs_root = self.project_root / "docs"
        self.config_root = self.project_root / "config"
        self.tests_root = self.project_root / "tests"

        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "checks": {},
            "summary": {
                "total_checks": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "errors": []
            }
        }

    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("🔍 Starting comprehensive project validation...")

        # Core validation checks
        self._validate_project_structure()
        self._validate_python_code()
        self._validate_configuration_files()
        self._validate_frontend_assets()
        self._validate_documentation()
        self._validate_docker_setup()
        self._validate_dependencies()
        self._validate_tests()
        self._validate_api_consistency()
        self._validate_security()

        # Calculate summary
        self._calculate_summary()

        return self.validation_results

    def _validate_project_structure(self):
        """Validate project directory structure and essential files."""
        check_name = "project_structure"
        check = {"name": "Project Structure", "status": "checking", "issues": []}

        # Required files and directories
        required_files = [
            "README.md",
            "requirements.txt",
            "setup.py",
            ".gitignore",
            "src/streamline_vpn/__init__.py",
            "config/sources.yaml",
            "docs/index.html",
            "run_unified.py",
            "run_api.py",
            "run_web.py"
        ]

        required_dirs = [
            "src/streamline_vpn",
            "src/streamline_vpn/core",
            "src/streamline_vpn/web",
            "docs",
            "docs/assets",
            "docs/assets/css",
            "docs/assets/js",
            "config",
            "tests"
        ]

        # Check required files
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        if missing_files:
            check["issues"].append({
                "type": "missing_files",
                "severity": "error",
                "description": f"Missing required files: {', '.join(missing_files)}"
            })

        # Check required directories
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)

        if missing_dirs:
            check["issues"].append({
                "type": "missing_directories",
                "severity": "error",
                "description": f"Missing required directories: {', '.join(missing_dirs)}"
            })

        # Check file permissions
        executable_files = ["run_unified.py", "run_api.py", "run_web.py"]
        for file_name in executable_files:
            file_path = self.project_root / file_name
            if file_path.exists() and not os.access(file_path, os.X_OK):
                check["issues"].append({
                    "type": "file_permissions",
                    "severity": "warning",
                    "description": f"File {file_name} should be executable"
                })

        check["status"] = "passed" if not check["issues"] else "failed"
        self.validation_results["checks"][check_name] = check

    def _validate_python_code(self):
        """Validate Python code quality and consistency."""
        check_name = "python_code"
        check = {"name": "Python Code Quality", "status": "checking", "issues": []}

        if not self.src_root.exists():
            check["issues"].append({
                "type": "missing_source",
                "severity": "error",
                "description": "Source directory not found"
            })
            check["status"] = "failed"
            self.validation_results["checks"][check_name] = check
            return

        python_files = list(self.src_root.rglob("*.py"))

        for file_path in python_files:
            try:
                # Check syntax
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    ast.parse(content)
                except SyntaxError as e:
                    check["issues"].append({
                        "type": "syntax_error",
                        "severity": "error",
                        "file": str(file_path.relative_to(self.project_root)),
                        "line": e.lineno,
                        "description": f"Syntax error: {e.msg}"
                    })

                # Check for legacy imports
                legacy_imports = [
                    "from vpn_merger",
                    "import vpn_merger",
                    "VPNSubscriptionMerger"
                ]

                # Check for legacy imports
                legacy_imports = [
                    "from vpn_merger",
                    "import vpn_merger",
                    "VPNSubscriptionMerger"
                ]

                for line_num, line in enumerate(content.split('\n'), 1):
                    for legacy in legacy_imports:
                        if legacy in line and not line.strip().startswith('#'):
                            check["issues"].append({
                                "type": "legacy_import",
                                "severity": "error",
                                "file": str(file_path.relative_to(self.project_root)),
                                "line": line_num,
                                "description": f"Legacy import found: {legacy}"
                            })

                # Check for TODO/FIXME/HACK comments
                todo_patterns = [r'TODO:', r'FIXME:', r'HACK:', r'XXX:']
                for line_num, line in enumerate(content.split('\n'), 1):
                    for pattern in todo_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            check["issues"].append({
                                "type": "todo_found",
                                "severity": "warning",
                                "file": str(file_path.relative_to(self.project_root)),
                                "line": line_num,
                                "description": f"TODO/FIXME found: {line.strip()}"
                            })

                # Check for missing docstrings
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                            if (not ast.get_docstring(node) and
                                not node.name.startswith('_') and
                                node.name not in ['__init__', '__str__', '__repr__']):
                                check["issues"].append({
                                    "type": "missing_docstring",
                                    "severity": "warning",
                                    "file": str(file_path.relative_to(self.project_root)),
                                    "line": node.lineno,
                                    "description": f"Missing docstring for {node.__class__.__name__.lower()}: {node.name}"
                                })
                except:
                    pass  # Skip AST analysis if it fails

            except Exception as e:
                check["issues"].append({
                    "type": "file_read_error",
                    "severity": "error",
                    "file": str(file_path.relative_to(self.project_root)),
                    "description": f"Could not read file: {e}"
                })

        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check

    def _validate_configuration_files(self):
        """Validate configuration files and their content."""
        check_name = "configuration"
        check = {"name": "Configuration Files", "status": "checking", "issues": []}

        # Check sources.yaml
        sources_file = self.config_root / "sources.yaml"
        if sources_file.exists():
            try:
                with open(sources_file, 'r', encoding='utf-8') as f:
                    sources_config = yaml.safe_load(f)

                # Validate structure
                if not isinstance(sources_config, dict):
                    check["issues"].append({
                        "type": "invalid_yaml_structure",
                        "severity": "error",
                        "file": "config/sources.yaml",
                        "description": "Root element must be a dictionary"
                    })
                elif 'sources' not in sources_config:
                    check["issues"].append({
                        "type": "missing_sources_key",
                        "severity": "error",
                        "file": "config/sources.yaml",
                        "description": "Missing 'sources' key in configuration"
                    })
                else:
                    # Validate sources structure
                    sources = sources_config['sources']
                    if not isinstance(sources, dict):
                        check["issues"].append({
                            "type": "invalid_sources_structure",
                            "severity": "error",
                            "file": "config/sources.yaml",
                            "description": "Sources must be a dictionary"
                        })
                    else:
                        # Check each tier
                        for tier_name, tier_data in sources.items():
                            if not isinstance(tier_data, dict):
                                check["issues"].append({
                                    "type": "invalid_tier_structure",
                                    "severity": "error",
                                    "file": "config/sources.yaml",
                                    "description": f"Tier '{tier_name}' must be a dictionary"
                                })
                                continue

                            if 'urls' not in tier_data:
                                check["issues"].append({
                                    "type": "missing_urls_key",
                                    "severity": "error",
                                    "file": "config/sources.yaml",
                                    "description": f"Tier '{tier_name}' is missing 'urls' key"
                                })
                                continue

                            tier_sources = tier_data.get('urls', [])
                            if not isinstance(tier_sources, list):
                                check["issues"].append({
                                    "type": "invalid_tier_structure",
                                    "severity": "error",
                                    "file": "config/sources.yaml",
                                    "description": f"URLs for tier '{tier_name}' must be a list"
                                })
                            else:
                                # Validate URLs
                                for i, source_config in enumerate(tier_sources):
                                    source_url = None
                                    if isinstance(source_config, str):
                                        source_url = source_config
                                    elif isinstance(source_config, dict):
                                        source_url = source_config.get('url')
                                    else:
                                         check["issues"].append({
                                            "type": "invalid_url_type",
                                            "severity": "error",
                                            "file": "config/sources.yaml",
                                            "description": f"Source config in {tier_name}[{i}] must be a string or dictionary"
                                        })
                                         continue

                                    if not source_url or not isinstance(source_url, str):
                                        check["issues"].append({
                                            "type": "invalid_url_type",
                                            "severity": "error",
                                            "file": "config/sources.yaml",
                                            "description": f"URL in {tier_name}[{i}] must be a string and not empty"
                                        })
                                    elif not re.match(r'https?://', source_url):
                                        check["issues"].append({
                                            "type": "invalid_url_format",
                                            "severity": "warning",
                                            "file": "config/sources.yaml",
                                            "description": f"URL in {tier_name}[{i}] should start with http:// or https://"
                                        })

            except yaml.YAMLError as e:
                check["issues"].append({
                    "type": "yaml_parse_error",
                    "severity": "error",
                    "file": "config/sources.yaml",
                    "description": f"YAML parse error: {e}"
                })
            except Exception as e:
                check["issues"].append({
                    "type": "file_read_error",
                    "severity": "error",
                    "file": "config/sources.yaml",
                    "description": f"Could not read file: {e}"
                })
        else:
            check["issues"].append({
                "type": "missing_config",
                "severity": "error",
                "description": "Missing config/sources.yaml file"
            })

        # Check environment file examples
        env_examples = [".env.example", ".env.development", ".env.production"]
        for env_file in env_examples:
            env_path = self.project_root / env_file
            if env_path.exists():
                try:
                    with open(env_path, 'r', encoding='utf-8') as f:
                        env_content = f.read()

                    # Check for required environment variables
                    required_vars = [
                        "API_HOST", "API_PORT", "WEB_HOST", "WEB_PORT",
                        "STREAMLINE_ENV", "STREAMLINE_LOG_LEVEL"
                    ]

                    for var in required_vars:
                        if var not in env_content:
                            check["issues"].append({
                                "type": "missing_env_var",
                                "severity": "warning",
                                "file": env_file,
                                "description": f"Missing environment variable: {var}"
                            })

                except Exception as e:
                    check["issues"].append({
                        "type": "env_file_error",
                        "severity": "warning",
                        "file": env_file,
                        "description": f"Could not read environment file: {e}"
                    })

        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check

    def _validate_frontend_assets(self):
        """Validate frontend HTML, CSS, and JavaScript files."""
        check_name = "frontend_assets"
        check = {"name": "Frontend Assets", "status": "checking", "issues": []}

        # Check required HTML files
        required_html = [
            "index.html",
            "interactive.html",
            "config_generator.html",
            "troubleshooting.html"
        ]

        for html_file in required_html:
            html_path = self.docs_root / html_file
            if not html_path.exists():
                check["issues"].append({
                    "type": "missing_html",
                    "severity": "error",
                    "description": f"Missing HTML file: docs/{html_file}"
                })
            else:
                try:
                    with open(html_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()

                    # Check for basic HTML structure
                    if not re.search(r'<!DOCTYPE html>', html_content, re.IGNORECASE):
                        check["issues"].append({
                            "type": "missing_doctype",
                            "severity": "warning",
                            "file": f"docs/{html_file}",
                            "description": "Missing DOCTYPE declaration"
                        })

                    # Check for incomplete HTML
                    if html_content.count('<html') != html_content.count('</html>'):
                        check["issues"].append({
                            "type": "unclosed_html_tag",
                            "severity": "error",
                            "file": f"docs/{html_file}",
                            "description": "HTML tag not properly closed"
                        })

                    if html_content.count('<body') != html_content.count('</body>'):
                        check["issues"].append({
                            "type": "unclosed_body_tag",
                            "severity": "error",
                            "file": f"docs/{html_file}",
                            "description": "Body tag not properly closed"
                        })

                    # Check for API base script inclusion
                    if html_file in ['interactive.html', 'config_generator.html']:
                        if 'api-base.js' not in html_content:
                            check["issues"].append({
                                "type": "missing_api_base",
                                "severity": "error",
                                "file": f"docs/{html_file}",
                                "description": "Missing api-base.js script inclusion"
                            })

                    # Check for placeholder content
                    placeholders = [
                        "example.com", "test.com"
                    ]

                    for placeholder in placeholders:
                        if placeholder in html_content:
                            check["issues"].append({
                                "type": "placeholder_content",
                                "severity": "warning",
                                "file": f"docs/{html_file}",
                                "description": f"Contains placeholder content: {placeholder}"
                            })

                except Exception as e:
                    check["issues"].append({
                        "type": "html_read_error",
                        "severity": "error",
                        "file": f"docs/{html_file}",
                        "description": f"Could not read HTML file: {e}"
                    })

        # Check CSS files
        css_path = self.docs_root / "assets" / "css" / "style.css"
        if css_path.exists():
            try:
                with open(css_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()

                # Check for CSS syntax issues (basic check)
                if css_content.count('{') != css_content.count('}'):
                    check["issues"].append({
                        "type": "css_syntax_error",
                        "severity": "error",
                        "file": "docs/assets/css/style.css",
                        "description": "Mismatched CSS braces"
                    })

                # Check for responsive design
                if '@media' not in css_content:
                    check["issues"].append({
                        "type": "missing_responsive_design",
                        "severity": "warning",
                        "file": "docs/assets/css/style.css",
                        "description": "No responsive design media queries found"
                    })

            except Exception as e:
                check["issues"].append({
                    "type": "css_read_error",
                    "severity": "error",
                    "file": "docs/assets/css/style.css",
                    "description": f"Could not read CSS file: {e}"
                })
        else:
            check["issues"].append({
                "type": "missing_css",
                "severity": "error",
                "description": "Missing main stylesheet: docs/assets/css/style.css"
            })

        # Check JavaScript files
        js_files = ["api-base.js", "assets/js/main.js"]
        for js_file in js_files:
            js_path = self.docs_root / js_file
            if js_path.exists():
                try:
                    with open(js_path, 'r', encoding='utf-8') as f:
                        js_content = f.read()

                    # Check for JavaScript syntax issues (basic check)
                    if js_content.count('{') != js_content.count('}'):
                        check["issues"].append({
                            "type": "js_syntax_error",
                            "severity": "warning",
                            "file": f"docs/{js_file}",
                            "description": "Possible JavaScript syntax issue (mismatched braces)"
                        })

                    # Check for console.log statements (should be warnings in production)
                    if 'console.log(' in js_content:
                        check["issues"].append({
                            "type": "debug_code",
                            "severity": "info",
                            "file": f"docs/{js_file}",
                            "description": "Contains console.log statements (consider removing for production)"
                        })

                except Exception as e:
                    check["issues"].append({
                        "type": "js_read_error",
                        "severity": "error",
                        "file": f"docs/{js_file}",
                        "description": f"Could not read JavaScript file: {e}"
                    })
            elif js_file == "api-base.js":  # This file is critical
                check["issues"].append({
                    "type": "missing_critical_js",
                    "severity": "error",
                    "description": f"Missing critical JavaScript file: docs/{js_file}"
                })

        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check

    def _validate_documentation(self):
        """Validate documentation completeness and quality."""
        check_name = "documentation"
        check = {"name": "Documentation", "status": "checking", "issues": []}

        # Check README.md
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()

                # Check for required sections
                required_sections = [
                    "# StreamlineVPN", "## Features", "## Installation",
                    "## Usage", "## Configuration"
                ]

                for section in required_sections:
                    if section not in readme_content:
                        check["issues"].append({
                            "type": "missing_readme_section",
                            "severity": "warning",
                            "file": "README.md",
                            "description": f"Missing section: {section}"
                        })

                # Check for placeholder content
                    check["issues"].append({
                        "type": "incomplete_readme",
                        "severity": "warning",
                        "file": "README.md",
                        "description": "README contains placeholder content"
                    })

                # Check length (should be substantial)
                if len(readme_content) < 1000:
                    check["issues"].append({
                        "type": "short_readme",
                        "severity": "warning",
                        "file": "README.md",
                        "description": "README is quite short, consider adding more details"
                    })

            except Exception as e:
                check["issues"].append({
                    "type": "readme_read_error",
                    "severity": "error",
                    "file": "README.md",
                    "description": f"Could not read README: {e}"
                })
        else:
            check["issues"].append({
                "type": "missing_readme",
                "severity": "error",
                "description": "Missing README.md file"
            })

        # Check API documentation
        api_docs = self.docs_root / "api"
        if api_docs.exists():
            api_files = list(api_docs.glob("*.md"))
            if not api_files:
                check["issues"].append({
                    "type": "empty_api_docs",
                    "severity": "warning",
                    "description": "API documentation directory exists but contains no files"
                })
        else:
            check["issues"].append({
                "type": "missing_api_docs",
                "severity": "warning",
                "description": "Missing API documentation directory"
            })

        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check

    def _validate_docker_setup(self):
        """Validate Docker configuration and setup."""
        check_name = "docker_setup"
        check = {"name": "Docker Setup", "status": "checking", "issues": []}

        # Check Dockerfile
        dockerfile_path = self.project_root / "Dockerfile"
        if dockerfile_path.exists():
            try:
                with open(dockerfile_path, 'r', encoding='utf-8') as f:
                    dockerfile_content = f.read()

                # Check for best practices
                if "COPY . ." in dockerfile_content:
                    check["issues"].append({
                        "type": "docker_copy_all",
                        "severity": "warning",
                        "file": "Dockerfile",
                        "description": "Using 'COPY . .' may include unnecessary files, consider using .dockerignore"
                    })

                if "USER" not in dockerfile_content:
                    check["issues"].append({
                        "type": "docker_no_user",
                        "severity": "warning",
                        "file": "Dockerfile",
                        "description": "Running as root, consider adding USER instruction"
                    })

                if "HEALTHCHECK" not in dockerfile_content:
                    check["issues"].append({
                        "type": "docker_no_healthcheck",
                        "severity": "info",
                        "file": "Dockerfile",
                        "description": "Consider adding HEALTHCHECK instruction"
                    })

            except Exception as e:
                check["issues"].append({
                    "type": "dockerfile_read_error",
                    "severity": "error",
                    "file": "Dockerfile",
                    "description": f"Could not read Dockerfile: {e}"
                })
        else:
            check["issues"].append({
                "type": "missing_dockerfile",
                "severity": "info",
                "description": "Missing Dockerfile (optional for non-containerized deployment)"
            })

        # Check docker-compose files
        compose_files = ["docker-compose.yml", "docker-compose.yaml", "docker-compose.production.yml"]
        compose_found = False

        for compose_file in compose_files:
            compose_path = self.project_root / compose_file
            if compose_path.exists():
                compose_found = True
                try:
                    with open(compose_path, 'r', encoding='utf-8') as f:
                        compose_content = f.read()

                    # Basic YAML validation
                    yaml.safe_load(compose_content)

                    # Check for version
                    if not re.search(r'version:', compose_content):
                        check["issues"].append({
                            "type": "docker_compose_no_version",
                            "severity": "warning",
                            "file": compose_file,
                            "description": "Docker Compose file should specify version"
                        })

                except yaml.YAMLError as e:
                    check["issues"].append({
                        "type": "docker_compose_yaml_error",
                        "severity": "error",
                        "file": compose_file,
                        "description": f"YAML error in Docker Compose file: {e}"
                    })
                except Exception as e:
                    check["issues"].append({
                        "type": "docker_compose_read_error",
                        "severity": "error",
                        "file": compose_file,
                        "description": f"Could not read Docker Compose file: {e}"
                    })

        if not compose_found:
            check["issues"].append({
                "type": "missing_docker_compose",
                "severity": "info",
                "description": "No Docker Compose file found (optional)"
            })

        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check

    def _read_requirements_recursive(self, file_path: Path, visited: set) -> str:
        if file_path in visited or not file_path.exists():
            return ""
        visited.add(file_path)

        content = ""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('-r'):
                    # Handle both absolute and relative paths in -r
                    include_path_str = line.split(maxsplit=1)[1]
                    include_path = Path(include_path_str)
                    if not include_path.is_absolute():
                        include_path = file_path.parent / include_path

                    content += self._read_requirements_recursive(include_path.resolve(), visited)
                elif not line.startswith('#'):
                    content += line + '\n'
        return content

    def _validate_dependencies(self):
        """Validate dependency files and their consistency."""
        check_name = "dependencies"
        check = {"name": "Dependencies", "status": "checking", "issues": []}

        # Check requirements files
        req_files = [
            ("requirements.txt", "error"),
            ("requirements-prod.txt", "warning"),
            ("requirements-dev.txt", "warning"),
            ("setup.py", "warning")
        ]

        found_req_files = []

        for req_file, severity in req_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                found_req_files.append(req_file)
                try:
                    req_content = self._read_requirements_recursive(req_path, set())

                    if req_file.endswith('.txt'):
                        # Check for basic dependencies
                        essential_deps = ['fastapi', 'aiohttp', 'uvicorn', 'pydantic']
                        missing_deps = []

                        for dep in essential_deps:
                            if dep not in req_content.lower():
                                missing_deps.append(dep)

                        if missing_deps:
                            check["issues"].append({
                                "type": "missing_essential_deps",
                                "severity": "warning",
                                "file": req_file,
                                "description": f"Missing essential dependencies: {', '.join(missing_deps)}"
                            })

                        # Check for version pinning in production
                        if req_file == "requirements-prod.txt":
                            lines = [line.strip() for line in req_content.split('\n')
                                   if line.strip() and not line.startswith('#')]
                            unpinned = [line for line in lines if '==' not in line and '>=' not in line]

                            if unpinned:
                                check["issues"].append({
                                    "type": "unpinned_prod_deps",
                                    "severity": "warning",
                                    "file": req_file,
                                    "description": f"Production dependencies should be pinned: {', '.join(unpinned[:5])}"
                                })

                except Exception as e:
                    check["issues"].append({
                        "type": "req_file_read_error",
                        "severity": severity,
                        "file": req_file,
                        "description": f"Could not read requirements file: {e}"
                    })
            else:
                if severity == "error":
                    check["issues"].append({
                        "type": "missing_req_file",
                        "severity": severity,
                        "description": f"Missing required file: {req_file}"
                    })

        # Check for dependency conflicts (if pip-compile is available)
        if len(found_req_files) > 1:
            # This is a placeholder for more advanced dependency analysis
            pass

        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check

    def _validate_tests(self):
        """Validate test suite completeness and quality."""
        check_name = "tests"
        check = {"name": "Test Suite", "status": "checking", "issues": []}

        if not self.tests_root.exists():
            check["issues"].append({
                "type": "missing_tests_dir",
                "severity": "warning",
                "description": "No tests directory found"
            })
            check["status"] = "failed"
            self.validation_results["checks"][check_name] = check
            return

        # Find test files
        test_files = list(self.tests_root.glob("test_*.py")) + list(self.tests_root.glob("*_test.py"))

        if not test_files:
            check["issues"].append({
                "type": "no_test_files",
                "severity": "warning",
                "description": "No test files found in tests directory"
            })
        else:
            # Check test file quality
            for test_file in test_files:
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        test_content = f.read()

                    # Check for async test issues
                    if 'AsyncMock' in test_content and 'await' not in test_content:
                        check["issues"].append({
                            "type": "async_mock_not_awaited",
                            "severity": "warning",
                            "file": str(test_file.relative_to(self.project_root)),
                            "description": "AsyncMock used but no await found - possible test issue"
                        })

                    # Check for test function naming
                    import re
                    test_functions = re.findall(r'def (test_\w+)', test_content)
                    if not test_functions:
                        check["issues"].append({
                            "type": "no_test_functions",
                            "severity": "warning",
                            "file": str(test_file.relative_to(self.project_root)),
                            "description": "No test functions found (functions should start with 'test_')"
                        })

                except Exception as e:
                    check["issues"].append({
                        "type": "test_file_read_error",
                        "severity": "error",
                        "file": str(test_file.relative_to(self.project_root)),
                        "description": f"Could not read test file: {e}"
                    })

        # Check for pytest configuration
        pytest_configs = ["pytest.ini", "pyproject.toml", "setup.cfg"]
        pytest_config_found = any((self.project_root / config).exists() for config in pytest_configs)

        if not pytest_config_found:
            check["issues"].append({
                "type": "no_pytest_config",
                "severity": "info",
                "description": "No pytest configuration found (pytest.ini, pyproject.toml, or setup.cfg)"
            })

        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check

    def _validate_api_consistency(self):
        """Validate API consistency between backend and frontend."""
        check_name = "api_consistency"
        check = {"name": "API Consistency", "status": "checking", "issues": []}

        # Check FastAPI routes
        unified_api_file = self.src_root / "web" / "unified_api.py"
        frontend_files = [
            self.docs_root / "assets" / "js" / "main.js",
            self.docs_root / "assets" / "js" / "app.js",
            self.docs_root / "interactive.html",
            self.docs_root / "config_generator.html"
        ]

        if unified_api_file.exists():
            try:
                with open(unified_api_file, 'r', encoding='utf-8') as f:
                    api_content = f.read()

                # Extract API endpoints
                api_routes = re.findall(r'@\w+\.(?:get|post|put|delete)\("([^"]+)"', api_content)

                # Check frontend API calls
                for frontend_file in frontend_files:
                    if frontend_file.exists():
                        with open(frontend_file, 'r', encoding='utf-8') as f:
                            frontend_content = f.read()

                        # Find API calls
                        api_calls = re.findall(r'(?:API\.get|API\.post|fetch)\s*\(\s*["\']([^"\']+)["\']', frontend_content)

                        # Check for missing endpoints
                        for call in api_calls:
                            if call not in api_routes and not call.startswith('http'):
                                check["issues"].append({
                                    "type": "missing_api_endpoint",
                                    "severity": "warning",
                                    "file": str(frontend_file.relative_to(self.project_root)),
                                    "description": f"Frontend calls API endpoint '{call}' but it's not defined in backend"
                                })

            except Exception as e:
                check["issues"].append({
                    "type": "api_validation_error",
                    "severity": "error",
                    "description": f"Error validating API consistency: {e}"
                })

        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check

    def _validate_security(self):
        """Validate security best practices and configurations."""
        check_name = "security"
        check = {"name": "Security", "status": "checking", "issues": []}

        # Check for hardcoded secrets
        sensitive_files = []
        for file_path in self.project_root.rglob("*.py"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for potential hardcoded secrets
                secret_patterns = [
                    r'password\s*=\s*["\'][^"\']{8,}["\']',
                    r'api_key\s*=\s*["\'][^"\']{20,}["\']',
                    r'secret\s*=\s*["\'][^"\']{16,}["\']',
                    r'token\s*=\s*["\'][^"\']{20,}["\']'
                ]

                for pattern in secret_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if 'example' not in match.group().lower() and 'placeholder' not in match.group().lower():
                            check["issues"].append({
                                "type": "potential_hardcoded_secret",
                                "severity": "error",
                                "file": str(file_path.relative_to(self.project_root)),
                                "description": f"Potential hardcoded secret: {match.group()[:30]}..."
                            })

            except Exception:
                pass  # Skip files that can't be read

        # Check .env files for security
        env_files = [".env", ".env.local", ".env.production"]
        for env_file in env_files:
            env_path = self.project_root / env_file
            if env_path.exists():
                check["issues"].append({
                    "type": "env_file_in_repo",
                    "severity": "warning",
                    "file": env_file,
                    "description": "Environment file found in repository - ensure it's in .gitignore"
                })

        # Check .gitignore for security-sensitive files
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    gitignore_content = f.read()

                security_patterns = [".env", "*.key", "*.pem", "secrets/", "config/*.local"]
                missing_patterns = [pattern for pattern in security_patterns if pattern not in gitignore_content]

                if missing_patterns:
                    check["issues"].append({
                        "type": "missing_gitignore_security",
                        "severity": "warning",
                        "file": ".gitignore",
                        "description": f"Consider adding security patterns: {', '.join(missing_patterns)}"
                    })

            except Exception as e:
                check["issues"].append({
                    "type": "gitignore_read_error",
                    "severity": "warning",
                    "file": ".gitignore",
                    "description": f"Could not read .gitignore: {e}"
                })

        check["status"] = "passed" if not any(issue["severity"] == "error" for issue in check["issues"]) else "failed"
        self.validation_results["checks"][check_name] = check

    def _calculate_summary(self):
        """Calculate validation summary statistics."""
        summary = self.validation_results["summary"]
        summary["total_checks"] = len(self.validation_results["checks"])

        for check_data in self.validation_results["checks"].values():
            if check_data["status"] == "passed":
                summary["passed"] += 1
            else:
                summary["failed"] += 1

            # Count issues by severity
            for issue in check_data.get("issues", []):
                if issue["severity"] == "warning":
                    summary["warnings"] += 1
                elif issue["severity"] == "error":
                    summary["errors"].append({
                        "check": check_data["name"],
                        "description": issue["description"]
                    })

    def generate_report(self) -> str:
        """Generate a human-readable validation report."""
        results = self.validation_results
        summary = results["summary"]

        report_lines = [
            "StreamlineVPN Project Validation Report",
            "=" * 50,
            f"Generated: {results['timestamp']}",
            f"Project Root: {results['project_root']}",
            "",
            "SUMMARY",
            "-" * 20,
            f"Total Checks: {summary['total_checks']}",
            f"✅ Passed: {summary['passed']}",
            f"❌ Failed: {summary['failed']}",
            f"⚠️  Warnings: {summary['warnings']}",
            f"🚨 Errors: {len(summary['errors'])}",
            ""
        ]

        if summary["errors"]:
            report_lines.extend([
                "CRITICAL ERRORS",
                "-" * 20
            ])
            for error in summary["errors"][:10]:  # Show first 10 errors
                report_lines.append(f"• {error['check']}: {error['description']}")
            if len(summary["errors"]) > 10:
                report_lines.append(f"... and {len(summary['errors']) - 10} more errors")
            report_lines.append("")

        # Detailed results
        report_lines.extend([
            "DETAILED RESULTS",
            "-" * 20
        ])

        for check_name, check_data in results["checks"].items():
            status_icon = "✅" if check_data["status"] == "passed" else "❌"
            report_lines.append(f"{status_icon} {check_data['name']}")

            if check_data.get("issues"):
                for issue in check_data["issues"][:3]:  # Show first 3 issues per check
                    severity_icon = {"error": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(issue["severity"], "•")
                    report_lines.append(f"    {severity_icon} {issue['description']}")
                    if issue.get("file"):
                        report_lines.append(f"      File: {issue['file']}")
                if len(check_data["issues"]) > 3:
                    report_lines.append(f"    ... and {len(check_data['issues']) - 3} more issues")

            report_lines.append("")

        # Recommendations
        if summary["failed"] > 0 or summary["warnings"] > 0:
            report_lines.extend([
                "RECOMMENDATIONS",
                "-" * 20,
                "1. Fix all critical errors (🚨) first",
                "2. Address warnings (⚠️) to improve code quality",
                "3. Run tests after making changes",
                "4. Re-run validation to verify fixes",
                ""
            ])

        report_lines.extend([
            "NEXT STEPS",
            "-" * 20,
            "1. Review the detailed results above",
            "2. Fix issues starting with highest severity",
            "3. Commit fixes and update documentation",
            "4. Run validation again to confirm fixes",
            ""
        ])

        return '\n'.join(report_lines)

    def save_report(self, filename: Optional[str] = None) -> str:
        """Save validation results to JSON and text files."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_report_{timestamp}"

        # Save JSON report
        json_path = self.project_root / f"{filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)

        # Save text report
        txt_path = self.project_root / f"{filename}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())

        return str(txt_path)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate StreamlineVPN project quality and completeness")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--save-report", metavar="FILENAME", help="Save report to files")
    parser.add_argument("--json-only", action="store_true", help="Output only JSON results")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")

    args = parser.parse_args()

    validator = ProjectValidator(args.project_root)

    if not args.quiet:
        print(f"🔍 Validating StreamlineVPN project at: {validator.project_root}")

    results = validator.validate_all()

    if args.json_only:
        print(json.dumps(results, indent=2))
    else:
        report = validator.generate_report()
        print(report)

        # Summary at the end
        summary = results["summary"]
        if summary["failed"] == 0 and summary["warnings"] == 0:
            print("🎉 All validations passed! Project is in excellent condition.")
        elif summary["failed"] == 0:
            print(f"✅ All critical checks passed, but {summary['warnings']} warnings to review.")
        else:
            print(f"❌ {summary['failed']} checks failed. Please review and fix issues above.")

    if args.save_report:
        report_path = validator.save_report(args.save_report)
        if not args.quiet:
            print(f"\n📄 Report saved to: {report_path}")

    # Exit with error code if critical issues found
    sys.exit(1 if results["summary"]["failed"] > 0 else 0)


if __name__ == "__main__":
    main()
