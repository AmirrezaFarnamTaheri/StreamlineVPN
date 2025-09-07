"""
Continuous Authenticator
========================

Continuous authentication and monitoring service.
"""

import time
from datetime import datetime
from typing import Dict, Any

from ...utils.logging import get_logger
from .models import UserIdentity, DevicePosture, ThreatLevel

logger = get_logger(__name__)


class ContinuousAuthenticator:
    """Continuous authentication and monitoring service."""

    def __init__(self):
        """Initialize continuous authenticator."""
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.behavioral_profiles: Dict[str, Dict[str, Any]] = {}
        self.anomaly_threshold = 0.7

    async def start_session(
        self, user_identity: UserIdentity, device_posture: DevicePosture
    ) -> str:
        """Start continuous authentication session.

        Args:
            user_identity: User identity
            device_posture: Device posture

        Returns:
            Session ID
        """
        session_id = f"session_{user_identity.user_id}_{int(time.time())}"

        session_data = {
            "user_id": user_identity.user_id,
            "device_id": device_posture.device_id,
            "started_at": datetime.now(),
            "last_activity": datetime.now(),
            "activity_count": 0,
            "risk_score": 0.0,
            "threat_level": ThreatLevel.LOW,
            "is_active": True,
        }

        self.active_sessions[session_id] = session_data

        # Initialize behavioral profile
        await self._initialize_behavioral_profile(user_identity.user_id)

        logger.info(
            f"Started continuous auth session {session_id} for user "
            f"{user_identity.user_id}"
        )
        return session_id

    async def monitor_session(
        self, session_id: str, activity_data: Dict[str, Any]
    ) -> ThreatLevel:
        """Monitor session for anomalies.

        Args:
            session_id: Session ID
            activity_data: Activity data

        Returns:
            Updated threat level
        """
        if session_id not in self.active_sessions:
            return ThreatLevel.CRITICAL

        session = self.active_sessions[session_id]
        user_id = session["user_id"]

        # Update session activity
        session["last_activity"] = datetime.now()
        session["activity_count"] += 1

        # Analyze behavior
        anomaly_score = await self._analyze_behavior(user_id, activity_data)
        session["risk_score"] = anomaly_score

        # Update threat level
        if anomaly_score >= 0.8:
            threat_level = ThreatLevel.CRITICAL
        elif anomaly_score >= 0.6:
            threat_level = ThreatLevel.HIGH
        elif anomaly_score >= 0.4:
            threat_level = ThreatLevel.MEDIUM
        else:
            threat_level = ThreatLevel.LOW

        session["threat_level"] = threat_level

        # Check for session termination
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            await self._terminate_session(
                session_id, "High threat level detected"
            )

        return threat_level

    async def _initialize_behavioral_profile(self, user_id: str) -> None:
        """Initialize behavioral profile for user."""
        if user_id not in self.behavioral_profiles:
            self.behavioral_profiles[user_id] = {
                "login_times": [],
                "ip_addresses": [],
                "user_agents": [],
                "activity_patterns": {},
                "created_at": datetime.now(),
            }

    async def _analyze_behavior(
        self, user_id: str, activity_data: Dict[str, Any]
    ) -> float:
        """Analyze user behavior for anomalies."""
        if user_id not in self.behavioral_profiles:
            return 0.0

        profile = self.behavioral_profiles[user_id]
        anomaly_score = 0.0

        # Check IP address anomalies
        current_ip = activity_data.get("ip_address")
        if current_ip and current_ip not in profile["ip_addresses"]:
            anomaly_score += 0.3
            profile["ip_addresses"].append(current_ip)

        # Check user agent anomalies
        current_ua = activity_data.get("user_agent")
        if current_ua and current_ua not in profile["user_agents"]:
            anomaly_score += 0.2
            profile["user_agents"].append(current_ua)

        # Check time-based anomalies
        current_time = datetime.now()
        login_times = profile["login_times"]
        if len(login_times) > 0:
            avg_hour = sum(t.hour for t in login_times) / len(login_times)
            if abs(current_time.hour - avg_hour) > 6:
                anomaly_score += 0.2

        login_times.append(current_time)

        return min(1.0, anomaly_score)

    async def _terminate_session(self, session_id: str, reason: str) -> None:
        """Terminate session due to security concerns."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["is_active"] = False
            logger.warning(f"Terminated session {session_id}: {reason}")
