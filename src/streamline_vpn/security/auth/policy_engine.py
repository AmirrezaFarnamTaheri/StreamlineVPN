"""
Policy Engine
============

Zero Trust policy evaluation engine.
"""

from typing import Dict, List

from ...utils.logging import get_logger
from .models import (
    PolicyRule,
    PolicyEvaluation,
    PolicyAction,
    UserIdentity,
    DevicePosture,
    ThreatLevel,
)

logger = get_logger(__name__)


class PolicyEngine:
    """Zero Trust policy evaluation engine."""

    def __init__(self):
        """Initialize policy engine."""
        self.policies: Dict[str, PolicyRule] = {}
        self._initialize_default_policies()

    def _initialize_default_policies(self) -> None:
        """Initialize default Zero Trust policies."""
        default_policies = [
            PolicyRule(
                rule_id="admin_access",
                name="Administrator Access",
                description="Allow admin access only from compliant devices",
                conditions={
                    "user_roles": ["admin"],
                    "device_status": ["compliant"],
                    "threat_level": ["low", "medium"],
                },
                action=PolicyAction.ALLOW,
                priority=1,
            ),
            PolicyRule(
                rule_id="user_access",
                name="Standard User Access",
                description="Allow user access with device compliance check",
                conditions={
                    "user_roles": ["user"],
                    "device_status": ["compliant", "non_compliant"],
                    "threat_level": ["low", "medium"],
                },
                action=PolicyAction.ALLOW,
                priority=2,
            ),
            PolicyRule(
                rule_id="suspicious_device",
                name="Suspicious Device Quarantine",
                description="Quarantine suspicious devices",
                conditions={
                    "device_status": ["suspicious"],
                    "threat_level": ["high", "critical"],
                },
                action=PolicyAction.QUARANTINE,
                priority=3,
            ),
            PolicyRule(
                rule_id="high_threat",
                name="High Threat Denial",
                description="Deny access for high threat levels",
                conditions={"threat_level": ["critical"]},
                action=PolicyAction.DENY,
                priority=4,
            ),
        ]

        for policy in default_policies:
            self.policies[policy.rule_id] = policy

    async def evaluate_policies(
        self,
        user_identity: UserIdentity,
        device_posture: DevicePosture,
        threat_level: ThreatLevel,
        resource: str,
    ) -> List[PolicyEvaluation]:
        """Evaluate policies for access decision.

        Args:
            user_identity: User identity
            device_posture: Device posture
            threat_level: Current threat level
            resource: Resource being accessed

        Returns:
            List of policy evaluations
        """
        evaluations = []

        # Sort policies by priority
        sorted_policies = sorted(
            self.policies.values(), key=lambda x: x.priority
        )

        for policy in sorted_policies:
            if not policy.enabled:
                continue

            evaluation = await self._evaluate_policy(
                policy, user_identity, device_posture, threat_level, resource
            )
            evaluations.append(evaluation)

            # Stop evaluation if policy denies access
            if evaluation.action == PolicyAction.DENY:
                break

        return evaluations

    async def _evaluate_policy(
        self,
        policy: PolicyRule,
        user_identity: UserIdentity,
        device_posture: DevicePosture,
        threat_level: ThreatLevel,
        resource: str,
    ) -> PolicyEvaluation:
        """Evaluate a single policy rule."""
        conditions = policy.conditions
        matched_conditions = 0
        total_conditions = len(conditions)

        # Check user roles
        if "user_roles" in conditions:
            if any(
                role in user_identity.roles
                for role in conditions["user_roles"]
            ):
                matched_conditions += 1

        # Check device status
        if "device_status" in conditions:
            if device_posture.status.value in conditions["device_status"]:
                matched_conditions += 1

        # Check threat level
        if "threat_level" in conditions:
            if threat_level.value in conditions["threat_level"]:
                matched_conditions += 1

        # Calculate confidence
        confidence = (
            matched_conditions / total_conditions
            if total_conditions > 0
            else 0.0
        )

        # Determine action
        if confidence >= 0.8:
            action = policy.action
            reason = f"Policy '{policy.name}' matched with {confidence:.1%} confidence"
        else:
            action = PolicyAction.DENY
            reason = f"Policy '{policy.name}' did not match conditions"

        return PolicyEvaluation(
            rule_id=policy.rule_id,
            action=action,
            reason=reason,
            confidence=confidence,
            metadata={
                "matched_conditions": matched_conditions,
                "total_conditions": total_conditions,
                "resource": resource,
            },
        )
