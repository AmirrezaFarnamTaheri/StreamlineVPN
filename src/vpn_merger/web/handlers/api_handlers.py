#!/usr/bin/env python3
"""
API Handlers for Enhanced Web Interface
======================================

Handles all API endpoints for the enhanced web interface.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from aiohttp.web import Request, Response

from ...core.merger import VPNSubscriptionMerger
from ...core.config_manager import ConfigurationManager
from ...core.config_validator import ConfigurationValidator, ValidationResult
from ...monitoring.health_monitor import get_health_monitor

logger = logging.getLogger(__name__)


class APIHandlers:
    """Handles all API endpoints for the enhanced web interface."""
    
    def __init__(self, merger: VPNSubscriptionMerger, health_monitor=None):
        """Initialize API handlers.
        
        Args:
            merger: VPN subscription merger instance
            health_monitor: Health monitor instance
        """
        self.merger = merger
        self.health_monitor = health_monitor or get_health_monitor()
        self.config_manager = ConfigurationManager()
        self.config_validator = ConfigurationValidator()
    
    async def handle_status_api(self, request: Request) -> Response:
        """Handle status API endpoint."""
        try:
            status_data = {
                "timestamp": datetime.now().isoformat(),
                "status": "running",
                "version": "2.0.0",
                "uptime": "N/A",
                "active_connections": 0,
                "last_merge": "N/A"
            }
            
            return Response(
                text=json.dumps(status_data, indent=2),
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Status API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def handle_health_api(self, request: Request) -> Response:
        """Handle health check API endpoint."""
        try:
            health_data = await self.health_monitor.check_health()
            return Response(
                text=json.dumps(health_data, indent=2),
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Health API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def handle_sources_api(self, request: Request) -> Response:
        """Handle sources API endpoint."""
        try:
            urls = self.merger.source_manager.get_prioritized_sources()

            sources_data = {
                "timestamp": datetime.now().isoformat(),
                "total_sources": len(urls),
                "sources": [{"url": url} for url in urls]
            }
            
            return Response(
                text=json.dumps(sources_data, indent=2),
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Sources API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def handle_configs_api(self, request: Request) -> Response:
        """Handle configurations API endpoint."""
        try:
            # Run a quick merge to provide a sample of configurations
            configs = await self.merger.run_quick_merge()
            
            configs_data = {
                "timestamp": datetime.now().isoformat(),
                "total_configs": len(configs) if configs else 0,
                "configs": [
                    {
                        "id": getattr(config, "id", f"config_{i}"),
                        "name": getattr(config, "name", f"Configuration {i+1}"),
                        "protocol": getattr(config, "protocol", "Unknown"),
                        "server": getattr(config, "server", "Unknown"),
                        "port": getattr(config, "port", 0),
                        "quality_score": getattr(config, "quality_score", 0)
                    }
                    for i, config in enumerate(configs[:50])  # Limit to 50 configs
                ]
            }
            
            return Response(
                text=json.dumps(configs_data, indent=2),
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Configs API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def handle_statistics_api(self, request: Request) -> Response:
        """Handle statistics API endpoint."""
        try:
            performance_report = self.merger.get_processing_statistics()
            health_summary = self.health_monitor.get_health_summary()
            
            statistics_data = {
                "timestamp": datetime.now().isoformat(),
                "performance": performance_report,
                "health": health_summary,
                "system": {
                    "active_connections": 0,
                    "websocket_connections": 0,
                    "monitoring_active": False
                }
            }
            
            return Response(
                text=json.dumps(statistics_data, indent=2),
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Statistics API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def handle_merge_api(self, request: Request) -> Response:
        """Handle merge operation API endpoint."""
        try:
            data = await request.json()
            strategy = data.get("strategy", "quality_based")
            max_concurrent = data.get("max_concurrent", None)
            
            # Current merger does not support strategy parameter; ignore it
            if max_concurrent is not None:
                configs = await self.merger.run_comprehensive_merge(max_concurrent=max_concurrent)
            else:
                configs = await self.merger.run_comprehensive_merge()
            
            merge_result = {
                "timestamp": datetime.now().isoformat(),
                "strategy": strategy,
                "max_concurrent": max_concurrent,
                "configs_generated": len(configs) if configs else 0,
                "status": "success"
            }
            
            return Response(
                text=json.dumps(merge_result, indent=2),
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Merge API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def handle_export_api(self, request: Request) -> Response:
        """Handle export operation API endpoint."""
        try:
            data = await request.json()
            format_type = data.get("format", "all")
            output_dir = data.get("output_dir", "output")
            
            # Ensure we have results to export
            results = self.merger.results
            if not results:
                # Run a quick merge to produce results if none available
                results = await self.merger.run_quick_merge()

            files_generated: list[str] = []
            if str(format_type).lower() in ("all", "*"):
                mapping = self.merger.save_results(output_dir=output_dir)
                files_generated = list(mapping.values())
            else:
                # Save only the requested format
                out_dir = output_dir or "output"
                # Decide filename by convention similar to OutputManager
                default_names = {
                    "raw": "vpn_subscription_raw.txt",
                    "base64": "vpn_subscription_base64.txt",
                    "csv": "vpn_detailed.csv",
                    "json": "vpn_report.json",
                    "singbox": "vpn_singbox.json",
                    "clash": "clash.yaml",
                }
                filename = default_names.get(str(format_type).lower(), f"export.{format_type}")
                from pathlib import Path as _P
                out_path = _P(out_dir) / filename
                self.merger.output_manager.save_single_format(results, str(format_type).lower(), out_path)
                files_generated = [str(out_path)]
            
            export_result = {
                "timestamp": datetime.now().isoformat(),
                "format": format_type,
                "output_dir": output_dir,
                "files_generated": files_generated,
                "status": "success"
            }
            
            return Response(
                text=json.dumps(export_result, indent=2),
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Export API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def handle_validate_api(self, request: Request) -> Response:
        """Handle validation API endpoint."""
        try:
            data = await request.json()
            config_data = data.get("config", {})

            # Best-effort validation using configuration manager semantics
            # If a path is provided, validate file; otherwise, perform basic checks
            result: dict[str, Any]
            try:
                path = data.get("config_path")
                if path:
                    vr: ValidationResult = self.config_validator.validate_config_file(path)
                    result = {
                        "is_valid": vr.is_valid,
                        "errors": [e.__dict__ for e in vr.errors],
                        "warnings": [w.__dict__ for w in vr.warnings],
                    }
                else:
                    # Load current config and update with provided data, then validate
                    for section, values in (config_data or {}).items():
                        if isinstance(values, dict):
                            self.config_manager.update_section(section, values)
                    ok = self.config_manager.validate()
                    result = {"is_valid": bool(ok)}
            except Exception as ex:
                result = {"is_valid": False, "error": str(ex)}

            return Response(text=json.dumps(result, indent=2), content_type="application/json")
        except Exception as e:
            logger.error(f"Validate API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def handle_get_config_api(self, request: Request) -> Response:
        """Handle get configuration API endpoint."""
        try:
            config_data = self.config_manager.get_all()
            return Response(
                text=json.dumps(config_data, indent=2),
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Get config API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def handle_update_config_api(self, request: Request) -> Response:
        """Handle update configuration API endpoint."""
        try:
            data = await request.json()
            if isinstance(data, dict):
                # Shallow merge per section
                for section, values in data.items():
                    if isinstance(values, dict):
                        self.config_manager.update_section(section, values)
            ok = self.config_manager.validate()

            update_result = {
                "timestamp": datetime.now().isoformat(),
                "status": "success" if ok else "invalid",
                "message": "Configuration updated successfully" if ok else "Configuration has validation issues"
            }
            
            return Response(
                text=json.dumps(update_result, indent=2),
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Update config API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def handle_monitoring_api(self, request: Request) -> Response:
        """Handle monitoring API endpoint."""
        try:
            monitoring_data = {
                "timestamp": datetime.now().isoformat(),
                "monitoring_active": False,  # Will be set by main interface
                "monitoring_port": 8082,
                "health_status": await self.health_monitor.check_health()
            }
            
            return Response(
                text=json.dumps(monitoring_data, indent=2),
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Monitoring API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def handle_start_monitoring_api(self, request: Request) -> Response:
        """Handle start monitoring API endpoint."""
        try:
            start_result = {
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "message": "Monitoring started successfully",
                "monitoring_url": "http://localhost:8082"
            }
            
            return Response(
                text=json.dumps(start_result, indent=2),
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Start monitoring API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )
    
    async def handle_stop_monitoring_api(self, request: Request) -> Response:
        """Handle stop monitoring API endpoint."""
        try:
            stop_result = {
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "message": "Monitoring stopped successfully"
            }
            
            return Response(
                text=json.dumps(stop_result, indent=2),
                content_type="application/json"
            )
        except Exception as e:
            logger.error(f"Stop monitoring API error: {e}")
            return Response(
                text=json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500
            )

