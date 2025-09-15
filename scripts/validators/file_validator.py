"""
File validation and syntax checking.
"""

from pathlib import Path
from typing import Dict, Any, List
from .base_validator import BaseValidator


class FileValidator(BaseValidator):
    """Validates file syntax and content."""
    
    def validate_runner_scripts(self):
        """Validate runner scripts functionality."""
        print("🏃 Validating runner scripts...")
        
        runner_scripts = [
            ("run_unified.py", "Unified runner"),
            ("run_api.py", "API runner"),
            ("run_web.py", "Web runner")
        ]
        
        for script, description in runner_scripts:
            if self._check_file_exists(script, description):
                # Check Python syntax
                if self._check_python_syntax(script):
                    self._add_check_result(
                        f"syntax_{script}",
                        "PASS",
                        f"{description} has valid Python syntax"
                    )
                else:
                    self._add_check_result(
                        f"syntax_{script}",
                        "FAIL",
                        f"{description} has syntax errors",
                        critical=True
                    )
                
                # Check for main function
                self._check_main_function(script, description)
    
    def validate_python_files(self):
        """Validate all Python files for syntax."""
        print("🐍 Validating Python file syntax...")
        
        python_files = list(self.project_root.rglob("*.py"))
        syntax_errors = []
        
        for py_file in python_files:
            # Skip __pycache__ and .venv
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue
            
            relative_path = py_file.relative_to(self.project_root)
            
            if not self._check_python_syntax(str(relative_path)):
                syntax_errors.append(str(relative_path))
        
        if syntax_errors:
            self._add_check_result(
                "python_syntax_validation",
                "FAIL",
                f"Found syntax errors in {len(syntax_errors)} Python files",
                {"files_with_errors": syntax_errors},
                critical=True
            )
        else:
            self._add_check_result(
                "python_syntax_validation",
                "PASS",
                "All Python files have valid syntax"
            )
    
    def _check_main_function(self, file_path: str, description: str):
        """Check if a file has a main function or if __name__ == '__main__'."""
        content = self._read_file_content(file_path)
        if not content:
            return
        
        has_main = (
            "if __name__ == '__main__':" in content or
            "def main(" in content or
            "async def main(" in content
        )
        
        if has_main:
            self._add_check_result(
                f"main_function_{file_path.replace('/', '_')}",
                "PASS",
                f"{description} has main entry point"
            )
        else:
            self._add_check_result(
                f"main_function_{file_path.replace('/', '_')}",
                "WARN",
                f"{description} may be missing main entry point"
            )
    
    def validate_imports(self):
        """Validate that all imports can be resolved."""
        print("📦 Validating import resolution...")
        
        python_files = list(self.project_root.rglob("*.py"))
        import_errors = []
        
        for py_file in python_files:
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue
            
            relative_path = py_file.relative_to(self.project_root)
            content = self._read_file_content(str(relative_path))
            
            if content:
                imports = self._extract_imports(content)
                for import_stmt in imports:
                    if not self._can_resolve_import(import_stmt, py_file):
                        import_errors.append(f"{relative_path}: {import_stmt}")
        
        if import_errors:
            self._add_check_result(
                "import_resolution",
                "WARN",
                f"Found {len(import_errors)} potentially unresolved imports",
                {"import_errors": import_errors[:10]}  # Limit to first 10
            )
        else:
            self._add_check_result(
                "import_resolution",
                "PASS",
                "All imports appear to be resolvable"
            )
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from Python content."""
        imports = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        
        return imports
    
    def _can_resolve_import(self, import_stmt: str, file_path: Path) -> bool:
        """Check if an import can be resolved."""
        # This is a simplified check - in practice, you'd need more sophisticated logic
        if import_stmt.startswith('from .') or import_stmt.startswith('from ..'):
            return True  # Relative imports are usually fine
        
        if import_stmt.startswith('import ') and not import_stmt.startswith('import .'):
            # Check if it's a standard library or third-party import
            module_name = import_stmt.split()[1].split('.')[0]
            try:
                __import__(module_name)
                return True
            except ImportError:
                return False
        
        return True  # Assume other imports are fine
