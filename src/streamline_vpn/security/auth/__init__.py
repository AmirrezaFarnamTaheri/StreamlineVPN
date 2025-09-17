"""
Authentication Module
====================

Zero Trust authentication and authorization system with continuous monitoring.
"""

# Import moved to avoid circular dependencies
# from .models import (
#     ThreatLevel,
#     DeviceStatus,
#     PolicyAction,
#     DeviceInfo,
#     DevicePosture,
#     UserIdentity,
#     PolicyRule,
#     PolicyEvaluation,
#     AuthResult,
# )
# from .identity_provider import IdentityProvider
# from .device_validator import DeviceValidator
# from .policy_engine import PolicyEngine
# from .continuous_auth import ContinuousAuthenticator
# from .threat_analyzer import ThreatAnalyzer
# from .zero_trust import ZeroTrustVPN

# Global instances
_zero_trust_instance = None


def initialize_zero_trust():
    """Initialize Zero Trust VPN instance."""
    global _zero_trust_instance
    if _zero_trust_instance is None:
        from .zero_trust import ZeroTrustVPN

        _zero_trust_instance = ZeroTrustVPN()
    return _zero_trust_instance


def get_zero_trust():
    """Get Zero Trust VPN instance."""
    if _zero_trust_instance is None:
        return initialize_zero_trust()
    return _zero_trust_instance


__all__ = [
    "ThreatLevel",
    "DeviceStatus",
    "PolicyAction",
    "DeviceInfo",
    "DevicePosture",
    "UserIdentity",
    "PolicyRule",
    "PolicyEvaluation",
    "AuthResult",
    "IdentityProvider",
    "DeviceValidator",
    "PolicyEngine",
    "ContinuousAuthenticator",
    "ThreatAnalyzer",
    "initialize_zero_trust",
    "get_zero_trust",
]
