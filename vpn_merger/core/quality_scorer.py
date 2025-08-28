from dataclasses import dataclass
from typing import List, Dict, Optional
import math


@dataclass
class QualityMetrics:
    ping_score: float
    reliability_score: float
    protocol_score: float
    geographic_score: float
    popularity_score: float
    composite_score: float


class AdvancedQualityScorer:
    def __init__(self):
        self.weights = {
            'ping': 0.3,
            'reliability': 0.25,
            'protocol': 0.2,
            'geographic': 0.15,
            'popularity': 0.1
        }
        self.protocol_rankings = {
            'Reality': 100,
            'VLESS': 95,
            'VMess': 85,
            'Hysteria2': 90,
            'Trojan': 80,
            'Shadowsocks': 75,
            'TUIC': 85,
            'WireGuard': 92,
            'Other': 50
        }

    def calculate_ping_score(self, ping_ms: Optional[float]) -> float:
        if ping_ms is None:
            return 0.0
        return max(0.0, 100.0 * math.exp(-ping_ms / 150.0))

    def calculate_reliability_score(self, success_history: List[bool]) -> float:
        if not success_history:
            return 50.0
        return (sum(success_history) / len(success_history)) * 100.0

    def calculate_protocol_score(self, protocol: str) -> float:
        return self.protocol_rankings.get(protocol, 50.0)

    def calculate_geographic_score(self, host: str, user_location: str = "US") -> float:
        return 75.0

    def calculate_popularity_score(self, source_url: str, source_stats: Dict) -> float:
        base_score = source_stats.get('reputation', 50)
        update_frequency = source_stats.get('update_frequency_hours', 24)
        frequency_bonus = min(25, (48 - update_frequency) / 2)
        return min(100.0, float(base_score) + float(frequency_bonus))

    def calculate_quality_metrics(self, config_result, history_data: Dict = None) -> QualityMetrics:
        ping_score = self.calculate_ping_score(
            config_result.ping_time * 1000 if getattr(config_result, 'ping_time', None) else None
        )
        reliability_score = self.calculate_reliability_score(
            history_data.get('success_history', []) if history_data else []
        )
        protocol_score = self.calculate_protocol_score(getattr(config_result, 'protocol', 'Other'))
        geographic_score = self.calculate_geographic_score(getattr(config_result, 'host', '') or "")
        popularity_score = self.calculate_popularity_score(
            getattr(config_result, 'source_url', ''),
            history_data.get('source_stats', {}) if history_data else {}
        )
        composite_score = (
            ping_score * self.weights['ping'] +
            reliability_score * self.weights['reliability'] +
            protocol_score * self.weights['protocol'] +
            geographic_score * self.weights['geographic'] +
            popularity_score * self.weights['popularity']
        )
        return QualityMetrics(
            ping_score=ping_score,
            reliability_score=reliability_score,
            protocol_score=protocol_score,
            geographic_score=geographic_score,
            popularity_score=popularity_score,
            composite_score=composite_score,
        )


