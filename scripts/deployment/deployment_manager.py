#!/usr/bin/env python3
"""
Deployment Manager
=================

Main deployment manager that orchestrates all deployment steps.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from vpn_merger.core.observers import get_event_bus
from vpn_merger.monitoring.health_monitor import get_health_monitor

from .deployment_steps import (
    PreDeploymentChecks,
    BackupManager,
    VersionDeployer,
    PostDeploymentVerification,
    MonitoringStarter,
    RollbackManager
)
from .deployment_utils import DeploymentUtils

logger = logging.getLogger(__name__)


class DeploymentManager:
    """Main deployment manager that orchestrates all deployment steps."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the deployment manager.
        
        Args:
            config: Deployment configuration
        """
        self.config = config or {}
        self.health_monitor = get_health_monitor()
        self.event_bus = get_event_bus()
        self.deployment_status = "not_started"
        self.deployment_log: List[Dict[str, Any]] = []
        
        # Deployment configuration
        self.deployment_config = self.config.get("deployment", {
            "environment": "production",
            "monitoring_port": 8082,
            "health_check_interval": 30,
            "max_retries": 3,
            "rollback_on_failure": True,
            "backup_before_deploy": True
        })
        
        # Initialize deployment steps
        self.pre_deployment_checks = PreDeploymentChecks(self.health_monitor)
        self.backup_manager = BackupManager()
        self.version_deployer = VersionDeployer(self.config)
        self.post_deployment_verification = PostDeploymentVerification(self.health_monitor)
        self.monitoring_starter = MonitoringStarter(self.deployment_config)
        self.rollback_manager = RollbackManager(self.backup_manager)
        
        logger.info("Deployment manager initialized")
    
    async def deploy(self) -> bool:
        """Execute the complete deployment process."""
        logger.info("Starting production deployment...")
        self.deployment_status = "in_progress"
        
        try:
            # Validate configuration
            DeploymentUtils.validate_deployment_config(self.config)
            
            # 1. Pre-deployment checks
            await self.pre_deployment_checks.run_checks(self.deployment_log)
            
            # 2. Backup current deployment
            backup_dir = None
            if self.deployment_config["backup_before_deploy"]:
                backup_dir = await self.backup_manager.create_backup(self.deployment_log)
            
            # 3. Deploy new version
            await self.version_deployer.deploy_new_version(self.deployment_log)
            
            # 4. Post-deployment verification
            await self.post_deployment_verification.verify_deployment(self.deployment_log)
            
            # 5. Start monitoring
            await self.monitoring_starter.start_monitoring(self.deployment_log)
            
            self.deployment_status = "completed"
            logger.info("Production deployment completed successfully")
            
            # Clean up old backups
            DeploymentUtils.cleanup_old_backups()
            
            # Publish deployment success event
            await self.event_bus.publish(
                "deployment_completed",
                {
                    "status": "success",
                    "deployment_log": self.deployment_log,
                    "backup_dir": str(backup_dir) if backup_dir else None
                },
                source="deployment_manager"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            self.deployment_status = "failed"
            
            # Publish deployment failure event
            await self.event_bus.publish(
                "deployment_failed",
                {
                    "status": "failed",
                    "error": str(e),
                    "deployment_log": self.deployment_log
                },
                source="deployment_manager"
            )
            
            # Rollback on failure
            if self.deployment_config["rollback_on_failure"]:
                try:
                    await self.rollback_manager.rollback_deployment(self.deployment_log)
                    logger.info("Deployment rolled back successfully")
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")
            
            return False
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        status_summary = DeploymentUtils.get_deployment_status_summary(self.deployment_log)
        
        return {
            "status": self.deployment_status,
            "log": self.deployment_log,
            "config": self.deployment_config,
            "summary": status_summary
        }
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring services."""
        await self.monitoring_starter.stop_monitoring()
    
    def get_deployment_log(self) -> List[Dict[str, Any]]:
        """Get deployment log."""
        return self.deployment_log.copy()
    
    def clear_deployment_log(self) -> None:
        """Clear deployment log."""
        self.deployment_log.clear()
        self.deployment_status = "not_started"
    
    async def dry_run_deployment(self) -> Dict[str, Any]:
        """Perform a dry run of the deployment process."""
        logger.info("Starting deployment dry run...")
        
        dry_run_log = []
        
        try:
            # Validate configuration
            DeploymentUtils.validate_deployment_config(self.config)
            DeploymentUtils.log_deployment_step(
                "config_validation", "completed", "Configuration validation passed", dry_run_log
            )
            
            # Simulate pre-deployment checks
            DeploymentUtils.log_deployment_step(
                "pre_deployment_checks", "simulated", "Pre-deployment checks would be performed", dry_run_log
            )
            
            # Simulate backup creation
            if self.deployment_config["backup_before_deploy"]:
                DeploymentUtils.log_deployment_step(
                    "backup", "simulated", "Backup creation would be performed", dry_run_log
                )
            
            # Simulate deployment
            DeploymentUtils.log_deployment_step(
                "deploy", "simulated", "New version deployment would be performed", dry_run_log
            )
            
            # Simulate verification
            DeploymentUtils.log_deployment_step(
                "verification", "simulated", "Post-deployment verification would be performed", dry_run_log
            )
            
            # Simulate monitoring startup
            DeploymentUtils.log_deployment_step(
                "monitoring", "simulated", "Monitoring services would be started", dry_run_log
            )
            
            logger.info("Deployment dry run completed successfully")
            
            return {
                "status": "success",
                "message": "Dry run completed successfully",
                "log": dry_run_log,
                "config": self.deployment_config
            }
            
        except Exception as e:
            logger.error(f"Deployment dry run failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "log": dry_run_log,
                "config": self.deployment_config
            }
    
    async def rollback_to_backup(self, backup_name: Optional[str] = None) -> bool:
        """Rollback to a specific backup or the latest backup."""
        logger.info(f"Rolling back to backup: {backup_name or 'latest'}")
        
        try:
            if backup_name:
                # Rollback to specific backup
                backup_path = Path("backups") / backup_name
                if not backup_path.exists():
                    raise Exception(f"Backup not found: {backup_name}")
                
                await self.backup_manager.restore_backup(backup_path, self.deployment_log)
            else:
                # Rollback to latest backup
                await self.rollback_manager.rollback_deployment(self.deployment_log)
            
            self.deployment_status = "rolled_back"
            logger.info("Rollback completed successfully")
            
            # Publish rollback event
            await self.event_bus.publish(
                "deployment_rolled_back",
                {
                    "status": "success",
                    "backup_name": backup_name,
                    "deployment_log": self.deployment_log
                },
                source="deployment_manager"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            
            # Publish rollback failure event
            await self.event_bus.publish(
                "rollback_failed",
                {
                    "status": "failed",
                    "error": str(e),
                    "backup_name": backup_name
                },
                source="deployment_manager"
            )
            
            return False
    
    def list_available_backups(self) -> List[str]:
        """List available backup directories."""
        backup_dir = Path("backups")
        if not backup_dir.exists():
            return []
        
        return [backup.name for backup in backup_dir.glob("deployment_*") if backup.is_dir()]

