"""
Web Interface Module for VPN Configuration Generator
==================================================

This module provides web-based interfaces for VPN configuration generation,
including the ProxyForge generator and integration with the analytics dashboard.
"""

from .config_generator import VPNConfigGenerator
from .static_server import StaticFileServer

__all__ = ["StaticFileServer", "VPNConfigGenerator"]
