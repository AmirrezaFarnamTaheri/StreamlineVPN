"""
StreamlineVPN - Enterprise VPN Configuration Aggregator
======================================================

A high-performance, production-ready VPN configuration aggregator that processes
VPN configurations from multiple sources with advanced filtering, validation,
and output formatting.

Features:
- Multi-source aggregation from 500+ sources
- Machine learning quality prediction
- Advanced multi-tier caching
- Geographic optimization
- Real-time source discovery
- Enterprise-grade security and monitoring

Version: 2.0.0
Status: Production Ready
License: MIT
Author: StreamlineVPN Team
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Core components
    from .core.merger import StreamlineVPNMerger
    from .core.source_manager import SourceManager
    from .core.config_processor import ConfigurationProcessor
    from .core.output_manager import OutputManager
    from .core.caching import VPNCacheService
    
    # Enhanced modules
    from .ml.quality_predictor import QualityPredictor
    from .geo.optimizer import GeographicOptimizer
    from .discovery.manager import DiscoveryManager
    
    # Data models
    from .models.configuration import VPNConfiguration
    from .models.source import SourceMetadata

# Version information
__version__ = "2.0.0"
__author__ = "StreamlineVPN Team"
__status__ = "Production Ready"
__license__ = "MIT"

# Core components - always available
from .core.merger import StreamlineVPNMerger
from .core.source_manager import SourceManager
from .core.config_processor import ConfigurationProcessor
from .core.output_manager import OutputManager

# Web components (lazy import to avoid dependency issues)
try:
    from .web import APIServer, VPNConfigGenerator, IntegratedWebServer, StaticFileServer
except ImportError:
    # Handle missing dependencies gracefully
    APIServer = None
    VPNConfigGenerator = None
    IntegratedWebServer = None
    StaticFileServer = None

# Job management
from .jobs import JobManager, Job, JobStatus, JobType

# Security components (lazy import to avoid dependency issues)
try:
    from .security import SecurityManager, ThreatAnalyzer, SecurityValidator, ZeroTrustVPN
except ImportError:
    SecurityManager = None
    ThreatAnalyzer = None
    SecurityValidator = None
    ZeroTrustVPN = None

# Fetcher service
from .fetcher import FetcherService, CircuitBreaker, RateLimiter

# State management
from .state import SourceStateMachine, SourceState, SourceEvent, StateManager

# Main entry point
def create_merger(config_path: str = "config/sources.yaml") -> StreamlineVPNMerger:
    """Create a new StreamlineVPN merger instance.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configured StreamlineVPN merger instance
    """
    return StreamlineVPNMerger(config_path=config_path)

# Convenience function for quick usage
async def merge_configurations(
    config_path: str = "config/sources.yaml",
    output_dir: str = "output"
) -> dict:
    """Quick function to merge VPN configurations.
    
    Args:
        config_path: Path to the configuration file
        output_dir: Output directory for results
        
    Returns:
        Dictionary with processing results
    """
    merger = create_merger(config_path)
    return await merger.process_all(output_dir=output_dir)

__all__ = [
    "StreamlineVPNMerger",
    "SourceManager", 
    "ConfigurationProcessor",
    "OutputManager",
    "create_merger",
    "merge_configurations",
    "__version__",
    "__author__",
    "__status__",
    "__license__"
]
