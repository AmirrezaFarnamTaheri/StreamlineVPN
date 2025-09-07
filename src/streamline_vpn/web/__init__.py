"""
Web Interface Components
========================

Web interface components for StreamlineVPN including FastAPI, GraphQL, and
static file serving.
"""

from .api import APIServer, create_app
from .config_generator import VPNConfigGenerator
from .graphql import create_graphql_app
from .integrated_server import IntegratedWebServer
from .static_server import EnhancedStaticServer

# Backward compatibility alias
StaticFileServer = EnhancedStaticServer

__all__ = [
    "APIServer",
    "create_app",
    "create_graphql_app",
    "VPNConfigGenerator",
    "IntegratedWebServer",
    "StaticFileServer",
    "EnhancedStaticServer",
]
