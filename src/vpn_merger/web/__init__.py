"""
Web Interface Module for VPN Configuration Generator
==================================================

This module provides web-based interfaces for VPN configuration generation,
including the ProxyForge generator, enhanced interface, and integration with the analytics dashboard.
"""

from .config_generator import VPNConfigGenerator
from .static_server import StaticFileServer

# Lazy import to avoid hard dependency on optional web extras at package import time
def get_enhanced_web_interface():
    from .enhanced_interface import EnhancedWebInterface
    return EnhancedWebInterface

__all__ = [
    "StaticFileServer", 
    "VPNConfigGenerator",
    "get_enhanced_web_interface",
]
