"""
Validation runner for deployment validation.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple


class ValidationRunner:
    """Runs validation checks after deployment."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
    
    def run_final_validation(self) -> Dict[str, Any]:
        """Run final validation after deployment."""
        print("\n🔍 Running final validation...")
        
        validation_results = {
            "python_syntax": self._check_python_syntax(),
            "imports": self._check_imports(),
            "configurations": self._check_configurations(),
            "file_completeness": self._check_file_completeness(),
            "overall_status": "unknown"
        }
        
        # Determine overall status
        if all(validation_results[key] for key in ["python_syntax", "imports", "configurations", "file_completeness"]):
            validation_results["overall_status"] = "success"
            print("✅ All validation checks passed!")
        else:
            validation_results["overall_status"] = "failed"
            print("❌ Some validation checks failed!")
        
        return validation_results
    
    def _check_python_syntax(self) -> bool:
        """Check Python syntax for all Python files."""
        print("🐍 Checking Python syntax...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print("⚠️  py_compile not available, skipping syntax check")
                return True
            
            # Check all Python files
            python_files = list(self.project_root.rglob("*.py"))
            syntax_errors = []
            
            for py_file in python_files:
                if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                    continue
                
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", str(py_file)],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode != 0:
                        syntax_errors.append(str(py_file.relative_to(self.project_root)))
                
                except subprocess.TimeoutExpired:
                    syntax_errors.append(f"{py_file} (timeout)")
            
            if syntax_errors:
                print(f"❌ Found syntax errors in {len(syntax_errors)} files:")
                for error_file in syntax_errors[:5]:  # Show first 5
                    print(f"  - {error_file}")
                if len(syntax_errors) > 5:
                    print(f"  ... and {len(syntax_errors) - 5} more")
                return False
            else:
                print("✅ All Python files have valid syntax")
                return True
                
        except Exception as e:
            print(f"⚠️  Syntax check failed: {e}")
            return False
    
    def _check_imports(self) -> bool:
        """Check that critical imports work."""
        print("📦 Checking critical imports...")
        
        critical_imports = [
            "streamline_vpn",
            "streamline_vpn.core",
            "streamline_vpn.api",
            "streamline_vpn.web",
            "streamline_vpn.cli"
        ]
        
        import_errors = []
        
        for module_name in critical_imports:
            try:
                result = subprocess.run(
                    [sys.executable, "-c", f"import {module_name}"],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    import_errors.append(module_name)
                    print(f"❌ Failed to import {module_name}: {result.stderr.strip()}")
                else:
                    print(f"✅ Successfully imported {module_name}")
            
            except subprocess.TimeoutExpired:
                import_errors.append(f"{module_name} (timeout)")
            except Exception as e:
                import_errors.append(f"{module_name} ({e})")
        
        if import_errors:
            print(f"❌ Import errors in {len(import_errors)} modules")
            return False
        else:
            print("✅ All critical imports successful")
            return True
    
    def _check_configurations(self) -> bool:
        """Check configuration files."""
        print("⚙️  Checking configuration files...")
        
        config_files = [
            "config/sources.yaml",
            ".env.example",
            "pyproject.toml",
            "requirements.txt"
        ]
        
        config_errors = []
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if not config_path.exists():
                config_errors.append(f"Missing: {config_file}")
                print(f"❌ Missing configuration file: {config_file}")
            else:
                print(f"✅ Found configuration file: {config_file}")
        
        if config_errors:
            print(f"❌ Configuration errors: {len(config_errors)}")
            return False
        else:
            print("✅ All configuration files present")
            return True
    
    def _check_file_completeness(self) -> bool:
        """Check that essential files are complete."""
        print("📄 Checking file completeness...")
        
        essential_files = [
            "run_unified.py",
            "run_api.py", 
            "run_web.py",
            "src/streamline_vpn/__main__.py",
            "src/streamline_vpn/cli.py"
        ]
        
        incomplete_files = []
        
        for file_path in essential_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                incomplete_files.append(f"Missing: {file_path}")
                print(f"❌ Missing essential file: {file_path}")
            else:
                # Check if file has content
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                if len(content.strip()) < 50:  # Minimum content check
                    incomplete_files.append(f"Too short: {file_path}")
                    print(f"⚠️  File may be incomplete: {file_path}")
                else:
                    print(f"✅ File complete: {file_path}")
        
        if incomplete_files:
            print(f"❌ File completeness issues: {len(incomplete_files)}")
            return False
        else:
            print("✅ All essential files are complete")
            return True
    
    def run_tests(self) -> Dict[str, Any]:
        """Run the test suite."""
        print("\n🧪 Running test suite...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Test suite timed out",
                "success": False
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }
    
    def run_coverage_check(self) -> Dict[str, Any]:
        """Run coverage check."""
        print("\n📊 Running coverage check...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "--cov=src/streamline_vpn", "--cov-report=term-missing"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Coverage check timed out",
                "success": False
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False
            }

