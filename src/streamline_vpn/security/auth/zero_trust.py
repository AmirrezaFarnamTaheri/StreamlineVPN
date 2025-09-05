"""
Zero Trust VPN
=============

Main Zero Trust VPN authentication system.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ...utils.logging import get_logger
from .models import (
    DeviceInfo, AuthResult, PolicyAction, ThreatLevel
)
from .identity_provider import IdentityProvider
from .device_validator import DeviceValidator
from .policy_engine import PolicyEngine
from .continuous_auth import ContinuousAuthenticator
from .threat_analyzer import ThreatAnalyzer

logger = get_logger(__name__)


class ZeroTrustVPN:
    """Main Zero Trust VPN authentication system."""
    
    def __init__(self):
        """Initialize Zero Trust VPN system."""
        self.identity_provider = IdentityProvider()
        self.device_validator = DeviceValidator()
        self.policy_engine = PolicyEngine()
        self.continuous_auth = ContinuousAuthenticator()
        self.threat_analyzer = ThreatAnalyzer()
    
    async def authenticate_connection(
        self, 
        credentials: Dict[str, str], 
        device_info: DeviceInfo,
        resource: str = "vpn_access"
    ) -> AuthResult:
        """Authenticate VPN connection with Zero Trust principles.
        
        Args:
            credentials: User credentials
            device_info: Device information
            resource: Resource being accessed
            
        Returns:
            Authentication result
        """
        # Step 1: Verify user identity
        user_identity = await self.identity_provider.verify_credentials(
            credentials["username"], 
            credentials["password"], 
            device_info
        )
        
        if not user_identity:
            raise Exception("Authentication failed")
        
        # Step 2: Validate device posture
        device_posture = await self.device_validator.check_posture(device_info)
        
        # Step 3: Assess threat level
        threat_level = await self.threat_analyzer.assess_threat_level(
            user_identity, device_info, device_posture
        )
        
        # Step 4: Evaluate policies
        policy_evaluations = await self.policy_engine.evaluate_policies(
            user_identity, device_posture, threat_level, resource
        )
        
        # Step 5: Determine final decision
        final_action = self._determine_final_action(policy_evaluations)
        
        if final_action == PolicyAction.DENY:
            raise Exception("Access denied by policy")
        
        # Step 6: Start continuous authentication session
        session_id = await self.continuous_auth.start_session(user_identity, device_posture)
        
        # Step 7: Generate permissions
        permissions = self._generate_permissions(user_identity, device_posture, threat_level)
        
        # Step 8: Set session expiration
        expires_at = datetime.now() + timedelta(hours=8)
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            expires_at = datetime.now() + timedelta(hours=1)
        
        return AuthResult(
            user_id=user_identity.user_id,
            session_id=session_id,
            permissions=permissions,
            expires_at=expires_at,
            device_posture=device_posture,
            policy_evaluations=policy_evaluations,
            threat_level=threat_level,
            continuous_auth_required=threat_level in [ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        )
    
    def _determine_final_action(self, policy_evaluations: List) -> PolicyAction:
        """Determine final action from policy evaluations."""
        # Prioritize DENY and QUARANTINE actions
        for evaluation in policy_evaluations:
            if evaluation.action in [PolicyAction.DENY, PolicyAction.QUARANTINE]:
                return evaluation.action
        
        # Check for ALLOW actions
        for evaluation in policy_evaluations:
            if evaluation.action == PolicyAction.ALLOW:
                return evaluation.action
        
        # Default to DENY
        return PolicyAction.DENY
    
    def _generate_permissions(self, user_identity, device_posture, threat_level: ThreatLevel) -> List[str]:
        """Generate permissions based on user, device, and threat level."""
        permissions = ["vpn_connect"]
        
        # Add role-based permissions
        if "admin" in user_identity.roles:
            permissions.extend(["admin_access", "user_management", "server_management"])
        
        if "user" in user_identity.roles:
            permissions.extend(["server_list", "connection_history"])
        
        # Restrict permissions based on device posture
        if device_posture.status.value == "non_compliant":
            permissions = [p for p in permissions if p not in ["admin_access", "user_management"]]
        
        # Restrict permissions based on threat level
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            permissions = ["vpn_connect"]  # Minimal permissions only
        
        return permissions


# Global Zero Trust instance
_zero_trust_vpn: Optional[ZeroTrustVPN] = None


def initialize_zero_trust() -> ZeroTrustVPN:
    """Initialize global Zero Trust VPN system."""
    global _zero_trust_vpn
    _zero_trust_vpn = ZeroTrustVPN()
    return _zero_trust_vpn


def get_zero_trust() -> Optional[ZeroTrustVPN]:
    """Get global Zero Trust VPN instance."""
    return _zero_trust_vpn
