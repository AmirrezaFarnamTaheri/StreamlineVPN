"""
Authentication Models
====================

Data models and enums for the Zero Trust authentication system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class ThreatLevel(Enum):
    """Threat level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DeviceStatus(Enum):
    """Device compliance status."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"
    SUSPICIOUS = "suspicious"


class PolicyAction(Enum):
    """Policy evaluation actions."""
    ALLOW = "allow"
    DENY = "deny"
    CHALLENGE = "challenge"
    QUARANTINE = "quarantine"


@dataclass
class DeviceInfo:
    """Device information for posture validation."""
    device_id: str
    device_type: str
    os_version: str
    browser_version: Optional[str]
    ip_address: str
    user_agent: str
    screen_resolution: Optional[str]
    timezone: str
    language: str
    plugins: List[str] = field(default_factory=list)
    certificates: List[str] = field(default_factory=list)
    last_seen: datetime = field(default_factory=datetime.now)


@dataclass
class DevicePosture:
    """Device posture assessment result."""
    device_id: str
    status: DeviceStatus
    compliance_score: float
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    last_assessed: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=1))


@dataclass
class UserIdentity:
    """User identity information."""
    user_id: str
    username: str
    email: str
    groups: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    last_verified: datetime = field(default_factory=datetime.now)


@dataclass
class PolicyRule:
    """Zero Trust policy rule."""
    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    action: PolicyAction
    priority: int
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PolicyEvaluation:
    """Policy evaluation result."""
    rule_id: str
    action: PolicyAction
    reason: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthResult:
    """Authentication result."""
    user_id: str
    session_id: str
    permissions: List[str]
    expires_at: datetime
    device_posture: DevicePosture
    policy_evaluations: List[PolicyEvaluation]
    threat_level: ThreatLevel
    continuous_auth_required: bool
