#!/usr/bin/env python3
"""
Enhanced Deployment Script - Refactored
======================================

Notes:
- API server entrypoint (when running directly): run_unified.py
- Web interface entrypoint: run_web.py
- Containerized deployments handle these via docker-compose.

Refactored production deployment script with modular architecture.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.deployment.deployment_manager import DeploymentManager

logger = logging.getLogger(__name__)


async def main():
    """Main deployment function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Deployment configuration
    deployment_config = {
        "deployment": {
            "environment": "production",
            "monitoring_port": 8082,
            "health_check_interval": 30,
            "max_retries": 3,
            "rollback_on_failure": True,
            "backup_before_deploy": True
        },
        "config_updates": {
            "config/sources.unified.yaml": {
                "deployment_timestamp": "2024-01-01T00:00:00Z"
            }
        }
    }
    
    # Create deployment manager
    deployment_manager = DeploymentManager(deployment_config)
    
    try:
        # Check command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "dry-run":
                # Perform dry run
                results = await deployment_manager.dry_run_deployment()
                print("🔍 Deployment Dry Run Results:")
                print(f"Status: {results['status']}")
                if results['status'] == 'success':
                    print("✅ Dry run completed successfully - deployment would proceed")
                else:
                    print(f"❌ Dry run failed: {results.get('error', 'Unknown error')}")
                return
            
            elif command == "rollback":
                # Rollback deployment
                backup_name = sys.argv[2] if len(sys.argv) > 2 else None
                success = await deployment_manager.rollback_to_backup(backup_name)
                if success:
                    print("✅ Rollback completed successfully")
                else:
                    print("❌ Rollback failed")
                    sys.exit(1)
                return
            
            elif command == "list-backups":
                # List available backups
                backups = deployment_manager.list_available_backups()
                print("📦 Available Backups:")
                for backup in backups:
                    print(f"  - {backup}")
                return
            
            elif command == "status":
                # Show deployment status
                status = deployment_manager.get_deployment_status()
                print("📊 Deployment Status:")
                print(f"Status: {status['status']}")
                print(f"Steps Completed: {status['summary']['steps_completed']}")
                print(f"Total Steps: {status['summary']['total_steps']}")
                if status['summary']['failed_steps'] > 0:
                    print(f"Failed Steps: {status['summary']['failed_steps']}")
                return
            
            else:
                print(f"Unknown command: {command}")
                print("Available commands: dry-run, rollback, list-backups, status")
                return
        
        # Execute deployment
        success = await deployment_manager.deploy()
        
        if success:
            logger.info("Deployment completed successfully!")
            print("✅ Deployment completed successfully!")
            print(f"📊 Monitoring dashboard available at: http://localhost:{deployment_config['deployment']['monitoring_port']}")
        else:
            logger.error("Deployment failed!")
            print("❌ Deployment failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
        print("⏹️ Deployment interrupted by user")
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        print(f"❌ Deployment error: {e}")
        sys.exit(1)
    finally:
        # Stop monitoring if running
        await deployment_manager.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())

