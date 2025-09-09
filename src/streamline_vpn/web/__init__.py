"""
Web Interface Components
========================

Web interface components for StreamlineVPN including FastAPI, GraphQL, and
static file serving.
"""

from .api import APIServer, create_api_server, create_app
from .config_generator import VPNConfigGenerator
from .integrated_server import IntegratedWebServer
from .static_server import EnhancedStaticServer

# Optional GraphQL import
try:
    from .graphql import create_graphql_app
except ImportError:
    create_graphql_app = None

# Backward compatibility alias
StaticFileServer = EnhancedStaticServer

__all__ = [
    "APIServer",
    "create_api_server",
    "create_app",
    "VPNConfigGenerator",
    "IntegratedWebServer",
    "StaticFileServer",
    "EnhancedStaticServer",
]

# Add GraphQL to __all__ if available
if create_graphql_app is not None:
    __all__.append("create_graphql_app")
