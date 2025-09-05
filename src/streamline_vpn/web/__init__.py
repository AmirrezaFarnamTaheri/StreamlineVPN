"""
Web Interface Components
========================

Web interface components for StreamlineVPN including FastAPI, GraphQL, and static file serving.
"""

from .api import create_app
from .graphql import create_graphql_app
from .config_generator import VPNConfigGenerator
from .integrated_server import IntegratedWebServer
from .static_server import StaticFileServer

__all__ = [
    "create_app",
    "create_graphql_app", 
    "VPNConfigGenerator",
    "IntegratedWebServer",
    "StaticFileServer"
]
