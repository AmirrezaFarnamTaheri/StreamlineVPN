"""
VPN Configuration Model
======================

Defines the data structure for VPN configurations with validation and serialization.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional, Union


@dataclass(frozen=False)
class VPNConfiguration:
    """Enhanced VPN configuration with testing metrics and quality assessment.
    
    This dataclass represents a VPN configuration with comprehensive metadata
    including protocol information, quality scoring, and testing results.
    
    Attributes:
        config: The raw configuration string
        protocol: Detected VPN protocol (vmess, vless, trojan, etc.)
        host: Extracted hostname/IP address
        port: Extracted port number
        ping_time: Measured ping time in milliseconds
        is_reachable: Whether the configuration is currently accessible
        source_url: Source URL where this configuration was found
        quality_score: Calculated quality score (0.0 to 1.0)
        last_tested: Timestamp of last connectivity test
        error_count: Number of consecutive errors encountered
    """
    
    config: str
    protocol: str
    host: Optional[str] = None
    port: Optional[int] = None
    ping_time: Optional[float] = None
    is_reachable: bool = False
    source_url: Optional[str] = None
    quality_score: float = 0.0
    last_tested: Optional[datetime] = None
    error_count: int = 0
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration data."""
        if not self.config or not self.config.strip():
            raise ValueError("Configuration string cannot be empty")
        
        if not isinstance(self.quality_score, (int, float)):
            raise ValueError("Quality score must be numeric")
        
        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError("Quality score must be between 0.0 and 1.0")
        
        if self.error_count < 0:
            raise ValueError("Error count cannot be negative")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of the configuration
        """
        return asdict(self)
    
    def __hash__(self) -> int:
        """Hash based on config content for deduplication.
        
        Returns:
            Hash value based on configuration content
        """
        return hash(self.config.strip())
    
    def __eq__(self, other: Any) -> bool:
        """Equality based on config content.
        
        Args:
            other: Object to compare with
            
        Returns:
            True if configurations are equal, False otherwise
        """
        if not isinstance(other, VPNConfiguration):
            return False
        return self.config.strip() == other.config.strip()
    
    def is_valid(self) -> bool:
        """Check if configuration is valid.
        
        Returns:
            True if configuration meets validity criteria
        """
        return (
            bool(self.config and self.config.strip()) and
            bool(self.protocol and self.protocol != 'unknown') and
            0.0 <= self.quality_score <= 1.0 and
            self.error_count >= 0
        )
    
    def update_quality_score(self, new_score: float) -> None:
        """Update quality score with validation.
        
        Args:
            new_score: New quality score (0.0 to 1.0)
            
        Raises:
            ValueError: If score is outside valid range
        """
        if not isinstance(new_score, (int, float)):
            raise ValueError("Quality score must be numeric")
        
        if not 0.0 <= new_score <= 1.0:
            raise ValueError("Quality score must be between 0.0 and 1.0")
        
        self.quality_score = float(new_score)
    
    def mark_tested(self, ping_time: Optional[float] = None, is_reachable: bool = False) -> None:
        """Mark configuration as tested with results.
        
        Args:
            ping_time: Measured ping time in milliseconds
            is_reachable: Whether the configuration is accessible
        """
        self.last_tested = datetime.now()
        if ping_time is not None:
            if not isinstance(ping_time, (int, float)) or ping_time < 0:
                raise ValueError("Ping time must be a non-negative number")
            self.ping_time = float(ping_time)
        self.is_reachable = bool(is_reachable)
    
    def increment_error_count(self) -> None:
        """Increment error count for failed operations."""
        self.error_count += 1
    
    def reset_error_count(self) -> None:
        """Reset error count to zero."""
        self.error_count = 0
    
    def get_status_summary(self) -> str:
        """Get a human-readable status summary.
        
        Returns:
            Status summary string
        """
        if self.is_reachable:
            status = "✅ Accessible"
            if self.ping_time is not None:
                status += f" (ping: {self.ping_time:.1f}ms)"
        else:
            status = "❌ Unreachable"
        
        if self.error_count > 0:
            status += f" (errors: {self.error_count})"
        
        return status
