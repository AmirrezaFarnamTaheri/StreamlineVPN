from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple


class ProtocolHandler(ABC):
    """Base class for protocol handlers."""

    @abstractmethod
    def parse(self, raw: str) -> Optional[Dict]:
        """Parse raw config string to structured format."""
        raise NotImplementedError

    @abstractmethod
    def validate(self, config: Dict) -> bool:
        """Validate config structure and values."""
        raise NotImplementedError

    @abstractmethod
    def extract_endpoint(self, config: Dict) -> Tuple[str, int]:
        """Extract host and port from config."""
        raise NotImplementedError

    @abstractmethod
    def to_uri(self, config: Dict) -> str:
        """Convert config to canonical URI."""
        raise NotImplementedError

    @abstractmethod
    def to_clash(self, config: Dict) -> Dict:
        """Convert to Clash format."""
        raise NotImplementedError

    @abstractmethod
    def to_singbox(self, config: Dict) -> Dict:
        """Convert to Sing-box format."""
        raise NotImplementedError

