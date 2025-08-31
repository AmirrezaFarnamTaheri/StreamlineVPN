"""
VPN Subscription Merger
======================

A high-performance, production-ready VPN subscription merger that aggregates and processes
VPN configurations from multiple sources with advanced filtering, validation, and output formatting.

Features:
- Core VPN configuration merging and processing
- Machine learning quality prediction
- Advanced multi-tier caching
- Geographic optimization
- Real-time source discovery
- Analytics dashboard

Version: 2.0.0
Status: Production Ready
License: MIT
Author: VPN Merger Team
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Core components
    from .core.merger import VPNSubscriptionMerger
    from .core.source_manager import SourceManager
    from .core.config_processor import ConfigurationProcessor
    from .core.source_validator import UnifiedSourceValidator
    from .core.output_manager import OutputManager
    from .core.source_processor import SourceProcessor
    
    # Data models
    from .models.configuration import VPNConfiguration
    
    # Utility functions
    from .utils.dependencies import check_dependencies
    from .utils.environment import detect_and_run, run_in_jupyter
    
    # Enhanced modules
    from .ml.quality_predictor_enhanced import EnhancedConfigQualityPredictor
    from .cache.cache_manager import CacheManager
    from .cache.predictive_warmer import PredictiveCacheWarmer
    from .geo.geographic_optimizer import GeographicOptimizer
    from .discovery.discovery_manager import RealTimeDiscovery
    from .analytics.advanced_dashboard import AnalyticsDashboard

# Version information
__version__ = "2.0.0"
__author__ = "VPN Merger Team"
__status__ = "Production Ready"
__license__ = "MIT"

# Core components - always available
from .core.merger import VPNSubscriptionMerger
from .core.source_manager import SourceManager
from .core.config_processor import ConfigurationProcessor
from .core.source_validator import UnifiedSourceValidator
from .core.output import OutputManager
from .core.source_processor import SourceProcessor

# Data models
from .models.configuration import VPNConfiguration

# Utility functions
from .utils.dependencies import check_dependencies
from .utils.environment import detect_and_run, run_in_jupyter

# Enhanced modules (optional imports)
try:
    from .ml.quality_predictor_enhanced import EnhancedConfigQualityPredictor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

try:
    from .cache.cache_manager import CacheManager
    from .cache.predictive_warmer import PredictiveCacheWarmer
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

try:
    from .geo.geographic_optimizer import GeographicOptimizer
    GEO_AVAILABLE = True
except ImportError:
    GEO_AVAILABLE = False

try:
    from .discovery.discovery_manager import RealTimeDiscovery
    DISCOVERY_AVAILABLE = True
except ImportError:
    DISCOVERY_AVAILABLE = False

try:
    from .analytics.advanced_dashboard import AnalyticsDashboard
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

# Public API
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__status__",
    "__license__",
    
    # Core classes
    "VPNSubscriptionMerger",
    "SourceManager", 
    "ConfigurationProcessor",
    "UnifiedSourceValidator",
    "OutputManager",
    "SourceProcessor",
    
    # Data models
    "VPNConfiguration",
    
    # Utility functions
    "check_dependencies",
    "detect_and_run",
    "run_in_jupyter",
    
    # Enhanced modules (conditional)
    "EnhancedConfigQualityPredictor",
    "CacheManager",
    "PredictiveCacheWarmer",
    "GeographicOptimizer",
    "RealTimeDiscovery",
    "AnalyticsDashboard",
    
    # Availability flags
    "ML_AVAILABLE",
    "CACHE_AVAILABLE",
    "GEO_AVAILABLE",
    "DISCOVERY_AVAILABLE",
    "ANALYTICS_AVAILABLE",
]
