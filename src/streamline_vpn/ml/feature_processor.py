"""
Feature Processor
=================

Network feature processing for ML quality prediction.
"""

import numpy as np
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NetworkMetrics:
    """Network performance metrics for ML prediction."""
    timestamp: datetime
    server_id: str
    latency: float
    bandwidth_up: float
    bandwidth_down: float
    packet_loss: float
    jitter: float
    connection_duration: int
    bytes_transferred: int
    protocol: str
    region: str


class NetworkFeatureProcessor:
    """Feature processor for network quality prediction."""
    
    def __init__(self, window_size: int = 30):
        """Initialize feature processor.
        
        Args:
            window_size: Time window size in seconds for feature extraction
        """
        self.window_size = window_size
        self.feature_cache = {}
    
    def extract_features(self, metrics_history: List[NetworkMetrics]) -> Dict[str, float]:
        """Extract features from network metrics for ML prediction.
        
        Args:
            metrics_history: List of network metrics
            
        Returns:
            Dictionary of extracted features
        """
        if not metrics_history:
            return self._get_default_features()
        
        # Sort by timestamp
        sorted_metrics = sorted(metrics_history, key=lambda x: x.timestamp)
        
        # Extract temporal features
        temporal_features = self._extract_temporal_features(sorted_metrics)
        
        # Extract statistical features
        statistical_features = self._extract_statistical_features(sorted_metrics)
        
        # Extract quality metrics
        quality_features = self._extract_quality_features(sorted_metrics)
        
        # Combine all features
        features = {
            **temporal_features,
            **statistical_features,
            **quality_features
        }
        
        return features
    
    def _extract_temporal_features(self, metrics: List[NetworkMetrics]) -> Dict[str, float]:
        """Extract temporal features from metrics."""
        if len(metrics) < 2:
            return {
                "packet_inter_arrival_time": 0.0,
                "rtt_variance": 0.0,
                "bandwidth_trend": 0.0
            }
        
        # Calculate packet inter-arrival times
        timestamps = [m.timestamp for m in metrics]
        inter_arrival_times = [
            (timestamps[i] - timestamps[i-1]).total_seconds()
            for i in range(1, len(timestamps))
        ]
        
        # Calculate RTT variance
        latencies = [m.latency for m in metrics]
        rtt_variance = np.var(latencies) if len(latencies) > 1 else 0.0
        
        # Calculate bandwidth trend
        bandwidths = [m.bandwidth_down for m in metrics]
        bandwidth_trend = self._calculate_trend(bandwidths)
        
        return {
            "packet_inter_arrival_time": np.mean(inter_arrival_times) if inter_arrival_times else 0.0,
            "rtt_variance": rtt_variance,
            "bandwidth_trend": bandwidth_trend
        }
    
    def _extract_statistical_features(self, metrics: List[NetworkMetrics]) -> Dict[str, float]:
        """Extract statistical features from metrics."""
        if not metrics:
            return {
                "packet_size_variance": 0.0,
                "flow_bytes_per_second": 0.0,
                "connection_duration_avg": 0.0
            }
        
        # Calculate packet size variance (using bytes transferred as proxy)
        bytes_transferred = [m.bytes_transferred for m in metrics]
        packet_size_variance = np.var(bytes_transferred) if len(bytes_transferred) > 1 else 0.0
        
        # Calculate flow bytes per second
        total_bytes = sum(bytes_transferred)
        total_duration = sum(m.connection_duration for m in metrics)
        flow_bytes_per_second = total_bytes / max(total_duration, 1)
        
        # Calculate average connection duration
        connection_durations = [m.connection_duration for m in metrics]
        connection_duration_avg = np.mean(connection_durations) if connection_durations else 0.0
        
        return {
            "packet_size_variance": packet_size_variance,
            "flow_bytes_per_second": flow_bytes_per_second,
            "connection_duration_avg": connection_duration_avg
        }
    
    def _extract_quality_features(self, metrics: List[NetworkMetrics]) -> Dict[str, float]:
        """Extract quality metrics from network data."""
        if not metrics:
            return {
                "latency_p95": 0.0,
                "packet_loss_rate": 0.0,
                "jitter_measurement": 0.0,
                "bandwidth_utilization": 0.0
            }
        
        # Calculate latency percentiles
        latencies = [m.latency for m in metrics]
        latency_p95 = np.percentile(latencies, 95) if latencies else 0.0
        
        # Calculate packet loss rate
        packet_losses = [m.packet_loss for m in metrics]
        packet_loss_rate = np.mean(packet_losses) if packet_losses else 0.0
        
        # Calculate jitter measurement
        jitters = [m.jitter for m in metrics]
        jitter_measurement = np.mean(jitters) if jitters else 0.0
        
        # Calculate bandwidth utilization
        bandwidths = [m.bandwidth_down for m in metrics]
        bandwidth_utilization = np.mean(bandwidths) if bandwidths else 0.0
        
        return {
            "latency_p95": latency_p95,
            "packet_loss_rate": packet_loss_rate,
            "jitter_measurement": jitter_measurement,
            "bandwidth_utilization": bandwidth_utilization
        }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend of values using linear regression."""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        y = np.array(values)
        
        # Simple linear regression
        n = len(values)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
    
    def _get_default_features(self) -> Dict[str, float]:
        """Get default feature values when no metrics are available."""
        return {
            "packet_inter_arrival_time": 0.0,
            "rtt_variance": 0.0,
            "bandwidth_trend": 0.0,
            "packet_size_variance": 0.0,
            "flow_bytes_per_second": 0.0,
            "connection_duration_avg": 0.0,
            "latency_p95": 0.0,
            "packet_loss_rate": 0.0,
            "jitter_measurement": 0.0,
            "bandwidth_utilization": 0.0
        }
