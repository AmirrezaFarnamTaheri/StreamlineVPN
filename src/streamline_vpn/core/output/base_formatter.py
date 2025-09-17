"""
Base Output Formatter
=====================

Base class for output formatting functionality.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from ...models.configuration import VPNConfiguration
from ...utils.logging import get_logger

logger = get_logger(__name__)


class BaseFormatter(ABC):
    """Base class for output formatters."""

    def __init__(self, output_dir: Path):
        """Initialize formatter.

        Args:
            output_dir: Output directory path
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def format_configurations(self, configs: List[VPNConfiguration]) -> str:
        """Format configurations to string.

        Args:
            configs: List of VPN configurations

        Returns:
            Formatted string
        """
        # Default implementation - can be overridden by subclasses
        return "\n".join(str(config) for config in configs)

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get file extension for this format.

        Returns:
            File extension (e.g., '.json', '.yaml')
        """
        pass

    def save_configurations(
        self, configs: List[VPNConfiguration], filename: str
    ) -> Path:
        """Save configurations to file.

        Args:
            configs: List of VPN configurations
            filename: Output filename (without extension)

        Returns:
            Path to saved file
        """
        content = self.format_configurations(configs)
        file_path = self.output_dir / f"{filename}{self.get_file_extension()}"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info("Saved %d configurations to %s", len(configs), file_path)
            return file_path
        except Exception as e:
            logger.error("Failed to save configurations to %s: %s", file_path, e)
            raise

    def _config_to_dict(self, config: VPNConfiguration) -> Dict[str, Any]:
        """Convert VPN configuration to dictionary.

        Args:
            config: VPN configuration

        Returns:
            Configuration dictionary
        """
        return {
            "id": getattr(config, "id", None),
            "protocol": getattr(config.protocol, "value", str(config.protocol)),
            "server": getattr(config, "server", ""),
            "port": getattr(config, "port", 0),
            "user_id": getattr(config, "user_id", None),
            "password": getattr(config, "password", None),
            "encryption": getattr(config, "encryption", None),
            "network": getattr(config, "network", None),
            "path": getattr(config, "path", None),
            "host": getattr(config, "host", None),
            "tls": getattr(config, "tls", False),
            "quality_score": getattr(config, "quality_score", 0.0),
            "source_url": getattr(config, "source_url", None),
            "created_at": (
                config.created_at.isoformat()
                if getattr(config, "created_at", None)
                else None
            ),
            "metadata": getattr(config, "metadata", {}),
        }

    def _safe_config_to_dict(self, config: VPNConfiguration) -> Dict[str, Any]:
        """Safely convert VPN configuration to dictionary with error handling.

        Args:
            config: VPN configuration

        Returns:
            Configuration dictionary
        """
        try:
            return self._config_to_dict(config)
        except Exception as e:
            logger.error("Failed to convert config to dict: %s", e)
            return {
                "id": getattr(config, "id", "unknown"),
                "protocol": "unknown",
                "server": "unknown",
                "port": 0,
                "error": str(e),
            }
