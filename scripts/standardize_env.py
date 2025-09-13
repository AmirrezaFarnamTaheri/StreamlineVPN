#!/usr/bin/env python3
"""
Environment Variable Standardization Script
==========================================

Standardizes and validates environment variables across StreamlineVPN.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any


class EnvironmentStandardizer:
    """Standardizes environment variables across the project."""

    # Standard environment variable mappings
    STANDARD_VARS = {
        # API Server Configuration
        "API_HOST": {"default": "0.0.0.0", "type": "string", "description": "API server host"},
        "API_PORT": {"default": "8080", "type": "int", "description": "API server port"},
        "API_BASE_URL": {"default": None, "type": "string", "description": "API base URL for frontend"},

        # Web Server Configuration
        "WEB_HOST": {"default": "0.0.0.0", "type": "string", "description": "Web server host"},
        "WEB_PORT": {"default": "8000", "type": "int", "description": "Web server port"},
        "WEB_CONNECT_SRC_EXTRA": {"default": "", "type": "string", "description": "Extra CSP connect-src origins"},

        # StreamlineVPN Configuration
        "STREAMLINE_ENV": {"default": "development", "type": "string", "description": "Environment mode"},
        "STREAMLINE_LOG_LEVEL": {"default": "INFO", "type": "string", "description": "Logging level"},
        "STREAMLINE_LOG_FILE": {"default": None, "type": "string", "description": "Log file path"},
        "STREAMLINE_CONFIG_PATH": {"default": "config/sources.yaml", "type": "string", "description": "Sources config path"},
        "STREAMLINE_OUTPUT_DIR": {"default": "output", "type": "string", "description": "Output directory"},

        # Database Configuration
        "STREAMLINE_DB_URL": {"default": None, "type": "string", "description": "Database URL"},
        "STREAMLINE_REDIS_URL": {"default": None, "type": "string", "description": "Redis URL"},
        "STREAMLINE_REDIS_NODES": {"default": "[]", "type": "json", "description": "Redis cluster nodes"},

        # Security Configuration
        "STREAMLINE_SECRET_KEY": {"default": None, "type": "string", "description": "Secret key for encryption"},
        "STREAMLINE_API_KEY": {"default": None, "type": "string", "description": "API authentication key"},
        "STREAMLINE_JWT_SECRET": {"default": None, "type": "string", "description": "JWT signing secret"},

        # Performance Configuration
        "STREAMLINE_MAX_CONCURRENT": {"default": "50", "type": "int", "description": "Max concurrent requests"},
        "STREAMLINE_TIMEOUT": {"default": "30", "type": "int", "description": "Request timeout seconds"},
        "STREAMLINE_BATCH_SIZE": {"default": "10", "type": "int", "description": "Processing batch size"},

        # Cache Configuration
        "STREAMLINE_CACHE_ENABLED": {"default": "true", "type": "bool", "description": "Enable caching"},
        "STREAMLINE_CACHE_TTL": {"default": "3600", "type": "int", "description": "Cache TTL seconds"},

        # CORS Configuration
        "ALLOWED_ORIGINS": {"default": '["*"]', "type": "json", "description": "CORS allowed origins"},
        "ALLOWED_METHODS": {"default": '["GET","POST","PUT","DELETE","OPTIONS"]', "type": "json", "description": "CORS allowed methods"},
        "ALLOWED_HEADERS": {"default": '["Content-Type","Authorization"]', "type": "json", "description": "CORS allowed headers"},
        "ALLOW_CREDENTIALS": {"default": "false", "type": "bool", "description": "CORS allow credentials"},

        # Jobs Configuration
        "JOBS_DIR": {"default": "data", "type": "string", "description": "Jobs data directory"},
        "JOBS_FILE": {"default": "data/jobs.json", "type": "string", "description": "Jobs storage file"},

        # Docker Configuration
        "WORKERS": {"default": "1", "type": "int", "description": "Number of worker processes"},
        "HOST": {"default": "0.0.0.0", "type": "string", "description": "Generic host binding"},
    }

    # Legacy variable mappings for migration
    LEGACY_MAPPINGS = {
        "VPN_MERGER_HOST": "API_HOST",
        "VPN_MERGER_PORT": "API_PORT",
        "VPN_MERGER_DEBUG": "STREAMLINE_ENV",  # Convert to development/production
        "VPN_MERGER_LOG_LEVEL": "STREAMLINE_LOG_LEVEL",
        "VPN_MERGER_ENVIRONMENT": "STREAMLINE_ENV",
        "VPN_LOG_LEVEL": "STREAMLINE_LOG_LEVEL",
        "VPN_LOG_FILE": "STREAMLINE_LOG_FILE",
        "VPN_TIMEOUT": "STREAMLINE_TIMEOUT",
        "VPN_CONCURRENT_LIMIT": "STREAMLINE_MAX_CONCURRENT",
        "VPN_CHUNK_SIZE": "STREAMLINE_BATCH_SIZE",
        "REDIS_URL": "STREAMLINE_REDIS_URL",
        "DATABASE_URL": "STREAMLINE_DB_URL",
        "SECRET_KEY": "STREAMLINE_SECRET_KEY",
        "API_KEY": "STREAMLINE_API_KEY",
        "JWT_SECRET": "STREAMLINE_JWT_SECRET",
        "MAX_CONCURRENT_REQUESTS": "STREAMLINE_MAX_CONCURRENT",
        "REQUEST_TIMEOUT": "STREAMLINE_TIMEOUT",
        "BATCH_SIZE": "STREAMLINE_BATCH_SIZE",
        "CACHE_TTL": "STREAMLINE_CACHE_TTL",
    }

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)

    def validate_environment(self) -> Dict[str, Any]:
        """Validate current environment variables."""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "current_values": {},
            "missing_required": [],
            "legacy_detected": []
        }

        # Check for legacy variables
        for legacy_var, new_var in self.LEGACY_MAPPINGS.items():
            if os.getenv(legacy_var):
                validation_results["legacy_detected"].append({
                    "legacy": legacy_var,
                    "new": new_var,
                    "value": os.getenv(legacy_var)
                })
                validation_results["warnings"].append(
                    f"Legacy variable {legacy_var} detected, should use {new_var}"
                )

        # Validate standard variables
        for var_name, config in self.STANDARD_VARS.items():
            current_value = os.getenv(var_name)
            validation_results["current_values"][var_name] = current_value

            # Check required variables (those without defaults)
            if config["default"] is None and not current_value:
                if var_name in ["STREAMLINE_SECRET_KEY", "STREAMLINE_API_KEY"]:
                    validation_results["missing_required"].append(var_name)
                    validation_results["errors"].append(
                        f"Required variable {var_name} is not set"
                    )

            # Validate types
            if current_value:
                try:
                    self._validate_type(var_name, current_value, config["type"])
                except ValueError as e:
                    validation_results["errors"].append(str(e))
                    validation_results["valid"] = False

        # Environment-specific validations
        env = os.getenv("STREAMLINE_ENV", "development")
        if env == "production":
            production_required = [
                "STREAMLINE_SECRET_KEY",
                "STREAMLINE_API_KEY",
                "STREAMLINE_REDIS_URL",
            ]
            for var in production_required:
                if not os.getenv(var):
                    validation_results["errors"].append(
                        f"Production environment requires {var}"
                    )
                    validation_results["valid"] = False

        # Port conflict checks
        api_port = int(os.getenv("API_PORT", 8080))
        web_port = int(os.getenv("WEB_PORT", 8000))
        if api_port == web_port:
            validation_results["errors"].append(
                f"API_PORT and WEB_PORT cannot be the same ({api_port})"
            )
            validation_results["valid"] = False

        return validation_results

    def _validate_type(self, var_name: str, value: str, expected_type: str) -> None:
        """Validate environment variable type."""
        try:
            if expected_type == "int":
                int_val = int(value)
                if var_name.endswith("_PORT") and not (1 <= int_val <= 65535):
                    raise ValueError(f"{var_name} must be between 1 and 65535")
                elif var_name == "STREAMLINE_TIMEOUT" and int_val < 1:
                    raise ValueError(f"{var_name} must be positive")
                elif var_name == "STREAMLINE_MAX_CONCURRENT" and not (1 <= int_val <= 1000):
                    raise ValueError(f"{var_name} must be between 1 and 1000")
            elif expected_type == "bool":
                if value.lower() not in ["true", "false", "1", "0", "yes", "no"]:
                    raise ValueError(f"{var_name} must be a boolean value")
            elif expected_type == "json":
                json.loads(value)
            # string type needs no validation
        except (ValueError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid {expected_type} value for {var_name}: {value}")

    def migrate_legacy_variables(self, dry_run: bool = False) -> Dict[str, Any]:
        """Migrate legacy environment variables to new format."""
        migration_results = {
            "migrated": [],
            "conflicts": [],
            "suggestions": []
        }

        for legacy_var, new_var in self.LEGACY_MAPPINGS.items():
            legacy_value = os.getenv(legacy_var)
            new_value = os.getenv(new_var)

            if legacy_value:
                if new_value and new_value != legacy_value:
                    migration_results["conflicts"].append({
                        "legacy": legacy_var,
                        "new": new_var,
                        "legacy_value": legacy_value,
                        "new_value": new_value,
                    })
                else:
                    # Special case conversions
                    converted_value = self._convert_legacy_value(legacy_var, legacy_value)

                    migration_results["migrated"].append({
                        "legacy": legacy_var,
                        "new": new_var,
                        "value": converted_value,
                    })

                    if not dry_run:
                        os.environ[new_var] = converted_value
                        # Don't remove legacy var to avoid breaking existing scripts
                        # del os.environ[legacy_var]

        return migration_results

    def _convert_legacy_value(self, legacy_var: str, value: str) -> str:
        """Convert legacy variable values to new format."""
        if legacy_var == "VPN_MERGER_DEBUG":
            return "development" if value.lower() in ["true", "1", "yes"] else "production"
        return value

    def generate_env_template(self, include_comments: bool = True) -> str:
        """Generate .env template file."""
        lines = []

        if include_comments:
            lines.append("# StreamlineVPN Environment Configuration")
            lines.append("# Generated by Environment Standardizer")
            lines.append("")

        # Group variables by category
        categories = {
            "API Server": ["API_HOST", "API_PORT", "API_BASE_URL"],
            "Web Server": ["WEB_HOST", "WEB_PORT", "WEB_CONNECT_SRC_EXTRA"],
            "Core": ["STREAMLINE_ENV", "STREAMLINE_LOG_LEVEL", "STREAMLINE_LOG_FILE",
                     "STREAMLINE_CONFIG_PATH", "STREAMLINE_OUTPUT_DIR"],
            "Database": ["STREAMLINE_DB_URL", "STREAMLINE_REDIS_URL", "STREAMLINE_REDIS_NODES"],
            "Security": ["STREAMLINE_SECRET_KEY", "STREAMLINE_API_KEY", "STREAMLINE_JWT_SECRET"],
            "Performance": ["STREAMLINE_MAX_CONCURRENT", "STREAMLINE_TIMEOUT", "STREAMLINE_BATCH_SIZE"],
            "Cache": ["STREAMLINE_CACHE_ENABLED", "STREAMLINE_CACHE_TTL"],
            "CORS": ["ALLOWED_ORIGINS", "ALLOWED_METHODS", "ALLOWED_HEADERS", "ALLOW_CREDENTIALS"],
            "Jobs": ["JOBS_DIR", "JOBS_FILE"],
            "Docker": ["WORKERS", "HOST"],
        }

        for category, vars_in_category in categories.items():
            if include_comments:
                lines.append(f"# {category} Configuration")
                lines.append("#" + "=" * (len(category) + 15))

            for var_name in vars_in_category:
                if var_name in self.STANDARD_VARS:
                    config = self.STANDARD_VARS[var_name]
                    if include_comments:
                        lines.append(f"# {config['description']}")
                        lines.append(f"# Type: {config['type']}")
                        if config['default']:
                            lines.append(f"# Default: {config['default']}")

                    current_value = os.getenv(var_name)
                    if current_value:
                        lines.append(f"{var_name}={current_value}")
                    elif config['default']:
                        lines.append(f"# {var_name}={config['default']}")
                    else:
                        lines.append(f"# {var_name}=")

                    if include_comments:
                        lines.append("")

            if include_comments:
                lines.append("")

        return "\n".join(lines)

    def create_env_file(self, filename: str = ".env", overwrite: bool = False) -> bool:
        """Create .env file with current configuration."""
        env_path = self.project_root / filename

        if env_path.exists() and not overwrite:
            print(f"File {filename} already exists. Use --overwrite to replace it.")
            return False

        template = self.generate_env_template()

        with open(env_path, "w") as f:
            f.write(template)

        print(f"Environment template created: {filename}")
        return True

    def validate_config_files(self) -> Dict[str, Any]:
        """Validate configuration files referenced by environment variables."""
        results = {"valid": True, "errors": [], "warnings": []}

        # Check config path
        config_path = Path(os.getenv("STREAMLINE_CONFIG_PATH", "config/sources.yaml"))
        if not config_path.exists():
            results["warnings"].append(f"Config file not found: {config_path}")

        # Check output directory
        output_dir = Path(os.getenv("STREAMLINE_OUTPUT_DIR", "output"))
        if not output_dir.exists():
            results["warnings"].append(f"Output directory will be created: {output_dir}")

        # Check jobs directory
        jobs_dir = Path(os.getenv("JOBS_DIR", "data"))
        if not jobs_dir.exists():
            results["warnings"].append(f"Jobs directory will be created: {jobs_dir}")

        # Check log file directory
        log_file = os.getenv("STREAMLINE_LOG_FILE")
        if log_file:
            log_path = Path(log_file)
            if not log_path.parent.exists():
                results["warnings"].append(f"Log directory will be created: {log_path.parent}")

        return results


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Standardize StreamlineVPN environment variables")
    parser.add_argument("--validate", action="store_true", help="Validate current environment")
    parser.add_argument("--migrate", action="store_true", help="Migrate legacy variables")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    parser.add_argument("--create-env", metavar="FILENAME", help="Create .env template file")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing .env file")
    parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()

    standardizer = EnvironmentStandardizer(args.project_root)

    if args.validate or (not args.migrate and not args.create_env):
        # Default to validation
        print("Validating environment variables...")
        results = standardizer.validate_environment()

        print(f"\nValidation Results: {'✓ PASSED' if results['valid'] else '✗ FAILED'}")

        if results['errors']:
            print(f"\nErrors ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"  ✗ {error}")

        if results['warnings']:
            print(f"\nWarnings ({len(results['warnings'])}):")
            for warning in results['warnings']:
                print(f"  ⚠ {warning}")

        if results['legacy_detected']:
            print(f"\nLegacy Variables Detected ({len(results['legacy_detected'])}):")
            for legacy in results['legacy_detected']:
                print(f"  • {legacy['legacy']} → {legacy['new']} (current: {legacy['value']})")

        if results['missing_required']:
            print(f"\nMissing Required Variables:")
            for var in results['missing_required']:
                print(f"  • {var}")

    if args.migrate:
        print("Migrating legacy environment variables...")
        results = standardizer.migrate_legacy_variables(dry_run=args.dry_run)

        if results['migrated']:
            print(f"\n{'Would migrate' if args.dry_run else 'Migrated'} ({len(results['migrated'])}):")
            for migration in results['migrated']:
                print(f"  • {migration['legacy']} → {migration['new']} = {migration['value']}")

        if results['conflicts']:
            print(f"\nConflicts found ({len(results['conflicts'])}):")
            for conflict in results['conflicts']:
                print(f"  • {conflict['legacy']} ({conflict['legacy_value']}) vs {conflict['new']} ({conflict['new_value']})")

    if args.create_env:
        standardizer.create_env_file(args.create_env, args.overwrite)


if __name__ == "__main__":
    main()

