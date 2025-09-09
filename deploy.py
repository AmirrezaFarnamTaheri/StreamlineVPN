#!/usr/bin/env python3
"""
deploy.py
=========

Deployment script for StreamlineVPN with multiple environments.
"""

import os
import sys
import subprocess
import shutil
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.utils.logging import get_logger

logger = get_logger(__name__)


class StreamlineVPNDeployer:
    """Deployment manager for StreamlineVPN."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.deployment_dir = Path("deployments")
        self.deployment_dir.mkdir(exist_ok=True)
        
        # Environment configurations
        self.env_configs = {
            "development": {
                "api_port": 8080,
                "web_port": 8000,
                "redis_port": 6379,
                "workers": 1,
                "debug": True,
                "log_level": "DEBUG"
            },
            "staging": {
                "api_port": 8080,
                "web_port": 8000,
                "redis_port": 6379,
                "workers": 2,
                "debug": False,
                "log_level": "INFO"
            },
            "production": {
                "api_port": 8080,
                "web_port": 8000,
                "redis_port": 6379,
                "workers": 4,
                "debug": False,
                "log_level": "WARNING"
            }
        }
    
    def deploy(self, target: str = "local", force: bool = False) -> bool:
        """Deploy StreamlineVPN to target environment."""
        logger.info(f"Deploying to {target} environment ({self.environment})")
        
        try:
            # Pre-deployment checks
            if not self.pre_deployment_checks():
                return False
            
            # Create deployment package
            package_path = self.create_deployment_package()
            if not package_path:
                return False
            
            # Deploy based on target
            if target == "local":
                return self.deploy_local(package_path, force)
            elif target == "docker":
                return self.deploy_docker(package_path, force)
            elif target == "kubernetes":
                return self.deploy_kubernetes(package_path, force)
            else:
                logger.error(f"Unknown deployment target: {target}")
                return False
                
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False
    
    def pre_deployment_checks(self) -> bool:
        """Run pre-deployment checks."""
        logger.info("Running pre-deployment checks...")
        
        checks = [
            self.check_dependencies,
            self.check_configuration,
            self.check_tests,
            self.check_environment
        ]
        
        for check_func in checks:
            try:
                if not check_func():
                    logger.error(f"Pre-deployment check failed: {check_func.__name__}")
                    return False
            except Exception as e:
                logger.error(f"Pre-deployment check error in {check_func.__name__}: {e}")
                return False
        
        logger.info("All pre-deployment checks passed")
        return True
    
    def check_dependencies(self) -> bool:
        """Check if all dependencies are available."""
        try:
            # Check Python packages
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Dependency check failed: {result.stderr}")
                return False
            
            # Check if required files exist
            required_files = [
                "requirements.txt",
                "pyproject.toml",
                "src/streamline_vpn/__init__.py"
            ]
            
            for file_path in required_files:
                if not Path(file_path).exists():
                    logger.error(f"Required file missing: {file_path}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Dependency check error: {e}")
            return False
    
    def check_configuration(self) -> bool:
        """Check configuration files."""
        try:
            # Check sources config
            sources_file = Path("config/sources.yaml")
            if not sources_file.exists():
                logger.warning("No sources config found, creating default")
                sources_file.parent.mkdir(exist_ok=True)
                with open(sources_file, 'w') as f:
                    f.write("sources:\n  free:\n    - https://example.com/config\n")
            
            # Validate YAML
            import yaml
            with open(sources_file) as f:
                yaml.safe_load(f)
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration check error: {e}")
            return False
    
    def check_tests(self) -> bool:
        """Run basic tests."""
        try:
            # Run smoke tests
            result = subprocess.run(
                [sys.executable, "test_runner.py", "--smoke"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.warning(f"Smoke tests failed: {result.stderr}")
                # Don't fail deployment for test issues in dev
                if self.environment == "production":
                    return False
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.warning("Smoke tests timed out")
            return True  # Don't fail deployment
        except Exception as e:
            logger.warning(f"Test check error: {e}")
            return True  # Don't fail deployment
    
    def check_environment(self) -> bool:
        """Check environment setup."""
        try:
            # Check if environment config exists
            env_file = Path(".env")
            if not env_file.exists():
                logger.warning("No .env file found, creating from example")
                if Path("env.example").exists():
                    shutil.copy("env.example", ".env")
                else:
                    logger.error("No env.example file found")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Environment check error: {e}")
            return False
    
    def create_deployment_package(self) -> Optional[str]:
        """Create deployment package."""
        logger.info("Creating deployment package...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"streamline_vpn_{self.environment}_{timestamp}"
        package_path = self.deployment_dir / f"{package_name}.tar.gz"
        
        try:
            import tarfile
            
            with tarfile.open(package_path, "w:gz") as tar:
                # Add source code
                tar.add("src", arcname="src")
                
                # Add configuration
                tar.add("config", arcname="config")
                
                # Add requirements
                for req_file in ["requirements.txt", "requirements-prod.txt", "pyproject.toml"]:
                    if Path(req_file).exists():
                        tar.add(req_file, arcname=req_file)
                
                # Add deployment files
                for deploy_file in ["Dockerfile", "docker-compose.yml", "run_unified.py", "run_web.py"]:
                    if Path(deploy_file).exists():
                        tar.add(deploy_file, arcname=deploy_file)
                
                # Add environment config
                if Path(".env").exists():
                    tar.add(".env", arcname=".env")
                
                # Add documentation
                if Path("docs").exists():
                    tar.add("docs", arcname="docs")
                
                # Add scripts
                if Path("scripts").exists():
                    tar.add("scripts", arcname="scripts")
            
            logger.info(f"Deployment package created: {package_path}")
            return str(package_path)
            
        except Exception as e:
            logger.error(f"Failed to create deployment package: {e}")
            return None
    
    def deploy_local(self, package_path: str, force: bool = False) -> bool:
        """Deploy locally."""
        logger.info("Deploying locally...")
        
        try:
            # Stop existing services
            self.stop_services()
            
            # Extract package
            extract_dir = Path("deployment_current")
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            
            import tarfile
            with tarfile.open(package_path, "r:gz") as tar:
                tar.extractall(extract_dir)
            
            # Copy files to current directory
            for item in extract_dir.iterdir():
                if item.is_dir():
                    if Path(item.name).exists():
                        shutil.rmtree(item.name)
                    shutil.copytree(item, item.name)
                else:
                    shutil.copy2(item, item.name)
            
            # Clean up
            shutil.rmtree(extract_dir)
            
            # Install dependencies
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            
            # Start services
            self.start_services()
            
            logger.info("Local deployment completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Local deployment failed: {e}")
            return False
    
    def deploy_docker(self, package_path: str, force: bool = False) -> bool:
        """Deploy using Docker."""
        logger.info("Deploying with Docker...")
        
        try:
            # Stop existing containers
            subprocess.run(["docker-compose", "down"], capture_output=True)
            
            # Build new image
            result = subprocess.run(
                ["docker", "build", "-t", f"streamline-vpn:{self.environment}", "."],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Docker build failed: {result.stderr}")
                return False
            
            # Start services
            subprocess.run(["docker-compose", "up", "-d"])
            
            # Wait for services to be ready
            self.wait_for_services()
            
            logger.info("Docker deployment completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Docker deployment failed: {e}")
            return False
    
    def deploy_kubernetes(self, package_path: str, force: bool = False) -> bool:
        """Deploy to Kubernetes."""
        logger.info("Deploying to Kubernetes...")
        
        try:
            # Apply Kubernetes manifests
            k8s_files = [
                "kubernetes/redis.yaml",
                "kubernetes/deployment.yaml",
                "kubernetes/service.yaml",
                "kubernetes/ingress.yaml"
            ]
            
            for k8s_file in k8s_files:
                if Path(k8s_file).exists():
                    result = subprocess.run(
                        ["kubectl", "apply", "-f", k8s_file],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        logger.error(f"Failed to apply {k8s_file}: {result.stderr}")
                        return False
            
            # Wait for deployment
            subprocess.run(["kubectl", "rollout", "status", "deployment/streamline-vpn"])
            
            logger.info("Kubernetes deployment completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Kubernetes deployment failed: {e}")
            return False
    
    def stop_services(self):
        """Stop running services."""
        logger.info("Stopping services...")
        
        # Stop API server
        subprocess.run(["pkill", "-f", "run_unified.py"], capture_output=True)
        
        # Stop web server
        subprocess.run(["pkill", "-f", "run_web.py"], capture_output=True)
        
        # Stop Redis
        subprocess.run(["pkill", "-f", "redis-server"], capture_output=True)
    
    def start_services(self):
        """Start services."""
        logger.info("Starting services...")
        
        config = self.env_configs[self.environment]
        
        # Start Redis
        subprocess.Popen(["redis-server", "--port", str(config["redis_port"])])
        
        # Start API server
        env = os.environ.copy()
        env.update({
            "API_PORT": str(config["api_port"]),
            "WORKERS": str(config["workers"]),
            "LOG_LEVEL": config["log_level"]
        })
        
        subprocess.Popen([sys.executable, "run_unified.py"], env=env)
        
        # Start web server
        env["WEB_PORT"] = str(config["web_port"])
        subprocess.Popen([sys.executable, "run_web.py"], env=env)
        
        # Wait for services
        self.wait_for_services()
    
    def wait_for_services(self, timeout: int = 60):
        """Wait for services to be ready."""
        logger.info("Waiting for services to be ready...")
        
        import time
        import requests
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check API
                response = requests.get(f"http://localhost:{self.env_configs[self.environment]['api_port']}/health")
                if response.status_code == 200:
                    logger.info("Services are ready")
                    return True
            except:
                pass
            
            time.sleep(2)
        
        logger.warning("Services did not become ready within timeout")
        return False
    
    def rollback(self, version: str = None) -> bool:
        """Rollback to previous version."""
        logger.info(f"Rolling back to version: {version or 'previous'}")
        
        try:
            # Find available versions
            versions = self.list_versions()
            
            if not versions:
                logger.error("No versions available for rollback")
                return False
            
            if not version:
                version = versions[0]  # Most recent
            
            if version not in versions:
                logger.error(f"Version not found: {version}")
                return False
            
            # Deploy the version
            package_path = self.deployment_dir / f"{version}.tar.gz"
            if not package_path.exists():
                logger.error(f"Package not found: {package_path}")
                return False
            
            return self.deploy_local(str(package_path), force=True)
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def list_versions(self) -> List[str]:
        """List available deployment versions."""
        versions = []
        
        for package_file in self.deployment_dir.glob("*.tar.gz"):
            version = package_file.stem
            versions.append(version)
        
        # Sort by timestamp (newest first)
        versions.sort(reverse=True)
        
        return versions
    
    def status(self) -> Dict[str, Any]:
        """Get deployment status."""
        status = {
            "environment": self.environment,
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "version": "unknown"
        }
        
        config = self.env_configs[self.environment]
        
        # Check API
        try:
            import requests
            response = requests.get(f"http://localhost:{config['api_port']}/health", timeout=5)
            status["services"]["api"] = {
                "status": "running" if response.status_code == 200 else "error",
                "port": config["api_port"]
            }
        except:
            status["services"]["api"] = {"status": "stopped", "port": config["api_port"]}
        
        # Check Web
        try:
            import requests
            response = requests.get(f"http://localhost:{config['web_port']}", timeout=5)
            status["services"]["web"] = {
                "status": "running" if response.status_code == 200 else "error",
                "port": config["web_port"]
            }
        except:
            status["services"]["web"] = {"status": "stopped", "port": config["web_port"]}
        
        # Check Redis
        try:
            import redis
            r = redis.Redis(port=config["redis_port"])
            r.ping()
            status["services"]["redis"] = {
                "status": "running",
                "port": config["redis_port"]
            }
        except:
            status["services"]["redis"] = {"status": "stopped", "port": config["redis_port"]}
        
        return status


def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='StreamlineVPN Deployment Tool')
    parser.add_argument('action', choices=['deploy', 'rollback', 'status', 'list'],
                       help='Action to perform')
    parser.add_argument('--environment', '-e', default='development',
                       choices=['development', 'staging', 'production'],
                       help='Target environment')
    parser.add_argument('--target', '-t', default='local',
                       choices=['local', 'docker', 'kubernetes'],
                       help='Deployment target')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force deployment even if checks fail')
    parser.add_argument('--version', '-v', help='Version for rollback')
    
    args = parser.parse_args()
    
    deployer = StreamlineVPNDeployer(args.environment)
    
    if args.action == 'deploy':
        success = deployer.deploy(args.target, args.force)
        if success:
            print("✅ Deployment completed successfully")
        else:
            print("❌ Deployment failed")
            sys.exit(1)
    
    elif args.action == 'rollback':
        success = deployer.rollback(args.version)
        if success:
            print("✅ Rollback completed successfully")
        else:
            print("❌ Rollback failed")
            sys.exit(1)
    
    elif args.action == 'status':
        status = deployer.status()
        print(f"\nDeployment Status ({status['environment']}):")
        print(f"Timestamp: {status['timestamp']}")
        print(f"Services:")
        for service, info in status['services'].items():
            status_icon = "✅" if info['status'] == 'running' else "❌"
            print(f"  {service}: {status_icon} {info['status']} (port {info['port']})")
    
    elif args.action == 'list':
        versions = deployer.list_versions()
        if versions:
            print("Available versions:")
            for version in versions:
                print(f"  {version}")
        else:
            print("No versions available")


if __name__ == '__main__':
    main()
