#!/usr/bin/env python3
"""
Deployment Manager for VPN Subscription Merger
Handles production deployment with Kubernetes, Docker, and monitoring setup.
"""

import asyncio
import json
import logging
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import with fallbacks for missing modules
try:
    import docker
except ImportError:
    docker = None

try:
    import kubernetes
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
except ImportError:
    kubernetes = None
    client = None
    config = None
    ApiException = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeploymentManager:
    """Manage production deployment of VPN Subscription Merger."""
    
    def __init__(self, config_dir: str = "k8s"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize Docker client with fallback
        try:
            if docker:
                self.docker_client = docker.from_env()
            else:
                self.docker_client = None
        except Exception as e:
            logger.warning(f"Could not initialize Docker client: {e}")
            self.docker_client = None
        
        # Initialize Kubernetes client with fallback
        try:
            if kubernetes:
                config.load_kube_config()
                self.k8s_client = client.CoreV1Api()
                self.k8s_apps_client = client.AppsV1Api()
                self.k8s_autoscaling_client = client.AutoscalingV1Api()
            else:
                self.k8s_client = None
                self.k8s_apps_client = None
                self.k8s_autoscaling_client = None
        except Exception as e:
            logger.warning(f"Could not initialize Kubernetes client: {e}")
            self.k8s_client = None
            self.k8s_apps_client = None
            self.k8s_autoscaling_client = None
    
    def build_docker_image(self, tag: str = "vpn-merger:latest", production: bool = True) -> bool:
        """Build Docker image for deployment."""
        try:
            logger.info(f"Building Docker image: {tag}")
            
            # Choose Dockerfile
            dockerfile = "Dockerfile.production" if production else "Dockerfile"
            
            # Build image with fallback
            if self.docker_client:
                image, logs = self.docker_client.images.build(
                    path=".",
                    dockerfile=dockerfile,
                    tag=tag,
                    rm=True
                )
                
                logger.info(f"Docker image built successfully: {image.id}")
                return True
            else:
                # Use docker command
                cmd = [
                    "docker", "build",
                    "-f", dockerfile,
                    "-t", tag,
                    "."
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"Docker image built successfully: {tag}")
                    return True
                else:
                    logger.error(f"Docker build failed: {result.stderr}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error building Docker image: {e}")
            return False
    
    def create_k8s_configmap(self, namespace: str = "vpn-merger") -> bool:
        """Create Kubernetes ConfigMap."""
        try:
            if not self.k8s_client:
                logger.error("Kubernetes client not available")
                return False
            
            # Create ConfigMap with source configuration
            configmap_data = {
                "sources.unified.yaml": self.get_source_config_yaml(),
                "performance_optimized.yaml": self.get_performance_config_yaml()
            }
            
            configmap = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(
                    name="vpn-merger-config",
                    namespace=namespace
                ),
                data=configmap_data
            )
            
            try:
                self.k8s_client.read_namespaced_config_map(
                    "vpn-merger-config", namespace
                )
                # Update existing ConfigMap
                self.k8s_client.replace_namespaced_config_map(
                    "vpn-merger-config", namespace, configmap
                )
                logger.info("Updated ConfigMap: vpn-merger-config")
            except ApiException as e:
                if e.status == 404:
                    # Create new ConfigMap
                    self.k8s_client.create_namespaced_config_map(namespace, configmap)
                    logger.info("Created ConfigMap: vpn-merger-config")
                else:
                    raise
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating ConfigMap: {e}")
            return False
    
    def deploy_k8s_application(self, namespace: str = "vpn-merger", image_tag: str = "vpn-merger:latest") -> bool:
        """Deploy application to Kubernetes."""
        try:
            if not self.k8s_apps_client:
                logger.error("Kubernetes apps client not available")
                return False
            
            # Create deployment
            deployment = client.V1Deployment(
                metadata=client.V1ObjectMeta(
                    name="vpn-merger",
                    namespace=namespace
                ),
                spec=client.V1DeploymentSpec(
                    replicas=3,
                    selector=client.V1LabelSelector(
                        match_labels={"app": "vpn-merger"}
                    ),
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(
                            labels={"app": "vpn-merger"}
                        ),
                        spec=client.V1PodSpec(
                            containers=[
                                client.V1Container(
                                    name="vpn-merger",
                                    image=image_tag,
                                    ports=[
                                        client.V1ContainerPort(container_port=8000)
                                    ],
                                    env=[
                                        client.V1EnvVar(
                                            name="LOG_LEVEL",
                                            value="INFO"
                                        ),
                                        client.V1EnvVar(
                                            name="METRICS_ENABLED",
                                            value="1"
                                        )
                                    ],
                                    resources=client.V1ResourceRequirements(
                                        requests={
                                            "cpu": "100m",
                                            "memory": "256Mi"
                                        },
                                        limits={
                                            "cpu": "500m",
                                            "memory": "1Gi"
                                        }
                                    )
                                )
                            ]
                        )
                    )
                )
            )
            
            try:
                self.k8s_apps_client.read_namespaced_deployment(
                    "vpn-merger", namespace
                )
                # Update existing deployment
                self.k8s_apps_client.replace_namespaced_deployment(
                    "vpn-merger", namespace, deployment
                )
                logger.info("Updated Deployment: vpn-merger")
            except ApiException as e:
                if e.status == 404:
                    # Create new deployment
                    self.k8s_apps_client.create_namespaced_deployment(namespace, deployment)
                    logger.info("Created Deployment: vpn-merger")
                else:
                    raise
            
            return True
            
        except Exception as e:
            logger.error(f"Error deploying application: {e}")
            return False
    
    def get_source_config_yaml(self) -> str:
        """Get source configuration YAML content."""
        try:
            config_path = Path("config/sources.unified.yaml")
            if config_path.exists():
                return config_path.read_text()
            else:
                return "# Default source configuration"
        except Exception as e:
            logger.error(f"Error reading source config: {e}")
            return "# Error reading source configuration"
    
    def get_performance_config_yaml(self) -> str:
        """Get performance configuration YAML content."""
        try:
            config_path = Path("config/performance_optimized.yaml")
            if config_path.exists():
                return config_path.read_text()
            else:
                return "# Default performance configuration"
        except Exception as e:
            logger.error(f"Error reading performance config: {e}")
            return "# Error reading performance configuration"
    
    def deploy_to_production(self, image_tag: str = "vpn-merger:latest") -> bool:
        """Complete production deployment."""
        try:
            logger.info("Starting production deployment...")
            
            # Build Docker image
            if not self.build_docker_image(image_tag, production=True):
                logger.error("Failed to build Docker image")
                return False
            
            # Deploy to Kubernetes
            namespace = "vpn-merger"
            
            # Create ConfigMap
            if not self.create_k8s_configmap(namespace):
                logger.error("Failed to create ConfigMap")
                return False
            
            # Deploy application
            if not self.deploy_k8s_application(namespace, image_tag):
                logger.error("Failed to deploy application")
                return False
            
            logger.info("Production deployment completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Production deployment failed: {e}")
            return False


async def main():
    """Main deployment function."""
    manager = DeploymentManager()
    
    # Deploy to production
    success = manager.deploy_to_production(
        image_tag="vpn-merger:v2.0.0"
    )
    
    if success:
        logger.info("Deployment completed successfully!")
    else:
        logger.error("Deployment failed!")


if __name__ == "__main__":
    asyncio.run(main())
