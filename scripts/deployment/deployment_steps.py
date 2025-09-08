#!/usr/bin/env python3
"""
Deployment Steps
===============

Individual deployment step implementations.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from streamline_vpn.monitoring.health_monitor import get_health_monitor
from streamline_vpn.core.observers import get_event_bus

from .deployment_utils import DeploymentUtils

logger = logging.getLogger(__name__)


class PreDeploymentChecks:
    """Handles pre-deployment health checks."""
    
    def __init__(self, health_monitor=None):
        """Initialize pre-deployment checks.
        
        Args:
            health_monitor: Health monitor instance
        """
        self.health_monitor = health_monitor or get_health_monitor()
    
    async def run_checks(self, deployment_log: List[Dict[str, Any]]) -> None:
        """Perform pre-deployment health checks."""
        logger.info("Running pre-deployment checks...")
        
        try:
            # Check system health
            health_status = await self.health_monitor.check_health()
            if health_status["overall_status"] != "healthy":
                raise Exception(f"System health check failed: {health_status}")
            
            # Check disk space
            disk_check = health_status["checks"].get("disk_space", {})
            if disk_check.get("status") == "unhealthy":
                raise Exception("Insufficient disk space for deployment")
            
            # Check network connectivity
            network_check = health_status["checks"].get("network_connectivity", {})
            if network_check.get("status") == "unhealthy":
                raise Exception("Network connectivity issues detected")
            
            # Check service availability
            service_check = health_status["checks"].get("service_availability", {})
            if service_check.get("status") == "unhealthy":
                raise Exception("Service availability issues detected")
            
            DeploymentUtils.log_deployment_step(
                "pre_deployment_checks", "completed", "All pre-deployment checks passed", deployment_log
            )
            logger.info("Pre-deployment checks completed successfully")
            
        except Exception as e:
            DeploymentUtils.log_deployment_step(
                "pre_deployment_checks", "failed", str(e), deployment_log
            )
            raise


class BackupManager:
    """Handles backup creation and management."""
    
    async def create_backup(self, deployment_log: List[Dict[str, Any]]) -> Path:
        """Create backup of current deployment."""
        logger.info("Creating backup of current deployment...")
        
        try:
            backup_dir = DeploymentUtils.create_backup_directory()
            
            # Backup configuration files
            config_files = [
                "config/sources.unified.yaml",
                "config/sources.enhanced.yaml",
                "config/performance.yaml"
            ]
            
            for config_file in config_files:
                config_path = Path(config_file)
                if config_path.exists():
                    backup_path = backup_dir / config_path.name
                    backup_path.write_text(config_path.read_text())
            
            # Backup output files
            output_dir = Path("output")
            if output_dir.exists():
                backup_output_dir = backup_dir / "output"
                backup_output_dir.mkdir(exist_ok=True)
                
                for output_file in output_dir.glob("*"):
                    if output_file.is_file():
                        backup_output_file = backup_output_dir / output_file.name
                        backup_output_file.write_text(output_file.read_text())
            
            DeploymentUtils.log_deployment_step(
                "backup", "completed", f"Backup created at {backup_dir}", deployment_log
            )
            logger.info(f"Backup created successfully at {backup_dir}")
            
            return backup_dir
            
        except Exception as e:
            DeploymentUtils.log_deployment_step(
                "backup", "failed", str(e), deployment_log
            )
            logger.error(f"Backup creation failed: {e}")
            raise
    
    async def restore_backup(self, backup_dir: Path, deployment_log: List[Dict[str, Any]]) -> None:
        """Restore from backup."""
        logger.info(f"Restoring from backup: {backup_dir}")
        
        try:
            # Restore configuration files
            for config_file in backup_dir.glob("*.yaml"):
                target_path = Path("config") / config_file.name
                target_path.write_text(config_file.read_text())
            
            # Restore output files
            backup_output_dir = backup_dir / "output"
            if backup_output_dir.exists():
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                
                for output_file in backup_output_dir.glob("*"):
                    if output_file.is_file():
                        target_output_file = output_dir / output_file.name
                        target_output_file.write_text(output_file.read_text())
            
            DeploymentUtils.log_deployment_step(
                "restore_backup", "completed", f"Restored from {backup_dir}", deployment_log
            )
            logger.info(f"Backup restored successfully from {backup_dir}")
            
        except Exception as e:
            DeploymentUtils.log_deployment_step(
                "restore_backup", "failed", str(e), deployment_log
            )
            logger.error(f"Backup restore failed: {e}")
            raise


class VersionDeployer:
    """Handles new version deployment."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize version deployer.
        
        Args:
            config: Deployment configuration
        """
        self.config = config or {}
    
    async def deploy_new_version(self, deployment_log: List[Dict[str, Any]]) -> None:
        """Deploy the new version."""
        logger.info("Deploying new version...")
        
        try:
            # Update dependencies
            await DeploymentUtils.update_dependencies()
            
            # Install new version
            await DeploymentUtils.install_new_version()
            
            # Update configuration
            await self._update_configuration(deployment_log)
            
            # Restart services
            await self._restart_services(deployment_log)
            
            DeploymentUtils.log_deployment_step(
                "deploy", "completed", "New version deployed successfully", deployment_log
            )
            logger.info("New version deployed successfully")
            
        except Exception as e:
            DeploymentUtils.log_deployment_step(
                "deploy", "failed", str(e), deployment_log
            )
            logger.error(f"Deployment failed: {e}")
            raise
    
    async def _update_configuration(self, deployment_log: List[Dict[str, Any]]) -> None:
        """Update configuration files."""
        logger.info("Updating configuration...")
        
        try:
            # Update configuration files if needed
            config_updates = self.config.get("config_updates", {})
            
            for config_file, updates in config_updates.items():
                config_path = Path(config_file)
                if config_path.exists():
                    # Apply configuration updates
                    await DeploymentUtils.apply_config_updates(config_path, updates)
            
            DeploymentUtils.log_deployment_step(
                "configuration", "completed", "Configuration updated successfully", deployment_log
            )
            logger.info("Configuration updated successfully")
            
        except Exception as e:
            DeploymentUtils.log_deployment_step(
                "configuration", "failed", str(e), deployment_log
            )
            logger.error(f"Configuration update failed: {e}")
            raise
    
    async def _restart_services(self, deployment_log: List[Dict[str, Any]]) -> None:
        """Restart system services."""
        logger.info("Restarting services...")
        
        try:
            # Restart web services if running
            await DeploymentUtils.restart_web_services()
            
            # Restart monitoring services
            await DeploymentUtils.restart_monitoring_services()
            
            DeploymentUtils.log_deployment_step(
                "restart", "completed", "Services restarted successfully", deployment_log
            )
            logger.info("Services restarted successfully")
            
        except Exception as e:
            DeploymentUtils.log_deployment_step(
                "restart", "failed", str(e), deployment_log
            )
            logger.error(f"Service restart failed: {e}")
            raise


class PostDeploymentVerification:
    """Handles post-deployment verification."""
    
    def __init__(self, health_monitor=None):
        """Initialize post-deployment verification.
        
        Args:
            health_monitor: Health monitor instance
        """
        self.health_monitor = health_monitor or get_health_monitor()
    
    async def verify_deployment(self, deployment_log: List[Dict[str, Any]]) -> None:
        """Perform post-deployment verification."""
        logger.info("Running post-deployment verification...")
        
        try:
            # Wait for services to stabilize
            await asyncio.sleep(10)
            
            # Run health checks
            health_status = await self.health_monitor.check_health()
            if health_status["overall_status"] != "healthy":
                raise Exception(f"Post-deployment health check failed: {health_status}")
            
            # Verify service functionality
            await DeploymentUtils.verify_service_functionality()
            
            DeploymentUtils.log_deployment_step(
                "verification", "completed", "Post-deployment verification passed", deployment_log
            )
            logger.info("Post-deployment verification completed successfully")
            
        except Exception as e:
            DeploymentUtils.log_deployment_step(
                "verification", "failed", str(e), deployment_log
            )
            logger.error(f"Post-deployment verification failed: {e}")
            raise


class MonitoringStarter:
    """Handles monitoring service startup."""
    
    def __init__(self, deployment_config: Optional[Dict[str, Any]] = None):
        """Initialize monitoring starter.
        
        Args:
            deployment_config: Deployment configuration
        """
        self.deployment_config = deployment_config or {}
        self.monitoring_dashboard = None
    
    async def start_monitoring(self, deployment_log: List[Dict[str, Any]]) -> None:
        """Start monitoring services."""
        logger.info("Starting monitoring services...")
        
        try:
            # Start monitoring dashboard (placeholder)
            # MonitoringDashboard would be implemented here
            self.monitoring_dashboard = None
            
            # Start continuous health monitoring
            from streamline_vpn.monitoring.health_monitor import get_health_monitor
            health_monitor = get_health_monitor()
            
            asyncio.create_task(
                health_monitor.start_continuous_monitoring(
                    interval_seconds=self.deployment_config.get("health_check_interval", 30)
                )
            )
            
            DeploymentUtils.log_deployment_step(
                "monitoring", "completed", "Monitoring services started", deployment_log
            )
            logger.info("Monitoring services started successfully")
            
        except Exception as e:
            DeploymentUtils.log_deployment_step(
                "monitoring", "failed", str(e), deployment_log
            )
            logger.error(f"Failed to start monitoring services: {e}")
            raise
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring services."""
        if self.monitoring_dashboard:
            await self.monitoring_dashboard.stop()
            logger.info("Monitoring services stopped")


class RollbackManager:
    """Handles deployment rollback operations."""
    
    def __init__(self, backup_manager: BackupManager):
        """Initialize rollback manager.
        
        Args:
            backup_manager: Backup manager instance
        """
        self.backup_manager = backup_manager
    
    async def rollback_deployment(self, deployment_log: List[Dict[str, Any]]) -> None:
        """Rollback to previous deployment."""
        logger.info("Rolling back deployment...")
        
        try:
            # Find latest backup
            latest_backup = DeploymentUtils.get_latest_backup()
            
            # Restore from backup
            await self.backup_manager.restore_backup(latest_backup, deployment_log)
            
            # Restart services
            await DeploymentUtils.restart_web_services()
            await DeploymentUtils.restart_monitoring_services()
            
            DeploymentUtils.log_deployment_step(
                "rollback", "completed", f"Rolled back to {latest_backup}", deployment_log
            )
            logger.info(f"Deployment rolled back to {latest_backup}")
            
        except Exception as e:
            DeploymentUtils.log_deployment_step(
                "rollback", "failed", str(e), deployment_log
            )
            logger.error(f"Rollback failed: {e}")
            raise

