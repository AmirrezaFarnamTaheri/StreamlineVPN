"""
Performance validation.
"""

from pathlib import Path
from typing import Dict, Any
from .base_validator import BaseValidator


class PerformanceValidator(BaseValidator):
    """Validates performance configurations and optimizations."""
    
    def validate_performance_configurations(self):
        """Validate performance-related configurations."""
        print("⚡ Validating performance configurations...")
        
        # Check for caching implementations
        self._validate_caching_implementation()
        
        # Check for async implementations
        self._validate_async_implementation()
        
        # Check for monitoring/metrics
        self._validate_monitoring_implementation()
    
    def _validate_caching_implementation(self):
        """Validate caching implementation."""
        cache_files = [
            "src/streamline_vpn/caching/l1_cache.py",
            "src/streamline_vpn/caching/l2_cache.py", 
            "src/streamline_vpn/caching/l3_cache.py"
        ]
        
        cache_found = False
        for cache_file in cache_files:
            if self._check_file_exists(cache_file, f"Cache module: {cache_file}"):
                cache_found = True
                self._validate_cache_module(cache_file)
        
        if cache_found:
            self._add_check_result(
                "caching_implementation",
                "PASS",
                "Caching modules found"
            )
        else:
            self._add_check_result(
                "caching_implementation",
                "WARN",
                "No caching modules found"
            )
    
    def _validate_async_implementation(self):
        """Validate async implementation."""
        # Check for async patterns in Python files
        python_files = list(self.project_root.rglob("*.py"))
        async_files = []
        
        for py_file in python_files:
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue
            
            content = self._read_file_content(str(py_file.relative_to(self.project_root)))
            if content and ("async def" in content or "await " in content):
                async_files.append(str(py_file.relative_to(self.project_root)))
        
        if async_files:
            self._add_check_result(
                "async_implementation",
                "PASS",
                f"Found async implementation in {len(async_files)} files"
            )
        else:
            self._add_check_result(
                "async_implementation",
                "WARN",
                "No async implementation found"
            )
    
    def _validate_monitoring_implementation(self):
        """Validate monitoring implementation."""
        monitoring_files = [
            "src/streamline_vpn/monitoring/metrics_collector.py",
            "src/streamline_vpn/monitoring/alerting.py"
        ]
        
        monitoring_found = False
        for monitoring_file in monitoring_files:
            if self._check_file_exists(monitoring_file, f"Monitoring module: {monitoring_file}"):
                monitoring_found = True
                self._validate_monitoring_module(monitoring_file)
        
        if monitoring_found:
            self._add_check_result(
                "monitoring_implementation",
                "PASS",
                "Monitoring modules found"
            )
        else:
            self._add_check_result(
                "monitoring_implementation",
                "WARN",
                "No monitoring modules found"
            )
    
    def _validate_cache_module(self, cache_file: str):
        """Validate cache module content."""
        content = self._read_file_content(cache_file)
        if not content:
            return
        
        # Check for cache-specific patterns
        has_cache_methods = any(keyword in content.lower() for keyword in [
            "get", "set", "delete", "clear", "cache"
        ])
        
        has_expiration = any(keyword in content.lower() for keyword in [
            "expire", "ttl", "timeout", "lifetime"
        ])
        
        if has_cache_methods:
            self._add_check_result(
                f"cache_methods_{cache_file.replace('/', '_')}",
                "PASS",
                f"Cache module {cache_file} has cache methods"
            )
        else:
            self._add_check_result(
                f"cache_methods_{cache_file.replace('/', '_')}",
                "WARN",
                f"Cache module {cache_file} may be missing cache methods"
            )
        
        if has_expiration:
            self._add_check_result(
                f"cache_expiration_{cache_file.replace('/', '_')}",
                "PASS",
                f"Cache module {cache_file} has expiration logic"
            )
    
    def _validate_monitoring_module(self, monitoring_file: str):
        """Validate monitoring module content."""
        content = self._read_file_content(monitoring_file)
        if not content:
            return
        
        # Check for monitoring patterns
        has_metrics = any(keyword in content.lower() for keyword in [
            "metric", "counter", "gauge", "histogram", "timer"
        ])
        
        has_alerting = any(keyword in content.lower() for keyword in [
            "alert", "threshold", "warning", "error", "critical"
        ])
        
        if has_metrics:
            self._add_check_result(
                f"monitoring_metrics_{monitoring_file.replace('/', '_')}",
                "PASS",
                f"Monitoring module {monitoring_file} has metrics"
            )
        
        if has_alerting:
            self._add_check_result(
                f"monitoring_alerting_{monitoring_file.replace('/', '_')}",
                "PASS",
                f"Monitoring module {monitoring_file} has alerting"
            )

