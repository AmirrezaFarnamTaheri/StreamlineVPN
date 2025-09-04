"""
Quality Metrics for Source Validation
=====================================

Data structures and utilities for measuring and tracking source quality metrics.
"""

import base64
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Set


@dataclass
class SourceQualityMetrics:
    """Comprehensive quality metrics for a source."""
    
    url: str
    quality_score: float
    historical_reliability: float
    ssl_certificate_score: float
    response_time_score: float
    content_quality_score: float
    protocol_diversity_score: float
    uptime_consistency_score: float
    last_checked: datetime
    check_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    average_response_time: float = 0.0
    protocols_found: Set[str] = field(default_factory=set)
    content_indicators: Dict[str, bool] = field(default_factory=dict)
    ssl_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "quality_score": self.quality_score,
            "historical_reliability": self.historical_reliability,
            "ssl_certificate_score": self.ssl_certificate_score,
            "response_time_score": self.response_time_score,
            "content_quality_score": self.content_quality_score,
            "protocol_diversity_score": self.protocol_diversity_score,
            "uptime_consistency_score": self.uptime_consistency_score,
            "last_checked": self.last_checked.isoformat(),
            "check_count": self.check_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "average_response_time": self.average_response_time,
            "protocols_found": list(self.protocols_found),
            "content_indicators": self.content_indicators,
            "ssl_info": self.ssl_info,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceQualityMetrics":
        """Create from dictionary."""
        return cls(
            url=data["url"],
            quality_score=data["quality_score"],
            historical_reliability=data["historical_reliability"],
            ssl_certificate_score=data["ssl_certificate_score"],
            response_time_score=data["response_time_score"],
            content_quality_score=data["content_quality_score"],
            protocol_diversity_score=data["protocol_diversity_score"],
            uptime_consistency_score=data["uptime_consistency_score"],
            last_checked=datetime.fromisoformat(data["last_checked"]),
            check_count=data.get("check_count", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            average_response_time=data.get("average_response_time", 0.0),
            protocols_found=set(data.get("protocols_found", [])),
            content_indicators=data.get("content_indicators", {}),
            ssl_info=data.get("ssl_info", {}),
        )
    
    def update_historical_data(self, success: bool, response_time: float) -> None:
        """Update historical reliability data."""
        self.check_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # Update average response time
        if self.average_response_time == 0.0:
            self.average_response_time = response_time
        else:
            self.average_response_time = (self.average_response_time + response_time) / 2
        
        # Update historical reliability
        self.historical_reliability = self.success_count / self.check_count if self.check_count > 0 else 0.0
        
        self.last_checked = datetime.now()
    
    def calculate_overall_quality(self) -> float:
        """Calculate overall quality score based on all metrics."""
        from .quality_weights import QUALITY_WEIGHTS
        
        weighted_score = (
            self.historical_reliability * QUALITY_WEIGHTS["historical_reliability"] +
            self.ssl_certificate_score * QUALITY_WEIGHTS["ssl_certificate"] +
            self.response_time_score * QUALITY_WEIGHTS["response_time"] +
            self.content_quality_score * QUALITY_WEIGHTS["content_quality"] +
            self.protocol_diversity_score * QUALITY_WEIGHTS["protocol_diversity"] +
            self.uptime_consistency_score * QUALITY_WEIGHTS["uptime_consistency"]
        )
        
        self.quality_score = max(0.0, min(1.0, weighted_score))
        return self.quality_score


@dataclass
class ValidationResult:
    """Result of a source validation operation."""
    
    url: str
    accessible: bool
    response_time: float
    status_code: int
    content_length: int
    protocols_found: Set[str]
    content_quality_indicators: Dict[str, bool]
    ssl_info: Dict[str, Any]
    error_message: str = ""
    reliability_score: float = 0.0
    estimated_configs: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "accessible": self.accessible,
            "response_time": self.response_time,
            "status_code": self.status_code,
            "content_length": self.content_length,
            "protocols_found": list(self.protocols_found),
            "content_quality_indicators": self.content_quality_indicators,
            "ssl_info": self.ssl_info,
            "error_message": self.error_message,
            "reliability_score": self.reliability_score,
            "estimated_configs": self.estimated_configs,
        }


def is_base64_encoded(content: str) -> bool:
    """Check if content is base64 encoded.
    
    Args:
        content: Content to check
        
    Returns:
        True if content appears to be base64 encoded
    """
    try:
        # Remove whitespace
        clean_content = re.sub(r'\s+', '', content)
        
        # Check if it's valid base64
        if len(clean_content) > 0 and len(clean_content) % 4 == 0:
            base64.b64decode(clean_content)
            return True
    except Exception:
        pass
    
    return False


def is_json_format(content: str) -> bool:
    """Check if content is JSON format.
    
    Args:
        content: Content to check
        
    Returns:
        True if content is valid JSON
    """
    try:
        json.loads(content)
        return True
    except json.JSONDecodeError:
        return False