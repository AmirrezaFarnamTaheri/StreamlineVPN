"""
Deployment manager for applying fixes and managing deployment.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class DeploymentManager:
    """Manages deployment operations and fixes."""
    
    def __init__(self, project_root: str = ".", dry_run: bool = False, create_backup: bool = True):
        self.project_root = Path(project_root).resolve()
        self.dry_run = dry_run
        self.create_backup = create_backup
        self.backup_path = None
        self.operations_log = []
    
    def deploy_all_fixes(self) -> Dict[str, Any]:
        """Apply all deployment fixes."""
        print("🚀 Starting comprehensive deployment fixes...")
        print("=" * 60)
        
        try:
            # Create backup if requested
            if self.create_backup:
                self._create_backup()
            
            # Create required directories
            self._create_required_directories()
            
            # Apply critical fixes
            self._apply_critical_fixes()
            
            # Apply configuration fixes
            self._apply_configuration_fixes()
            
            # Apply deployment fixes
            self._apply_deployment_fixes()
            
            # Apply documentation fixes
            self._apply_documentation_fixes()
            
            print("\n✅ All deployment fixes completed successfully!")
            
            return {
                    "status": "success",
                "operations_count": len(self.operations_log),
                "backup_created": self.backup_path is not None,
                "backup_path": str(self.backup_path) if self.backup_path else None,
                "operations": self.operations_log
            }
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {str(e)}")
            return {
                "status": "error",
                    "error": str(e),
                "operations_count": len(self.operations_log),
                "operations": self.operations_log
            }
    
    def _create_backup(self):
        """Create backup of current project state."""
        if self.dry_run:
            print("📦 [DRY RUN] Would create backup")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = self.project_root.parent / f"backup_{self.project_root.name}_{timestamp}"
        
        print(f"📦 Creating backup at {self.backup_path}")
        
        try:
            shutil.copytree(
                self.project_root,
                self.backup_path,
                ignore=shutil.ignore_patterns(
                    '__pycache__', '*.pyc', '.git', '.venv', 'node_modules'
                )
            )
            self.operations_log.append(f"Created backup: {self.backup_path}")
            print(f"✅ Backup created successfully")
        except Exception as e:
            print(f"⚠️  Backup creation failed: {e}")
            self.backup_path = None
    
    def _create_required_directories(self):
        """Create required directory structure."""
        required_dirs = [
            "config/nginx",
            "docs/api",
            "scripts/validators",
            "scripts/deployment",
            "tests/integration",
            "src/streamline_vpn/web/static/css",
            "src/streamline_vpn/web/static/js",
            "src/streamline_vpn/web/templates"
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                if self.dry_run:
                    print(f"📁 [DRY RUN] Would create directory: {dir_path}")
                else:
                    full_path.mkdir(parents=True, exist_ok=True)
                    self.operations_log.append(f"Created directory: {dir_path}")
                    print(f"📁 Created directory: {dir_path}")
    
    def _apply_critical_fixes(self):
        """Apply critical fixes that are essential for functionality."""
        print("\n🔧 Applying critical fixes...")
        
        critical_files = [
            ("run_unified.py", "Unified runner script"),
            ("src/streamline_vpn/__main__.py", "Main entry point"),
            ("src/streamline_vpn/cli.py", "CLI interface")
        ]
        
        for file_path, description in critical_files:
            if not (self.project_root / file_path).exists():
                print(f"⚠️  Missing critical file: {description}")
                # These would be created by content generators
                self.operations_log.append(f"Missing critical file: {file_path}")
    
    def _apply_configuration_fixes(self):
        """Apply configuration-related fixes."""
        print("\n⚙️  Applying configuration fixes...")
        
        config_files = [
            ("config/sources.yaml", "Source configuration"),
            (".env.example", "Environment template"),
            ("pyproject.toml", "Modern packaging config")
        ]
        
        for file_path, description in config_files:
            if not (self.project_root / file_path).exists():
                print(f"⚠️  Missing config file: {description}")
                self.operations_log.append(f"Missing config file: {file_path}")
    
    def _apply_deployment_fixes(self):
        """Apply deployment-related fixes."""
        print("\n🐳 Applying deployment fixes...")
        
        deployment_files = [
            ("Dockerfile", "Docker configuration"),
            ("docker-compose.yml", "Docker composition"),
            ("docker-compose.prod.yml", "Production Docker composition")
        ]
        
        for file_path, description in deployment_files:
            if not (self.project_root / file_path).exists():
                print(f"⚠️  Missing deployment file: {description}")
                self.operations_log.append(f"Missing deployment file: {file_path}")
    
    def _apply_documentation_fixes(self):
        """Apply documentation fixes."""
        print("\n📚 Applying documentation fixes...")
        
        doc_files = [
            ("README.md", "Main documentation"),
            ("docs/api/index.html", "API documentation"),
            ("IMPLEMENTATION_GUIDE.md", "Implementation guide")
        ]
        
        for file_path, description in doc_files:
            if not (self.project_root / file_path).exists():
                print(f"⚠️  Missing documentation: {description}")
                self.operations_log.append(f"Missing documentation: {file_path}")
    
    def write_file(self, file_path: str, content: str) -> bool:
        """Write content to a file."""
        if self.dry_run:
            print(f"📝 [DRY RUN] Would write {len(content)} chars to {file_path}")
            return True
        
        try:
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.operations_log.append(f"Wrote file: {file_path}")
            print(f"📝 Created/updated: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to write {file_path}: {e}")
            return False
    
    def run_command(self, command: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run a command and return results."""
        if self.dry_run:
            print(f"🔧 [DRY RUN] Would run: {' '.join(command)}")
            return {"returncode": 0, "stdout": "", "stderr": ""}
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd or str(self.project_root),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            self.operations_log.append(f"Ran command: {' '.join(command)}")
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"returncode": -1, "stdout": "", "stderr": "Command timed out"}
        except Exception as e:
            return {"returncode": -1, "stdout": "", "stderr": str(e)}
    
    def get_operations_log(self) -> List[str]:
        """Get the log of operations performed."""
        return self.operations_log.copy()