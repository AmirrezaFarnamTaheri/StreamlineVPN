"""
Integration validation for backend/frontend and API consistency.
"""

from pathlib import Path
from typing import Dict, Any
from .base_validator import BaseValidator


class IntegrationValidator(BaseValidator):
    """Validates integration between components."""
    
    def validate_backend_integration(self):
        """Validate backend component integration."""
        print("🔧 Validating backend integration...")
        
        # Check core modules integration
        core_files = [
            "src/streamline_vpn/core/merger.py",
            "src/streamline_vpn/core/config_processor.py",
            "src/streamline_vpn/core/source_manager.py"
        ]
        
        for core_file in core_files:
            if self._check_file_exists(core_file, f"Core module: {core_file}"):
                self._validate_module_imports(core_file)
        
        # Check API integration
        api_files = [
            "src/streamline_vpn/api/api.py",
            "src/streamline_vpn/api/unified_api.py",
            "src/streamline_vpn/api/schema.py"
        ]
        
        for api_file in api_files:
            if self._check_file_exists(api_file, f"API module: {api_file}"):
                self._validate_api_endpoints(api_file)
    
    def validate_frontend_integration(self):
        """Validate frontend integration."""
        print("🌐 Validating frontend integration...")
        
        # Check web interface files
        web_files = [
            "src/streamline_vpn/web/static_server.py",
            "src/streamline_vpn/web/templates",
            "src/streamline_vpn/web/static"
        ]
        
        for web_file in web_files:
            if web_file.endswith('/'):
                self._check_directory_exists(web_file, f"Web directory: {web_file}")
            else:
                self._check_file_exists(web_file, f"Web file: {web_file}")
        
        # Check for HTML templates
        template_files = list((self.project_root / "src/streamline_vpn/web").rglob("*.html"))
        if template_files:
            self._add_check_result(
                "html_templates",
                "PASS",
                f"Found {len(template_files)} HTML template files"
            )
        else:
            self._add_check_result(
                "html_templates",
                "WARN",
                "No HTML template files found"
            )
    
    def validate_api_consistency(self):
        """Validate API consistency and documentation."""
        print("🔗 Validating API consistency...")
        
        # Check API documentation
        api_docs = [
            "docs/api/index.html",
            "docs/api/endpoints.md"
        ]
        
        for doc_file in api_docs:
            self._check_file_exists(doc_file, f"API documentation: {doc_file}")
        
        # Check for OpenAPI schema
        schema_files = [
            "src/streamline_vpn/api/schema.py",
            "docs/api/openapi.json"
        ]
        
        for schema_file in schema_files:
            if self._check_file_exists(schema_file, f"API schema: {schema_file}"):
                self._validate_api_schema(schema_file)
    
    def _validate_module_imports(self, module_path: str):
        """Validate that a module can be imported."""
        content = self._read_file_content(module_path)
        if not content:
            return
        
        # Check for basic class/function definitions
        has_classes = "class " in content
        has_functions = "def " in content
        
        if has_classes or has_functions:
            self._add_check_result(
                f"module_structure_{module_path.replace('/', '_')}",
                "PASS",
                f"Module {module_path} has proper structure"
            )
        else:
            self._add_check_result(
                f"module_structure_{module_path.replace('/', '_')}",
                "WARN",
                f"Module {module_path} may be empty or incomplete"
            )
    
    def _validate_api_endpoints(self, api_file: str):
        """Validate API endpoint definitions."""
        content = self._read_file_content(api_file)
        if not content:
            return
        
        # Check for FastAPI patterns
        has_routes = "@app." in content or "@router." in content
        has_models = "class " in content and ("BaseModel" in content or "pydantic" in content)
        
        if has_routes:
            self._add_check_result(
                f"api_routes_{api_file.replace('/', '_')}",
                "PASS",
                f"API file {api_file} has route definitions"
            )
        else:
            self._add_check_result(
                f"api_routes_{api_file.replace('/', '_')}",
                "WARN",
                f"API file {api_file} may be missing route definitions"
            )
        
        if has_models:
            self._add_check_result(
                f"api_models_{api_file.replace('/', '_')}",
                "PASS",
                f"API file {api_file} has data models"
            )
    
    def _validate_api_schema(self, schema_file: str):
        """Validate API schema file."""
        content = self._read_file_content(schema_file)
        if not content:
            return
        
        # Check for schema patterns
        has_schema = (
            "BaseModel" in content or
            "openapi" in content.lower() or
            "schema" in content.lower()
        )
        
        if has_schema:
            self._add_check_result(
                f"api_schema_{schema_file.replace('/', '_')}",
                "PASS",
                f"Schema file {schema_file} contains schema definitions"
            )
        else:
            self._add_check_result(
                f"api_schema_{schema_file.replace('/', '_')}",
                "WARN",
                f"Schema file {schema_file} may be incomplete"
            )
