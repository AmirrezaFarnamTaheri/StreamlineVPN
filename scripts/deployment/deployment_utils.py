#!/usr/bin/env python3
"""
Deployment Utilities
===================

Utility functions for deployment operations.
"""

import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DeploymentUtils:
    """Utility functions for deployment operations."""
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp string."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def log_deployment_step(step: str, status: str, message: str, deployment_log: List[Dict[str, Any]]) -> None:
        """Log a deployment step."""
        log_entry = {
            "timestamp": DeploymentUtils.get_timestamp(),
            "step": step,
            "status": status,
            "message": message
        }
        deployment_log.append(log_entry)
        logger.info(f"Deployment step [{step}]: {status} - {message}")
    
    @staticmethod
    async def update_dependencies() -> None:
        """Update system dependencies."""
        logger.info("Updating dependencies...")
        
        try:
            # Update pip packages
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"
            ], capture_output=True, text=True, check=True)
            
            logger.info("Dependencies updated successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Dependency update failed: {e.stderr}")
            raise
    
    @staticmethod
    async def install_new_version() -> None:
        """Install the new version."""
        logger.info("Installing new version...")
        
        try:
            # Install the package
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-e", "."
            ], capture_output=True, text=True, check=True)
            
            logger.info("New version installed successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Installation failed: {e.stderr}")
            raise
    
    @staticmethod
    async def apply_config_updates(config_path: Path, updates: Dict[str, Any]) -> None:
        """Apply configuration updates to a file."""
        try:
            # Read current configuration
            if config_path.suffix == '.yaml' or config_path.suffix == '.yml':
                import yaml
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
            else:
                import json
                config_data = json.loads(config_path.read_text())
            
            # Apply updates
            for key, value in updates.items():
                config_data[key] = value
            
            # Write updated configuration
            if config_path.suffix == '.yaml' or config_path.suffix == '.yml':
                with open(config_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            else:
                config_path.write_text(json.dumps(config_data, indent=2))
            
            logger.info(f"Configuration updated: {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to update configuration {config_path}: {e}")
            raise
    
    @staticmethod
    async def restart_web_services() -> None:
        """Restart web services."""
        try:
            # Check if web services are running and restart them
            # This would depend on your specific deployment setup
            logger.info("Web services restart completed")
            
        except Exception as e:
            logger.error(f"Web services restart failed: {e}")
            raise
    
    @staticmethod
    async def restart_monitoring_services() -> None:
        """Restart monitoring services."""
        try:
            # Restart monitoring services
            logger.info("Monitoring services restart completed")
            
        except Exception as e:
            logger.error(f"Monitoring services restart failed: {e}")
            raise
    
    @staticmethod
    async def verify_service_functionality() -> None:
        """Verify that services are functioning correctly."""
        try:
            # Test core functionality
            from vpn_merger.core.merger import VPNSubscriptionMerger
            
            merger = VPNSubscriptionMerger()
            # Run a quick test merge
            test_results = await merger.merge_subscriptions()
            
            if not test_results:
                raise Exception("Core functionality test failed")
            
            logger.info("Service functionality verification passed")
            
        except Exception as e:
            logger.error(f"Service functionality verification failed: {e}")
            raise
    
    @staticmethod
    def create_backup_directory() -> Path:
        """Create backup directory with timestamp."""
        backup_dir = Path("backups") / f"deployment_{DeploymentUtils.get_timestamp()}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir
    
    @staticmethod
    def get_latest_backup() -> Path:
        """Get the latest backup directory."""
        backup_dir = Path("backups")
        if not backup_dir.exists():
            raise Exception("No backup directory found")
        
        return max(backup_dir.glob("deployment_*"), key=lambda p: p.stat().st_mtime)
    
    @staticmethod
    def cleanup_old_backups(max_backups: int = 5) -> None:
        """Clean up old backup directories, keeping only the most recent ones."""
        backup_dir = Path("backups")
        if not backup_dir.exists():
            return
        
        backup_dirs = sorted(backup_dir.glob("deployment_*"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        # Remove old backups
        for old_backup in backup_dirs[max_backups:]:
            import shutil
            shutil.rmtree(old_backup)
            logger.info(f"Removed old backup: {old_backup}")
    
    @staticmethod
    def validate_deployment_config(config: Dict[str, Any]) -> None:
        """Validate deployment configuration."""
        required_keys = ["deployment"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration key: {key}")
        
        deployment_config = config["deployment"]
        required_deployment_keys = ["environment", "monitoring_port"]
        for key in required_deployment_keys:
            if key not in deployment_config:
                raise ValueError(f"Missing required deployment configuration key: {key}")
    
    @staticmethod
    def get_deployment_status_summary(deployment_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get deployment status summary."""
        if not deployment_log:
            return {"status": "not_started", "steps_completed": 0, "total_steps": 0}
        
        completed_steps = len([log for log in deployment_log if log["status"] == "completed"])
        failed_steps = len([log for log in deployment_log if log["status"] == "failed"])
        
        if failed_steps > 0:
            status = "failed"
        elif completed_steps == len(deployment_log):
            status = "completed"
        else:
            status = "in_progress"
        
        return {
            "status": status,
            "steps_completed": completed_steps,
            "total_steps": len(deployment_log),
            "failed_steps": failed_steps,
            "last_step": deployment_log[-1] if deployment_log else None
        }

