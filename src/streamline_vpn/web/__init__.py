"""
Web Interface Components
========================

Web interface components for StreamlineVPN including FastAPI, GraphQL, and
static file serving.
"""

# Unified API (primary)
from .unified_api import create_unified_app, UnifiedAPI, JobManager, ConfigManager

# Legacy API (for backward compatibility)
try:
    from .api import APIServer, create_api_server, create_app
except ImportError:
    APIServer = create_api_server = create_app = None

# Other components
try:
    from .config_generator import VPNConfigGenerator
except ImportError:
    VPNConfigGenerator = None

try:
    from .integrated_server import IntegratedWebServer
except ImportError:
    IntegratedWebServer = None

try:
    from .static_server import EnhancedStaticServer
except ImportError:
    EnhancedStaticServer = None

# Optional GraphQL import
try:
    from .graphql import create_graphql_app
except ImportError:
    create_graphql_app = None

# Backward compatibility alias
StaticFileServer = EnhancedStaticServer

__all__ = [
    # Primary unified API
    "create_unified_app",
    "UnifiedAPI", 
    "JobManager",
    "ConfigManager",
    # Legacy API
    "APIServer",
    "create_api_server", 
    "create_app",
    # Other components
    "VPNConfigGenerator",
    "IntegratedWebServer",
    "StaticFileServer",
    "EnhancedStaticServer",
]

# Add GraphQL to __all__ if available
if create_graphql_app is not None:
    __all__.append("create_graphql_app")
