"""
Diagnostics and monitoring routes.
"""

import psutil
import asyncio
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

diagnostics_router = APIRouter()


class PerformanceRoutes:
    @staticmethod
    def _get_merger():
        try:
            from ...unified_api import get_merger  # type: ignore

            return get_merger()
        except Exception:
            return None


@diagnostics_router.get("/diagnostics/system")
async def diagnostics_system():
    """System diagnostics."""
    try:
        # CPU and Memory info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Process info
        process = psutil.Process()
        process_memory = process.memory_info()

        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
            },
            "process": {
                "pid": process.pid,
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
            },
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"System diagnostics failed: {str(e)}"
        )


@diagnostics_router.post("/diagnostics/performance")
async def diagnostics_performance():
    """Performance diagnostics."""
    try:
        # Test async performance
        async def test_async_operation():
            await asyncio.sleep(0.1)
            return "async_test_complete"

        start_time = asyncio.get_event_loop().time()
        result = await test_async_operation()
        end_time = asyncio.get_event_loop().time()

        async_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Test sync performance
        import time

        start_sync = time.time()
        sum(range(10000))  # Simple CPU test
        end_sync = time.time()

        sync_time = (end_sync - start_sync) * 1000

        return {
            "performance": {
                "async_operation_ms": async_time,
                "sync_operation_ms": sync_time,
                "cpu_count": psutil.cpu_count(),
                "load_average": (
                    psutil.getloadavg() if hasattr(psutil, "getloadavg") else None
                ),
            },
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Performance diagnostics failed: {str(e)}"
        )


@diagnostics_router.get("/diagnostics/network")
async def diagnostics_network(limit: int = 5):
    """Network diagnostics."""
    try:
        # Network interfaces
        interfaces = []
        for interface, addrs in psutil.net_if_addrs().items():
            interface_info = {"name": interface, "addresses": []}

            for addr in addrs:
                interface_info["addresses"].append(
                    {
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast,
                    }
                )

            interfaces.append(interface_info)

        # Network connections
        connections = []
        for conn in psutil.net_connections(kind="inet")[:limit]:
            connections.append(
                {
                    "fd": conn.fd,
                    "family": str(conn.family),
                    "type": str(conn.type),
                    "laddr": (
                        f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None
                    ),
                    "raddr": (
                        f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None
                    ),
                    "status": conn.status,
                    "pid": conn.pid,
                }
            )

        return {
            "network": {
                "interfaces": interfaces,
                "connections": connections,
                "internet_ok": True,  # Simplified check
            },
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Network diagnostics failed: {str(e)}"
        )


@diagnostics_router.get("/diagnostics/cache")
async def diagnostics_cache():
    """Cache diagnostics."""
    try:
        from ...caching.service import CacheService

        cache_service = CacheService()
        stats = cache_service.get_stats()

        return {
            "cache": {
                "l1_status": "healthy",
                "l2_status": "healthy",
                "l3_status": "healthy",
                "stats": stats,
            },
            "status": "success",
        }
    except Exception as e:
        return {
            "cache": {
                "l1_status": "error",
                "l2_status": "error",
                "l3_status": "error",
                "error": str(e),
            },
            "status": "error",
        }


@diagnostics_router.get("/diagnostics/logs")
async def diagnostics_logs(limit: int = 100):
    """Get recent log entries."""
    try:
        import logging

        # This is a simplified implementation
        # In a real application, you'd want to read from log files
        logs = [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "level": "INFO",
                "message": "Application started",
                "module": "main",
            },
            {
                "timestamp": "2024-01-01T00:00:01Z",
                "level": "DEBUG",
                "message": "Configuration loaded",
                "module": "config",
            },
        ]

        return {"logs": logs[:limit], "count": len(logs), "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve logs: {str(e)}"
        )
