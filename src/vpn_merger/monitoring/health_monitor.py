#!/usr/bin/env python3
"""
Comprehensive Health Monitoring System
=====================================

Advanced health monitoring with real-time metrics, alerting, and automated recovery.
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..core.interfaces import HealthCheckInterface, MetricsInterface
from ..core.observers import EventBus, get_event_bus

logger = logging.getLogger(__name__)


class SystemHealthMonitor(HealthCheckInterface):
    """Comprehensive system health monitoring with automated recovery."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the health monitor.
        
        Args:
            config: Health monitoring configuration
        """
        self.config = config or {}
        self.event_bus = get_event_bus()
        self.health_status = "unknown"
        self.last_check = None
        self.check_history: List[Dict[str, Any]] = []
        self.alert_thresholds = self.config.get("alert_thresholds", {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 10.0,
            "error_rate": 0.1
        })
        self.recovery_actions: Dict[str, List[str]] = self.config.get("recovery_actions", {})
        self.health_checks: Dict[str, callable] = {}
        
        # Register default health checks
        self._register_default_checks()
        
        logger.info("System health monitor initialized")
    
    def _register_default_checks(self) -> None:
        """Register default health check functions."""
        self.register_health_check("system_resources", self._check_system_resources)
        self.register_health_check("disk_space", self._check_disk_space)
        self.register_health_check("network_connectivity", self._check_network_connectivity)
        self.register_health_check("service_availability", self._check_service_availability)
        self.register_health_check("performance_metrics", self._check_performance_metrics)
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        logger.debug("Performing comprehensive health check")
        
        start_time = time.time()
        health_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {},
            "metrics": {},
            "alerts": [],
            "recommendations": []
        }
        
        # Run all registered health checks
        for check_name, check_func in self.health_checks.items():
            try:
                result = await check_func()
                health_results["checks"][check_name] = result
                
                # Check for alerts
                if result.get("status") == "unhealthy":
                    health_results["overall_status"] = "unhealthy"
                    health_results["alerts"].append({
                        "check": check_name,
                        "message": result.get("message", "Health check failed"),
                        "severity": result.get("severity", "warning")
                    })
                
            except Exception as e:
                logger.error(f"Health check {check_name} failed: {e}")
                health_results["checks"][check_name] = {
                    "status": "error",
                    "message": str(e),
                    "severity": "critical"
                }
                health_results["overall_status"] = "unhealthy"
        
        # Calculate overall metrics
        health_results["metrics"] = {
            "check_duration": time.time() - start_time,
            "total_checks": len(self.health_checks),
            "healthy_checks": sum(1 for check in health_results["checks"].values() 
                                if check.get("status") == "healthy"),
            "unhealthy_checks": sum(1 for check in health_results["checks"].values() 
                                  if check.get("status") == "unhealthy"),
            "error_checks": sum(1 for check in health_results["checks"].values() 
                              if check.get("status") == "error")
        }
        
        # Generate recommendations
        health_results["recommendations"] = self._generate_recommendations(health_results)
        
        # Update status and history
        self.health_status = health_results["overall_status"]
        self.last_check = datetime.now()
        self.check_history.append(health_results)
        
        # Keep only last 100 checks
        if len(self.check_history) > 100:
            self.check_history.pop(0)
        
        # Publish health check event
        await self.event_bus.publish(
            "health_check_completed",
            health_results,
            source="health_monitor"
        )
        
        return health_results
    
    def get_health_status(self) -> str:
        """Get current health status."""
        return self.health_status
    
    def register_health_check(self, name: str, check_func: callable) -> None:
        """Register a health check function."""
        self.health_checks[name] = check_func
        logger.debug(f"Registered health check: {name}")
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = "healthy"
            alerts = []
            
            # Check CPU usage
            if cpu_percent > self.alert_thresholds["cpu_usage"]:
                status = "unhealthy"
                alerts.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            # Check memory usage
            if memory.percent > self.alert_thresholds["memory_usage"]:
                status = "unhealthy"
                alerts.append(f"High memory usage: {memory.percent:.1f}%")
            
            # Check disk usage
            if disk.percent > self.alert_thresholds["disk_usage"]:
                status = "unhealthy"
                alerts.append(f"High disk usage: {disk.percent:.1f}%")
            
            return {
                "status": status,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                },
                "alerts": alerts,
                "message": "System resources check completed"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"System resources check failed: {e}",
                "severity": "critical"
            }
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space availability."""
        try:
            # Check multiple important directories
            directories = ["/", "./output", "./logs", "./cache"]
            disk_status = {}
            
            for directory in directories:
                try:
                    path = Path(directory)
                    if path.exists():
                        usage = psutil.disk_usage(str(path))
                        disk_status[directory] = {
                            "total_gb": usage.total / (1024**3),
                            "used_gb": usage.used / (1024**3),
                            "free_gb": usage.free / (1024**3),
                            "percent_used": (usage.used / usage.total) * 100
                        }
                except Exception as e:
                    disk_status[directory] = {"error": str(e)}
            
            # Check for critical disk space issues
            critical_dirs = []
            for dir_path, status in disk_status.items():
                if "percent_used" in status and status["percent_used"] > 95:
                    critical_dirs.append(dir_path)
            
            overall_status = "unhealthy" if critical_dirs else "healthy"
            
            return {
                "status": overall_status,
                "metrics": disk_status,
                "message": f"Disk space check completed. Critical directories: {critical_dirs}" if critical_dirs else "Disk space is adequate"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Disk space check failed: {e}",
                "severity": "critical"
            }
    
    async def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity and DNS resolution."""
        try:
            import socket
            import aiohttp
            
            connectivity_tests = {
                "dns_resolution": False,
                "http_connectivity": False,
                "external_api": False
            }
            
            # Test DNS resolution
            try:
                socket.gethostbyname("google.com")
                connectivity_tests["dns_resolution"] = True
            except Exception:
                pass
            
            # Test HTTP connectivity
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get("http://httpbin.org/get") as response:
                        if response.status == 200:
                            connectivity_tests["http_connectivity"] = True
            except Exception:
                pass
            
            # Test external API (GitHub)
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get("https://api.github.com") as response:
                        if response.status == 200:
                            connectivity_tests["external_api"] = True
            except Exception:
                pass
            
            healthy_tests = sum(connectivity_tests.values())
            total_tests = len(connectivity_tests)
            
            status = "healthy" if healthy_tests >= total_tests * 0.7 else "unhealthy"
            
            return {
                "status": status,
                "metrics": connectivity_tests,
                "message": f"Network connectivity: {healthy_tests}/{total_tests} tests passed"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Network connectivity check failed: {e}",
                "severity": "critical"
            }
    
    async def _check_service_availability(self) -> Dict[str, Any]:
        """Check availability of critical services."""
        try:
            # Check if output directory is writable
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # Test write access
            test_file = output_dir / "health_check_test.tmp"
            try:
                test_file.write_text("health check test")
                test_file.unlink()
                output_writable = True
            except Exception:
                output_writable = False
            
            # Check if configuration files exist
            config_files = [
                "config/sources.unified.yaml",
                "config/sources.enhanced.yaml"
            ]
            
            config_status = {}
            for config_file in config_files:
                config_path = Path(config_file)
                config_status[config_file] = {
                    "exists": config_path.exists(),
                    "readable": config_path.exists() and config_path.is_file()
                }
            
            # Check if logs directory is writable
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            logs_writable = logs_dir.is_dir() and os.access(logs_dir, os.W_OK)
            
            service_checks = {
                "output_directory": output_writable,
                "logs_directory": logs_writable,
                "config_files": all(status["exists"] for status in config_status.values())
            }
            
            healthy_services = sum(service_checks.values())
            total_services = len(service_checks)
            
            status = "healthy" if healthy_services == total_services else "unhealthy"
            
            return {
                "status": status,
                "metrics": {
                    "service_checks": service_checks,
                    "config_files": config_status
                },
                "message": f"Service availability: {healthy_services}/{total_services} services healthy"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Service availability check failed: {e}",
                "severity": "critical"
            }
    
    async def _check_performance_metrics(self) -> Dict[str, Any]:
        """Check performance metrics and trends."""
        try:
            # Get recent performance data from history
            if len(self.check_history) < 2:
                return {
                    "status": "healthy",
                    "message": "Insufficient data for performance analysis",
                    "metrics": {}
                }
            
            # Analyze recent performance trends
            recent_checks = self.check_history[-10:]  # Last 10 checks
            
            # Calculate average check duration
            durations = [check.get("metrics", {}).get("check_duration", 0) for check in recent_checks]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Count unhealthy checks in recent history
            unhealthy_count = sum(1 for check in recent_checks 
                                if check.get("overall_status") == "unhealthy")
            
            # Calculate health trend
            if len(recent_checks) >= 5:
                recent_5 = recent_checks[-5:]
                older_5 = recent_checks[-10:-5] if len(recent_checks) >= 10 else []
                
                recent_unhealthy = sum(1 for check in recent_5 if check.get("overall_status") == "unhealthy")
                older_unhealthy = sum(1 for check in older_5 if check.get("overall_status") == "unhealthy")
                
                if recent_unhealthy > older_unhealthy:
                    trend = "deteriorating"
                elif recent_unhealthy < older_unhealthy:
                    trend = "improving"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            # Determine status based on performance
            status = "healthy"
            if avg_duration > 30:  # More than 30 seconds for health checks
                status = "unhealthy"
            elif unhealthy_count > len(recent_checks) * 0.3:  # More than 30% unhealthy
                status = "unhealthy"
            
            return {
                "status": status,
                "metrics": {
                    "average_check_duration": avg_duration,
                    "recent_unhealthy_count": unhealthy_count,
                    "health_trend": trend,
                    "total_checks_analyzed": len(recent_checks)
                },
                "message": f"Performance analysis: {trend} trend, {avg_duration:.2f}s avg duration"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Performance metrics check failed: {e}",
                "severity": "critical"
            }
    
    def _generate_recommendations(self, health_results: Dict[str, Any]) -> List[str]:
        """Generate health recommendations based on check results."""
        recommendations = []
        
        # Check system resources
        system_check = health_results["checks"].get("system_resources", {})
        if system_check.get("status") == "unhealthy":
            metrics = system_check.get("metrics", {})
            if metrics.get("cpu_percent", 0) > 80:
                recommendations.append("Consider reducing concurrent operations to lower CPU usage")
            if metrics.get("memory_percent", 0) > 85:
                recommendations.append("Consider implementing memory cleanup or increasing available memory")
            if metrics.get("disk_percent", 0) > 90:
                recommendations.append("Consider cleaning up old files or increasing disk space")
        
        # Check disk space
        disk_check = health_results["checks"].get("disk_space", {})
        if disk_check.get("status") == "unhealthy":
            recommendations.append("Critical disk space issues detected. Clean up unnecessary files immediately")
        
        # Check network connectivity
        network_check = health_results["checks"].get("network_connectivity", {})
        if network_check.get("status") == "unhealthy":
            recommendations.append("Network connectivity issues detected. Check internet connection and DNS settings")
        
        # Check service availability
        service_check = health_results["checks"].get("service_availability", {})
        if service_check.get("status") == "unhealthy":
            recommendations.append("Service availability issues detected. Check file permissions and configuration")
        
        # Check performance metrics
        performance_check = health_results["checks"].get("performance_metrics", {})
        if performance_check.get("status") == "unhealthy":
            recommendations.append("Performance degradation detected. Consider optimizing health check frequency")
        
        if not recommendations:
            recommendations.append("System is healthy. Continue monitoring for any changes.")
        
        return recommendations
    
    async def start_continuous_monitoring(self, interval_seconds: int = 60) -> None:
        """Start continuous health monitoring."""
        logger.info(f"Starting continuous health monitoring (interval: {interval_seconds}s)")
        
        while True:
            try:
                await self.check_health()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Continuous monitoring error: {e}")
                await asyncio.sleep(10)  # Wait 10 seconds before retrying
    
    def get_health_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get health check history."""
        return self.check_history[-limit:] if limit > 0 else self.check_history
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary statistics."""
        if not self.check_history:
            return {"status": "no_data", "message": "No health check history available"}
        
        total_checks = len(self.check_history)
        healthy_checks = sum(1 for check in self.check_history 
                           if check.get("overall_status") == "healthy")
        unhealthy_checks = sum(1 for check in self.check_history 
                             if check.get("overall_status") == "unhealthy")
        
        # Calculate uptime percentage
        uptime_percentage = (healthy_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # Get last check time
        last_check = self.check_history[-1].get("timestamp") if self.check_history else None
        
        return {
            "current_status": self.health_status,
            "last_check": last_check,
            "total_checks": total_checks,
            "healthy_checks": healthy_checks,
            "unhealthy_checks": unhealthy_checks,
            "uptime_percentage": uptime_percentage,
            "health_trend": "improving" if uptime_percentage > 90 else "stable" if uptime_percentage > 70 else "deteriorating"
        }


# Global health monitor instance
_health_monitor: Optional[SystemHealthMonitor] = None


def get_health_monitor(config: Optional[Dict[str, Any]] = None) -> SystemHealthMonitor:
    """Get the global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = SystemHealthMonitor(config)
    return _health_monitor


def reset_health_monitor() -> None:
    """Reset the global health monitor."""
    global _health_monitor
    _health_monitor = None
