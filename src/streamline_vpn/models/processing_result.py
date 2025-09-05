"""
Processing Result Model
=======================

Data model for processing results and statistics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import json


@dataclass
class ProcessingResult:
    """Result container for source processing.
    
    Attributes:
        url: Source URL that was processed
        success: Whether processing was successful
        configs: List of extracted configurations
        error: Error message if processing failed
        response_time: Response time in seconds
        retry_count: Number of retries attempted
        config_count: Number of configurations found
        quality_scores: Quality scores for each config
        metadata: Additional processing metadata
    """
    
    url: str
    success: bool
    configs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    response_time: float = 0.0
    retry_count: int = 0
    config_count: int = 0
    quality_scores: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Update config_count after initialization."""
        self.config_count = len(self.configs)
    
    @property
    def avg_quality_score(self) -> float:
        """Calculate average quality score."""
        if not self.quality_scores:
            return 0.0
        return sum(self.quality_scores) / len(self.quality_scores)
    
    @property
    def is_high_quality(self) -> bool:
        """Check if result contains high-quality configurations."""
        return self.avg_quality_score > 0.7
    
    def add_config(self, config: str, quality_score: float = 0.0) -> None:
        """Add a configuration with quality score."""
        self.configs.append(config)
        self.quality_scores.append(quality_score)
        self.config_count = len(self.configs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "success": self.success,
            "configs": self.configs,
            "error": self.error,
            "response_time": self.response_time,
            "retry_count": self.retry_count,
            "config_count": self.config_count,
            "quality_scores": self.quality_scores,
            "avg_quality_score": self.avg_quality_score,
            "is_high_quality": self.is_high_quality,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessingResult":
        """Create from dictionary."""
        # Remove computed fields
        data = data.copy()
        data.pop("avg_quality_score", None)
        data.pop("is_high_quality", None)
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> "ProcessingResult":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def __str__(self) -> str:
        """String representation."""
        status = "SUCCESS" if self.success else "FAILED"
        return f"{status}: {self.url} ({self.config_count} configs)"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"ProcessingResult(url={self.url}, success={self.success}, "
                f"config_count={self.config_count}, "
                f"avg_quality={self.avg_quality_score:.2f})")


@dataclass
class ProcessingStatistics:
    """Statistics for processing operations.
    
    Attributes:
        total_sources: Total number of sources processed
        successful_sources: Number of successfully processed sources
        failed_sources: Number of failed sources
        total_configs: Total number of configurations found
        avg_response_time: Average response time
        total_processing_time: Total processing time
        start_time: Processing start time
        end_time: Processing end time
    """
    
    total_sources: int = 0
    successful_sources: int = 0
    failed_sources: int = 0
    total_configs: int = 0
    avg_response_time: float = 0.0
    total_processing_time: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_sources == 0:
            return 0.0
        return self.successful_sources / self.total_sources
    
    @property
    def configs_per_source(self) -> float:
        """Calculate average configs per source."""
        if self.successful_sources == 0:
            return 0.0
        return self.total_configs / self.successful_sources
    
    def finish(self) -> None:
        """Mark processing as finished."""
        self.end_time = datetime.now()
        if self.start_time:
            self.total_processing_time = (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_sources": self.total_sources,
            "successful_sources": self.successful_sources,
            "failed_sources": self.failed_sources,
            "total_configs": self.total_configs,
            "avg_response_time": self.avg_response_time,
            "total_processing_time": self.total_processing_time,
            "success_rate": self.success_rate,
            "configs_per_source": self.configs_per_source,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def __str__(self) -> str:
        """String representation."""
        return (f"ProcessingStats(sources={self.total_sources}, "
                f"success_rate={self.success_rate:.1%}, "
                f"configs={self.total_configs})")
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"ProcessingStatistics(total_sources={self.total_sources}, "
                f"successful_sources={self.successful_sources}, "
                f"total_configs={self.total_configs}, "
                f"success_rate={self.success_rate:.2f})")
