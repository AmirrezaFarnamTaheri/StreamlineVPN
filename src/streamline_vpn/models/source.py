"""
Source Model
============

Data model for VPN source management with reputation tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import json


class SourceTier(Enum):
    """Source reliability tiers."""
    PREMIUM = "premium"
    RELIABLE = "reliable"
    BULK = "bulk"
    EXPERIMENTAL = "experimental"


@dataclass
class SourceMetadata:
    """Source metadata with performance tracking.
    
    Attributes:
        url: Source URL
        tier: Source reliability tier
        weight: Source weight for processing priority
        protocols: Supported protocols
        update_frequency: How often to check this source
        last_check: Last check timestamp
        success_count: Number of successful fetches
        failure_count: Number of failed fetches
        avg_response_time: Average response time in seconds
        avg_config_count: Average number of configs returned
        reputation_score: Calculated reputation score (0-1)
        history: Performance history
        is_blacklisted: Whether source is blacklisted
        metadata: Additional metadata
    """
    
    url: str
    tier: SourceTier
    weight: float = 0.5
    protocols: List[str] = field(default_factory=lambda: ["all"])
    update_frequency: str = "24h"
    last_check: datetime = field(default_factory=datetime.now)
    success_count: int = 0
    failure_count: int = 0
    avg_response_time: float = 0.0
    avg_config_count: int = 0
    reputation_score: float = 0.5
    history: List[Dict[str, Any]] = field(default_factory=list)
    is_blacklisted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate source metadata after initialization."""
        if not self.url:
            raise ValueError("Source URL is required")
        if not (0 <= self.weight <= 1):
            raise ValueError("Weight must be between 0 and 1")
        if not (0 <= self.reputation_score <= 1):
            raise ValueError("Reputation score must be between 0 and 1")
    
    def update_reputation(self) -> None:
        """Update reputation score based on recent performance."""
        if not self.history:
            return
        
        # Use last 10 checks for reputation calculation
        recent_history = self.history[-10:]
        
        # Calculate success rate
        success_rate = sum(1 for h in recent_history if h.get('success', False)) / len(recent_history)
        
        # Calculate average config count (only successful fetches)
        successful_fetches = [h for h in recent_history if h.get('success', False)]
        avg_configs = sum(h.get('config_count', 0) for h in successful_fetches) / max(len(successful_fetches), 1)
        
        # Calculate average response time
        avg_response = sum(h.get('response_time', 0) for h in recent_history) / len(recent_history)
        
        # Calculate reputation (0.0 to 1.0)
        self.reputation_score = (
            success_rate * 0.4 +  # 40% weight on success rate
            min(avg_configs / 1000, 1.0) * 0.3 +  # 30% weight on config count
            max(0, 1 - avg_response / 30) * 0.2 +  # 20% weight on response time
            self.weight * 0.1  # 10% weight on base weight
        )
        
        # Apply slight decay to prevent reputation from staying too high
        self.reputation_score = self.reputation_score * 0.95 + 0.05
    
    def add_performance_record(
        self, 
        success: bool, 
        config_count: int, 
        response_time: float
    ) -> None:
        """Add a performance record and update statistics."""
        record = {
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'config_count': config_count,
            'response_time': response_time
        }
        
        self.history.append(record)
        
        # Update counters
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # Update averages
        if self.history:
            recent = self.history[-20:]  # Last 20 records
            self.avg_response_time = sum(h.get('response_time', 0) for h in recent) / len(recent)
            successful_records = [h for h in recent if h.get('success', False)]
            if successful_records:
                self.avg_config_count = int(sum(h.get('config_count', 0) for h in successful_records) / len(successful_records))
        
        # Update reputation
        self.update_reputation()
        
        # Update last check time
        self.last_check = datetime.now()
        
        # Check for blacklisting
        if self.failure_count > 10 and self.success_count < self.failure_count * 0.2:
            self.is_blacklisted = True
    
    def should_update(self) -> bool:
        """Check if source should be updated based on frequency."""
        if self.is_blacklisted:
            return False
        
        # Parse update frequency
        freq_str = self.update_frequency.lower()
        if freq_str.endswith('m'):
            interval = timedelta(minutes=int(freq_str[:-1]))
        elif freq_str.endswith('h'):
            interval = timedelta(hours=int(freq_str[:-1]))
        elif freq_str.endswith('d'):
            interval = timedelta(days=int(freq_str[:-1]))
        else:
            interval = timedelta(hours=24)  # Default
        
        return datetime.now() - self.last_check > interval
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "tier": self.tier.value,
            "weight": self.weight,
            "protocols": self.protocols,
            "update_frequency": self.update_frequency,
            "last_check": self.last_check.isoformat(),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "avg_response_time": self.avg_response_time,
            "avg_config_count": self.avg_config_count,
            "reputation_score": self.reputation_score,
            "history": self.history,
            "is_blacklisted": self.is_blacklisted,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceMetadata":
        """Create from dictionary."""
        data = data.copy()
        data["tier"] = SourceTier(data["tier"])
        if "last_check" in data and isinstance(data["last_check"], str):
            data["last_check"] = datetime.fromisoformat(data["last_check"])
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "SourceMetadata":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.tier.value}:{self.url}"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"SourceMetadata(url={self.url}, tier={self.tier.value}, "
                f"reputation={self.reputation_score:.2f}, "
                f"blacklisted={self.is_blacklisted})")
