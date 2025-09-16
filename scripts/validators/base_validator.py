"""
Base validator class with common functionality.
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


class BaseValidator:
    """Base class for all validators with common functionality."""
    
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
    
    def _add_check_result(self, check_name: str, status: str, message: str, 
                         details: Optional[Dict] = None, critical: bool = False):
        """Add a check result to the validation results."""
        self.validation_results["checks"][check_name] = {
            "status": status,
            "message": message,
            "details": details or {},
            "critical": critical,
            "timestamp": datetime.now().isoformat()
        }
        
        self.validation_results["summary"]["total_checks"] += 1
        
        if status == "PASS":
            self.validation_results["summary"]["passed"] += 1
        elif status == "FAIL":
            self.validation_results["summary"]["failed"] += 1
            if critical:
                self.validation_results["summary"]["critical_errors"] += 1
        elif status == "WARN":
            self.validation_results["summary"]["warnings"] += 1
    
    def _add_recommendation(self, recommendation: str):
        """Add a recommendation to the summary."""
        self.validation_results["summary"]["recommendations"].append(recommendation)
    
    def _check_file_exists(self, file_path: str, description: str) -> bool:
        """Check if a file exists and add result."""
        full_path = self.project_root / file_path
        exists = full_path.exists()
        
        if exists:
            self._add_check_result(
                f"file_exists_{file_path.replace('/', '_')}",
                "PASS",
                f"{description} exists"
            )
        else:
            self._add_check_result(
                f"file_exists_{file_path.replace('/', '_')}",
                "FAIL",
                f"{description} missing",
                critical=True
            )
        
        return exists
    
    def _check_directory_exists(self, dir_path: str, description: str) -> bool:
        """Check if a directory exists and add result."""
        full_path = self.project_root / dir_path
        exists = full_path.is_dir()
        
        if exists:
            self._add_check_result(
                f"dir_exists_{dir_path.replace('/', '_')}",
                "PASS",
                f"{description} directory exists"
            )
        else:
            self._add_check_result(
                f"dir_exists_{dir_path.replace('/', '_')}",
                "FAIL",
                f"{description} directory missing",
                critical=True
            )
        
        return exists
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """Read file content safely."""
        try:
            full_path = self.project_root / file_path
            return full_path.read_text(encoding='utf-8')
        except Exception:
            return None
    
    def _check_python_syntax(self, file_path: str) -> bool:
        """Check if a Python file has valid syntax."""
        content = self._read_file_content(file_path)
        if not content:
            return False
        
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False
    
    def _run_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or str(self.project_root),
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    def get_results(self) -> Dict[str, Any]:
        """Get validation results."""
        return self.validation_results

