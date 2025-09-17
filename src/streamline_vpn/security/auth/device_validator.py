"""
Device Validator
===============

Device posture validation service for Zero Trust security.
"""

from typing import Any, Dict

from ....utils.logging import get_logger
from .models import DeviceInfo, DevicePosture, DeviceStatus

logger = get_logger(__name__)


class DeviceValidator:
    """Device posture validation service."""

    def __init__(self):
        """Initialize device validator."""
        self.compliance_rules = {
            "os_version": {
                "windows": {"min_version": "10.0.19041"},
                "macos": {"min_version": "10.15"},
                "linux": {"min_version": "5.4"},
            },
            "browser_version": {
                "chrome": {"min_version": "90"},
                "firefox": {"min_version": "88"},
                "safari": {"min_version": "14"},
            },
            "security_features": {
                "required_plugins": [],
                "blocked_plugins": ["flash", "java"],
                "required_certificates": [],
            },
        }
        self.device_postures: Dict[str, DevicePosture] = {}

    async def check_posture(self, device_info: DeviceInfo) -> DevicePosture:
        """Check device posture compliance.

        Args:
            device_info: Device information

        Returns:
            Device posture assessment
        """
        compliance_score = 0.0
        risk_factors = []
        recommendations = []

        # Check OS version compliance
        os_compliance = await self._check_os_compliance(device_info)
        compliance_score += os_compliance["score"]
        if not os_compliance["compliant"]:
            risk_factors.append(f"Outdated OS: {device_info.os_version}")
            recommendations.append("Update operating system to latest version")

        # Check browser version compliance
        browser_compliance = await self._check_browser_compliance(device_info)
        compliance_score += browser_compliance["score"]
        if not browser_compliance["compliant"]:
            risk_factors.append(f"Outdated browser: {device_info.browser_version}")
            recommendations.append("Update browser to latest version")

        # Check security features
        security_compliance = await self._check_security_features(device_info)
        compliance_score += security_compliance["score"]
        if not security_compliance["compliant"]:
            risk_factors.extend(security_compliance["risk_factors"])
            recommendations.extend(security_compliance["recommendations"])

        # Check for suspicious characteristics
        suspicious_factors = await self._check_suspicious_characteristics(device_info)
        compliance_score -= suspicious_factors["penalty"]
        risk_factors.extend(suspicious_factors["factors"])

        # Determine status
        if compliance_score >= 0.8:
            status = DeviceStatus.COMPLIANT
        elif compliance_score >= 0.6:
            status = DeviceStatus.NON_COMPLIANT
        elif suspicious_factors["penalty"] > 0.3:
            status = DeviceStatus.SUSPICIOUS
        else:
            status = DeviceStatus.UNKNOWN

        posture = DevicePosture(
            device_id=device_info.device_id,
            status=status,
            compliance_score=max(0.0, min(1.0, compliance_score)),
            risk_factors=risk_factors,
            recommendations=recommendations,
        )

        self.device_postures[device_info.device_id] = posture
        logger.info(
            f"Device posture assessed: {status.value} "
            f"(score: {compliance_score:.2f})"
        )

        return posture

    async def _check_os_compliance(self, device_info: DeviceInfo) -> Dict[str, Any]:
        """Check OS version compliance."""
        # Simplified OS version checking
        device_os = device_info.device_type.lower()

        if device_os in self.compliance_rules["os_version"]:
            # In production, implement proper version comparison
            return {"compliant": True, "score": 0.3}
        else:
            return {"compliant": False, "score": 0.0}

    async def _check_browser_compliance(
        self, device_info: DeviceInfo
    ) -> Dict[str, Any]:
        """Check browser version compliance."""
        if not device_info.browser_version:
            return {"compliant": False, "score": 0.0}

        # Simplified browser version checking
        browser_name = device_info.browser_version.lower().split()[0]

        if browser_name in self.compliance_rules["browser_version"]:
            return {"compliant": True, "score": 0.2}
        else:
            return {"compliant": False, "score": 0.0}

    async def _check_security_features(self, device_info: DeviceInfo) -> Dict[str, Any]:
        """Check security features compliance."""
        score = 0.2
        risk_factors = []
        recommendations = []

        # Check for blocked plugins
        blocked_plugins = self.compliance_rules["security_features"]["blocked_plugins"]
        found_blocked = [
            plugin
            for plugin in device_info.plugins
            if plugin.lower() in blocked_plugins
        ]

        if found_blocked:
            score -= 0.1
            risk_factors.append(f"Blocked plugins detected: {', '.join(found_blocked)}")
            recommendations.append("Remove or disable blocked browser plugins")

        # Check for required certificates
        required_certs = self.compliance_rules["security_features"][
            "required_certificates"
        ]
        if required_certs:
            missing_certs = [
                cert for cert in required_certs if cert not in device_info.certificates
            ]
            if missing_certs:
                score -= 0.1
                risk_factors.append(
                    "Missing required certificates: " f"{', '.join(missing_certs)}"
                )
                recommendations.append("Install required security certificates")

        return {
            "compliant": score >= 0.1,
            "score": score,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
        }

    async def _check_suspicious_characteristics(
        self, device_info: DeviceInfo
    ) -> Dict[str, Any]:
        """Check for suspicious device characteristics."""
        penalty = 0.0
        factors = []

        # Check for suspicious user agent
        if (
            "bot" in device_info.user_agent.lower()
            or "crawler" in device_info.user_agent.lower()
        ):
            penalty += 0.2
            factors.append("Suspicious user agent detected")

        # Check for missing common headers
        if not device_info.screen_resolution:
            penalty += 0.1
            factors.append("Missing screen resolution information")

        # Check for unusual timezone
        unusual_timezones = ["UTC+14", "UTC-12"]
        if device_info.timezone in unusual_timezones:
            penalty += 0.1
            factors.append("Unusual timezone detected")

        return {"penalty": penalty, "factors": factors}
