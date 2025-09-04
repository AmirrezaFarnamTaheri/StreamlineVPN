#!/usr/bin/env python3
"""
Configuration Migration Utility
===============================

Migrates basic configuration to enhanced configuration format with
comprehensive validation and error handling.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install PyYAML")
    sys.exit(1)

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vpn_merger.core import validate_config_file, ValidationResult

logger = logging.getLogger(__name__)

# Default enhanced configuration template
ENHANCED_CONFIG_TEMPLATE = {
    "metadata": {
        "version": "3.0.0",
        "description": "Enhanced VPN subscription sources configuration",
        "last_updated": "2024-12-29",
        "maintainer": "vpn-merger-team",
        "total_sources": 0,
        "categories": 0,
        "update_frequency": "hourly",
        "schema_version": "3.0"
    },
    "sources": {},
    "settings": {
        "processing": {
            "concurrent_limit": 100,
            "timeout": 30,
            "batch_size": 20,
            "max_retries": 3,
            "retry_policy": {
                "max_retries": 3,
                "backoff_factor": 2,
                "backoff_max": 60,
                "retry_on_errors": ["timeout", "connection_error", "server_error"]
            },
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 60,
                "burst_limit": 10,
                "per_host_limit": 20
            },
            "memory_management": {
                "max_memory_usage": "2GB",
                "cleanup_interval": 300,
                "garbage_collection_threshold": 0.8
            },
            "caching": {
                "enabled": True,
                "cache_size": 1000,
                "cache_ttl": 3600,
                "cache_backend": "memory"
            },
            "deduplication": {
                "enabled": True,
                "method": "bloom_filter",
                "bloom_filter_size": 1000000,
                "hash_set_max_size": 100000
            }
        },
        "quality": {
            "min_score": 0.5,
            "scoring_weights": {
                "historical_reliability": 0.25,
                "ssl_certificate": 0.15,
                "response_time": 0.15,
                "content_quality": 0.20,
                "protocol_diversity": 0.15,
                "uptime_consistency": 0.10
            },
            "deduplication": True,
            "protocol_validation": "strict",
            "content_validation": {
                "enabled": True,
                "min_length": 10,
                "max_length": 10000,
                "allowed_chars": "a-zA-Z0-9:/?=&._-",
                "suspicious_patterns": [
                    ".*\\.xyz$",
                    ".*\\.tk$",
                    ".*\\.ml$"
                ]
            },
            "source_filtering": {
                "enabled": True,
                "min_configs": 10,
                "max_response_time": 30,
                "required_protocols": ["vmess"],
                "blocked_domains": [
                    "malicious.com",
                    "spam.com",
                    "fake-vpn.com"
                ]
            },
            "quality_thresholds": {
                "excellent": 0.8,
                "good": 0.6,
                "fair": 0.4,
                "poor": 0.0
            }
        },
        "monitoring": {
            "metrics_enabled": True,
            "health_check_interval": 60,
            "metrics_collection_interval": 30,
            "alert_thresholds": {
                "error_rate": 0.1,
                "response_time": 10,
                "memory_usage": 0.8,
                "disk_usage": 0.9,
                "cpu_usage": 0.8
            },
            "alert_channels": [
                {
                    "type": "webhook",
                    "url": "${ALERT_WEBHOOK}",
                    "enabled": True,
                    "severity": ["critical", "warning"]
                },
                {
                    "type": "email",
                    "recipients": ["${ALERT_EMAIL}"],
                    "enabled": True,
                    "severity": ["critical"]
                },
                {
                    "type": "slack",
                    "channel": "${SLACK_CHANNEL}",
                    "enabled": True,
                    "severity": ["critical", "warning", "info"]
                }
            ],
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "handlers": ["console", "file", "syslog"],
                "file_rotation": {
                    "enabled": True,
                    "max_size": "100MB",
                    "backup_count": 5
                }
            },
            "performance_monitoring": {
                "enabled": True,
                "cpu_monitoring": True,
                "memory_monitoring": True,
                "disk_monitoring": True,
                "network_monitoring": True,
                "custom_metrics": [
                    "sources_processed_per_second",
                    "configs_generated_per_minute",
                    "average_response_time",
                    "error_rate_by_source"
                ]
            }
        },
        "security": {
            "ssl_validation": {
                "enabled": True,
                "verify_certificates": True,
                "check_hostname": True,
                "allowed_ciphers": [
                    "TLS_AES_256_GCM_SHA384",
                    "TLS_CHACHA20_POLY1305_SHA256"
                ]
            },
            "content_security": {
                "enabled": True,
                "max_content_size": "10MB",
                "allowed_content_types": [
                    "text/plain",
                    "application/json",
                    "application/x-yaml"
                ],
                "scan_for_malware": False,
                "content_sandboxing": False
            },
            "access_control": {
                "enabled": False,
                "allowed_ips": [],
                "blocked_ips": [],
                "rate_limiting_per_ip": 100
            },
            "threat_detection": {
                "enabled": True,
                "suspicious_domains": True,
                "content_analysis": True,
                "behavioral_analysis": False
            }
        },
        "output": {
            "directory": "output",
            "formats": {
                "raw": True,
                "base64": True,
                "csv": True,
                "json": True,
                "yaml": True,
                "clash": True,
                "singbox": True
            },
            "compression": {
                "enabled": True,
                "algorithm": "gzip",
                "level": 6
            },
            "file_management": {
                "max_files": 100,
                "cleanup_old_files": True,
                "retention_days": 30,
                "backup_enabled": True,
                "backup_interval": "daily"
            },
            "quality_control": {
                "validate_output": True,
                "min_configs_per_file": 1,
                "max_configs_per_file": 100000,
                "deduplicate_output": True
            }
        }
    }
}

# Tier configuration mapping
TIER_CONFIG_MAPPING = {
    "tier_1_premium": {
        "description": "High-quality, reliable sources with premium performance",
        "reliability_score": 0.95,
        "priority": 1,
        "update_frequency": "hourly"
    },
    "tier_2_reliable": {
        "description": "Good quality sources with occasional issues",
        "reliability_score": 0.8,
        "priority": 2,
        "update_frequency": "daily"
    },
    "tier_3_bulk": {
        "description": "Large volume sources for comprehensive coverage",
        "reliability_score": 0.6,
        "priority": 3,
        "update_frequency": "daily"
    },
    "specialized": {
        "description": "Protocol-specific or niche sources",
        "reliability_score": 0.7,
        "priority": 2,
        "update_frequency": "daily"
    },
    "regional": {
        "description": "Geographic-specific sources",
        "reliability_score": 0.7,
        "priority": 2,
        "update_frequency": "daily"
    },
    "experimental": {
        "description": "New and experimental sources for testing",
        "reliability_score": 0.4,
        "priority": 4,
        "update_frequency": "daily"
    }
}


class ConfigurationMigrator:
    """Configuration migration utility."""
    
    def __init__(self, verbose: bool = False):
        """Initialize the migrator.
        
        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.setup_logging()
        
    def setup_logging(self) -> None:
        """Setup logging configuration."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
    def load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration data
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        logger.info(f"Loading configuration from {config_path}")
        
        with open(config_path, encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
            
        if config_data is None:
            raise ValueError("Configuration file is empty or invalid")
            
        logger.info("Configuration loaded successfully")
        return config_data
        
    def migrate_sources(self, old_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate sources from old format to enhanced format.
        
        Args:
            old_sources: Old sources configuration
            
        Returns:
            Enhanced sources configuration
        """
        logger.info("Migrating sources configuration")
        
        enhanced_sources = {}
        total_sources = 0
        
        for tier_name, tier_data in old_sources.items():
            if isinstance(tier_data, list):
                # Old format: list of URLs
                urls = tier_data
                tier_config = TIER_CONFIG_MAPPING.get(tier_name, {
                    "description": f"Migrated {tier_name} sources",
                    "reliability_score": 0.7,
                    "priority": 2,
                    "update_frequency": "daily"
                })
                
                enhanced_sources[tier_name] = {
                    "description": tier_config["description"],
                    "reliability_score": tier_config["reliability_score"],
                    "priority": tier_config["priority"],
                    "update_frequency": tier_config["update_frequency"],
                    "urls": []
                }
                
                for url in urls:
                    if isinstance(url, str):
                        enhanced_sources[tier_name]["urls"].append({
                            "url": url,
                            "weight": 1.0,
                            "protocols": ["vmess", "vless", "trojan", "shadowsocks"],
                            "expected_configs": 100,
                            "format": "raw",
                            "region": "global",
                            "maintainer": "unknown",
                            "source_type": "migrated",
                            "validation": {
                                "min_configs": 10,
                                "max_response_time": 30,
                                "required_protocols": ["vmess"],
                                "ssl_required": False,
                                "content_validation": "basic"
                            },
                            "monitoring": {
                                "health_check_interval": 3600,
                                "failure_threshold": 5,
                                "alert_on_downtime": False
                            }
                        })
                        total_sources += 1
                        
            elif isinstance(tier_data, dict):
                # Already in enhanced format
                enhanced_sources[tier_name] = tier_data
                if "urls" in tier_data and isinstance(tier_data["urls"], list):
                    total_sources += len(tier_data["urls"])
                    
        logger.info(f"Migrated {total_sources} sources across {len(enhanced_sources)} tiers")
        return enhanced_sources
        
    def create_enhanced_config(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced configuration from old configuration.
        
        Args:
            old_config: Old configuration data
            
        Returns:
            Enhanced configuration data
        """
        logger.info("Creating enhanced configuration")
        
        # Start with template
        enhanced_config = ENHANCED_CONFIG_TEMPLATE.copy()
        
        # Update metadata
        if "metadata" in old_config:
            enhanced_config["metadata"].update(old_config["metadata"])
            
        # Migrate sources
        if "sources" in old_config:
            enhanced_config["sources"] = self.migrate_sources(old_config["sources"])
            
        # Update metadata with source counts
        total_sources = sum(
            len(tier.get("urls", [])) for tier in enhanced_config["sources"].values()
        )
        enhanced_config["metadata"]["total_sources"] = total_sources
        enhanced_config["metadata"]["categories"] = len(enhanced_config["sources"])
        
        # Merge settings if present
        if "settings" in old_config:
            self.merge_settings(enhanced_config["settings"], old_config["settings"])
            
        logger.info("Enhanced configuration created successfully")
        return enhanced_config
        
    def merge_settings(self, enhanced_settings: Dict[str, Any], old_settings: Dict[str, Any]) -> None:
        """Merge old settings into enhanced settings.
        
        Args:
            enhanced_settings: Enhanced settings configuration
            old_settings: Old settings configuration
        """
        logger.info("Merging settings configuration")
        
        # Merge processing settings
        if "processing" in old_settings:
            processing = old_settings["processing"]
            if "concurrent_limit" in processing:
                enhanced_settings["processing"]["concurrent_limit"] = processing["concurrent_limit"]
            if "timeout" in processing:
                enhanced_settings["processing"]["timeout"] = processing["timeout"]
            if "max_retries" in processing:
                enhanced_settings["processing"]["max_retries"] = processing["max_retries"]
                
        # Merge quality settings
        if "quality" in old_settings:
            quality = old_settings["quality"]
            if "min_score" in quality:
                enhanced_settings["quality"]["min_score"] = quality["min_score"]
            if "deduplication" in quality:
                enhanced_settings["quality"]["deduplication"] = quality["deduplication"]
                
        # Merge monitoring settings
        if "monitoring" in old_settings:
            monitoring = old_settings["monitoring"]
            if "metrics_enabled" in monitoring:
                enhanced_settings["monitoring"]["metrics_enabled"] = monitoring["metrics_enabled"]
            if "health_check_interval" in monitoring:
                enhanced_settings["monitoring"]["health_check_interval"] = monitoring["health_check_interval"]
                
        logger.info("Settings merged successfully")
        
    def save_config(self, config_data: Dict[str, Any], output_path: Path) -> None:
        """Save configuration to file.
        
        Args:
            config_data: Configuration data
            output_path: Output file path
        """
        logger.info(f"Saving enhanced configuration to {output_path}")
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2, sort_keys=False)
            
        logger.info("Configuration saved successfully")
        
    def validate_enhanced_config(self, config_path: Path) -> ValidationResult:
        """Validate enhanced configuration.
        
        Args:
            config_path: Path to enhanced configuration file
            
        Returns:
            Validation result
        """
        logger.info(f"Validating enhanced configuration: {config_path}")
        
        result = validate_config_file(config_path)
        
        if result.is_valid:
            logger.info("✅ Enhanced configuration is valid")
        else:
            logger.error("❌ Enhanced configuration has errors:")
            for error in result.errors:
                logger.error(f"  Error: {error.field} - {error.message}")
                
        if result.warnings:
            logger.warning("⚠️  Enhanced configuration has warnings:")
            for warning in result.warnings:
                logger.warning(f"  Warning: {warning.field} - {warning.message}")
                
        return result
        
    def migrate(self, input_path: Path, output_path: Path, validate: bool = True) -> bool:
        """Migrate configuration from old format to enhanced format.
        
        Args:
            input_path: Input configuration file path
            output_path: Output configuration file path
            validate: Whether to validate the enhanced configuration
            
        Returns:
            True if migration was successful
        """
        try:
            # Load old configuration
            old_config = self.load_config(input_path)
            
            # Create enhanced configuration
            enhanced_config = self.create_enhanced_config(old_config)
            
            # Save enhanced configuration
            self.save_config(enhanced_config, output_path)
            
            # Validate enhanced configuration
            if validate:
                result = self.validate_enhanced_config(output_path)
                if not result.is_valid:
                    logger.error("Enhanced configuration validation failed")
                    return False
                    
            logger.info("✅ Configuration migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration migration failed: {e}")
            return False


def main():
    """Main entry point for the migration utility."""
    parser = argparse.ArgumentParser(
        description="Migrate VPN Merger configuration to enhanced format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate basic configuration to enhanced format
  python migrate_config.py config/sources.unified.yaml config/sources.enhanced.yaml
  
  # Migrate without validation
  python migrate_config.py config/sources.unified.yaml config/sources.enhanced.yaml --no-validate
  
  # Verbose output
  python migrate_config.py config/sources.unified.yaml config/sources.enhanced.yaml --verbose
        """
    )
    
    parser.add_argument(
        "input",
        type=Path,
        help="Input configuration file path"
    )
    
    parser.add_argument(
        "output",
        type=Path,
        help="Output configuration file path"
    )
    
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation of enhanced configuration"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Create migrator
    migrator = ConfigurationMigrator(verbose=args.verbose)
    
    # Perform migration
    success = migrator.migrate(
        input_path=args.input,
        output_path=args.output,
        validate=not args.no_validate
    )
    
    if success:
        print(f"✅ Migration completed successfully")
        print(f"   Input:  {args.input}")
        print(f"   Output: {args.output}")
        sys.exit(0)
    else:
        print(f"❌ Migration failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
