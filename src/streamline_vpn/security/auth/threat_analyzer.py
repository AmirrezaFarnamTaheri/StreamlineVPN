"""
Threat Analyzer
==============

Threat analysis and risk assessment service.
"""

from datetime import datetime

from ...utils.logging import get_logger
from .models import UserIdentity, DeviceInfo, DevicePosture, ThreatLevel

logger = get_logger(__name__)


class ThreatAnalyzer:
    """Threat analysis and risk assessment service."""

    def __init__(self):
        """Initialize threat analyzer."""
        self.risk_factors = {
            "device_compliance": 0.3,
            "ip_reputation": 0.2,
            "geolocation": 0.2,
            "time_patterns": 0.1,
            "behavioral_anomalies": 0.2,
        }

    async def assess_threat_level(
        self,
        user_identity: UserIdentity,
        device_info: DeviceInfo,
        device_posture: DevicePosture,
    ) -> ThreatLevel:
        """Assess overall threat level.

        Args:
            user_identity: User identity
            device_info: Device information
            device_posture: Device posture

        Returns:
            Threat level assessment
        """
        risk_score = 0.0

        # Device compliance risk
        if device_posture.status.value == "suspicious":
            risk_score += self.risk_factors["device_compliance"]
        elif device_posture.status.value == "non_compliant":
            risk_score += self.risk_factors["device_compliance"] * 0.5

        # IP reputation risk (simplified)
        ip_risk = await self._assess_ip_reputation(device_info.ip_address)
        risk_score += ip_risk * self.risk_factors["ip_reputation"]

        # Geolocation risk (simplified)
        geo_risk = await self._assess_geolocation_risk(device_info.ip_address)
        risk_score += geo_risk * self.risk_factors["geolocation"]

        # Time pattern risk
        time_risk = await self._assess_time_patterns(user_identity.user_id)
        risk_score += time_risk * self.risk_factors["time_patterns"]

        # Behavioral anomalies risk
        behavior_risk = await self._assess_behavioral_anomalies(
            user_identity.user_id
        )
        risk_score += behavior_risk * self.risk_factors["behavioral_anomalies"]

        # Determine threat level
        if risk_score >= 0.8:
            return ThreatLevel.CRITICAL
        elif risk_score >= 0.6:
            return ThreatLevel.HIGH
        elif risk_score >= 0.4:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW

    async def _assess_ip_reputation(self, ip_address: str) -> float:
        """Assess IP address reputation."""
        # Simplified IP reputation check
        # In production, integrate with threat intelligence feeds
        suspicious_ips = ["192.168.1.100", "10.0.0.100"]  # Demo suspicious IPs

        if ip_address in suspicious_ips:
            logger.warning("High-risk IP detected: %s", ip_address)
            try:
                import logging as _logging
                _logging.getLogger().warning("High-risk IP detected: %s", ip_address)
            except Exception:
                pass
            return 1.0

        logger.debug("IP address %s has no reputation flags", ip_address)
        return 0.0

    async def _assess_geolocation_risk(self, ip_address: str) -> float:
        """Assess geolocation risk."""
        # Simplified geolocation risk assessment
        # In production, use a GeoIP database
        import ipaddress

        high_risk_countries = ["XX", "YY"]  # Demo high-risk countries

        try:
            ip_obj = ipaddress.ip_address(ip_address)
        except ValueError:
            logger.warning("Invalid IP address for geolocation: %s", ip_address)
            try:
                import logging as _logging
                _logging.getLogger().warning("Invalid IP address for geolocation: %s", ip_address)
            except Exception:
                pass
            return 1.0

        # Determine country code; for private/reserved ranges mark as 'PRIVATE'
        country_code = "PRIVATE" if ip_obj.is_private else "UNKNOWN"

        if country_code in high_risk_countries:
            logger.warning(
                "IP %s located in high-risk country: %s", ip_address, country_code
            )
            return 1.0

        logger.debug(
            "IP %s geolocation assessed as low risk (%s)", ip_address, country_code
        )
        return 0.0

    async def _assess_time_patterns(self, user_id: str) -> float:
        """Assess time-based access patterns."""
        # Simplified time pattern analysis
        current_hour = datetime.now().hour

        # Normal business hours (9 AM - 6 PM)
        if 9 <= current_hour <= 18:
            return 0.0

        # After hours access
        return 0.3

    async def _assess_behavioral_anomalies(self, user_id: str) -> float:
        """Assess behavioral anomalies."""
        # Simplified behavioral analysis
        # In production, use machine learning models
        return 0.0
