# isort: skip_file
"""StreamlineVPN - Enterprise VPN Configuration Aggregator
======================================================

A high-performance, production-ready VPN configuration aggregator.
"""

__version__ = "2.0.0"
__author__ = "StreamlineVPN Team"
__status__ = "Production Ready"
__license__ = "GPL-3.0-or-later"

from .core.config_processor import ConfigurationProcessor
from .core.merger import StreamlineVPNMerger
from .core.output_manager import OutputManager
from .core.source_manager import SourceManager
from .models.configuration import VPNConfiguration
from .models.source import SourceMetadata


try:
    from .core.caching import VPNCacheService  # optional
except ImportError:  # pragma: no cover
    VPNCacheService = None  # type: ignore

try:
    from .ml.quality_predictor import QualityPredictionService  # optional
except ImportError:  # pragma: no cover
    QualityPredictionService = None  # type: ignore

try:
    from .geo.optimizer import GeographicOptimizer  # optional
except ImportError:  # pragma: no cover
    GeographicOptimizer = None  # type: ignore

try:
    from .discovery.manager import DiscoveryManager  # optional
except ImportError:  # pragma: no cover
    DiscoveryManager = None  # type: ignore

try:
    from .web import (
        APIServer,
        IntegratedWebServer,
        StaticFileServer,
        VPNConfigGenerator,
    )
except ImportError:
    APIServer = VPNConfigGenerator = IntegratedWebServer = StaticFileServer = (
        None
    )

try:
    from .jobs import Job, JobManager, JobStatus, JobType
except ImportError:  # pragma: no cover
    JobManager = Job = JobStatus = JobType = None

try:
    from .security import (
        SecurityManager,
        SecurityValidator,
        ThreatAnalyzer,
        ZeroTrustVPN,
    )
except ImportError:  # pragma: no cover
    SecurityManager = ThreatAnalyzer = SecurityValidator = ZeroTrustVPN = None

try:
    from .fetcher import CircuitBreaker, FetcherService, RateLimiter
except ImportError:  # pragma: no cover
    FetcherService = CircuitBreaker = RateLimiter = None

try:
    from .state import (
        SourceEvent,
        SourceState,
        SourceStateMachine,
        StateManager,
    )
except ImportError:  # pragma: no cover
    SourceStateMachine = SourceState = SourceEvent = StateManager = None


def create_merger(
    config_path: str = "config/sources.yaml",
) -> "StreamlineVPNMerger":
    """Create a new StreamlineVPN merger instance."""
    return StreamlineVPNMerger(config_path=config_path)


async def merge_configurations(
    config_path: str = "config/sources.yaml", output_dir: str = "output"
) -> dict:
    """Quick function to merge VPN configurations."""
    merger = create_merger(config_path)
    return await merger.process_all(output_dir=output_dir)


__all__ = [
    "StreamlineVPNMerger",
    "SourceManager",
    "ConfigurationProcessor",
    "OutputManager",
    "VPNConfiguration",
    "SourceMetadata",
    "create_merger",
    "merge_configurations",
    "__version__",
    "__author__",
    "__status__",
    "__license__",
]

for _name in [
    "VPNCacheService",
    "QualityPredictionService",
    "GeographicOptimizer",
    "DiscoveryManager",
    "APIServer",
    "VPNConfigGenerator",
    "IntegratedWebServer",
    "StaticFileServer",
    "JobManager",
    "Job",
    "JobStatus",
    "JobType",
    "SecurityManager",
    "ThreatAnalyzer",
    "SecurityValidator",
    "ZeroTrustVPN",
    "FetcherService",
    "CircuitBreaker",
    "RateLimiter",
    "SourceStateMachine",
    "SourceState",
    "SourceEvent",
    "StateManager",
]:
    if locals().get(_name) is not None:
        __all__.append(_name)
