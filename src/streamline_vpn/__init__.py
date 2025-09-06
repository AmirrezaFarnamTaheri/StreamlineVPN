"""
StreamlineVPN - Enterprise VPN Configuration Aggregator
======================================================

A high-performance, production-ready VPN configuration aggregator.
"""

# Version information
__version__ = "2.0.0"
__author__ = "StreamlineVPN Team"
__status__ = "Production Ready"
__license__ = "MIT"

# Core components
from .core.merger import StreamlineVPNMerger
from .core.source_manager import SourceManager
from .core.config_processor import ConfigurationProcessor
from .core.output_manager import OutputManager
from .core.caching import VPNCacheService

# Enhanced modules
from .ml.quality_predictor import QualityPredictionService
from .geo.optimizer import GeographicOptimizer
from .discovery.manager import DiscoveryManager

# Data models
from .models.configuration import VPNConfiguration
from .models.source import SourceMetadata

# Web components (lazy import to avoid dependency issues)
try:
    from .web import (
        APIServer,
        VPNConfigGenerator,
        IntegratedWebServer,
        StaticFileServer,
    )
except ImportError:
    APIServer = None
    VPNConfigGenerator = None
    IntegratedWebServer = None
    StaticFileServer = None

# Job management
try:
    from .jobs import JobManager, Job, JobStatus, JobType
except ImportError:
    JobManager = Job = JobStatus = JobType = None

# Security components
try:
    from .security import (
        SecurityManager,
        ThreatAnalyzer,
        SecurityValidator,
        ZeroTrustVPN,
    )
except ImportError:
    SecurityManager = ThreatAnalyzer = SecurityValidator = ZeroTrustVPN = None

# Fetcher service
try:
    from .fetcher import FetcherService, CircuitBreaker, RateLimiter
except ImportError:
    FetcherService = CircuitBreaker = RateLimiter = None

# State management
try:
    from .state import SourceStateMachine, SourceState, SourceEvent, StateManager
except ImportError:
    SourceStateMachine = SourceState = SourceEvent = StateManager = None


# Main entry point
def create_merger(
    config_path: str = "config/sources.yaml",
) -> "StreamlineVPNMerger":
    """Create a new StreamlineVPN merger instance."""
    return StreamlineVPNMerger(config_path=config_path)


# Convenience function for quick usage
async def merge_configurations(
    config_path: str = "config/sources.yaml", output_dir: str = "output"
) -> dict:
    """Quick function to merge VPN configurations."""
    merger = create_merger(config_path)
    return await merger.process_all(output_dir=output_dir)


__all__ = [
    # Core
    "StreamlineVPNMerger",
    "SourceManager",
    "ConfigurationProcessor",
    "OutputManager",
    "VPNCacheService",
    # Enhanced
    "QualityPredictionService",
    "GeographicOptimizer",
    "DiscoveryManager",
    # Models
    "VPNConfiguration",
    "SourceMetadata",
    # Web
    "APIServer",
    "VPNConfigGenerator",
    "IntegratedWebServer",
    "StaticFileServer",
    # Jobs
    "JobManager",
    "Job",
    "JobStatus",
    "JobType",
    # Security
    "SecurityManager",
    "ThreatAnalyzer",
    "SecurityValidator",
    "ZeroTrustVPN",
    # Fetcher
    "FetcherService",
    "CircuitBreaker",
    "RateLimiter",
    # State
    "SourceStateMachine",
    "SourceState",
    "SourceEvent",
    "StateManager",
    # Functions
    "create_merger",
    "merge_configurations",
    # Metadata
    "__version__",
    "__author__",
    "__status__",
    "__license__",
]
