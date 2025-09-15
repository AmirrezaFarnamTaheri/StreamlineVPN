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
