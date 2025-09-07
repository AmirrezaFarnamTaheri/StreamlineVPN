"""
Identity Provider
================

Identity provider for user authentication with device context.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ...utils.logging import get_logger
from .models import UserIdentity, DeviceInfo

logger = get_logger(__name__)


class IdentityProvider:
    """Identity provider for user authentication."""

    def __init__(self):
        """Initialize identity provider."""
        self.users: Dict[str, UserIdentity] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)

    async def verify_credentials(
        self, username: str, password: str, device_info: DeviceInfo
    ) -> Optional[UserIdentity]:
        """Verify user credentials with device context.

        Args:
            username: Username
            password: Password
            device_info: Device information

        Returns:
            UserIdentity if valid, None otherwise
        """
        # Check for account lockout
        if await self._is_account_locked(username):
            logger.warning(f"Account locked for user {username}")
            return None

        # Verify credentials (simplified implementation)
        user = await self._authenticate_user(username, password)
        if not user:
            await self._record_failed_attempt(username)
            return None

        # Clear failed attempts on successful login
        if username in self.failed_attempts:
            del self.failed_attempts[username]

        # Update last verified time
        user.last_verified = datetime.now()
        self.users[user.user_id] = user

        logger.info(f"User {username} authenticated successfully")
        return user

    async def _authenticate_user(
        self, username: str, password: str
    ) -> Optional[UserIdentity]:
        """Authenticate user (simplified implementation)."""
        # In production, integrate with proper identity provider
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Demo users
        demo_users = {
            "admin": {
                "password_hash": hashlib.sha256(
                    "admin123".encode()
                ).hexdigest(),
                "email": "admin@streamlinevpn.com",
                "groups": ["administrators"],
                "roles": ["admin", "user"],
            },
            "user": {
                "password_hash": hashlib.sha256(
                    "user123".encode()
                ).hexdigest(),
                "email": "user@streamlinevpn.com",
                "groups": ["users"],
                "roles": ["user"],
            },
        }

        if username in demo_users:
            user_data = demo_users[username]
            if user_data["password_hash"] == password_hash:
                return UserIdentity(
                    user_id=f"user_{username}",
                    username=username,
                    email=user_data["email"],
                    groups=user_data["groups"],
                    roles=user_data["roles"],
                )

        return None

    async def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed attempts."""
        if username not in self.failed_attempts:
            return False

        failed_attempts = self.failed_attempts[username]
        recent_attempts = [
            attempt
            for attempt in failed_attempts
            if datetime.now() - attempt < self.lockout_duration
        ]

        if len(recent_attempts) >= self.max_failed_attempts:
            return True

        # Update failed attempts list
        self.failed_attempts[username] = recent_attempts
        return False

    async def _record_failed_attempt(self, username: str) -> None:
        """Record failed authentication attempt."""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []

        self.failed_attempts[username].append(datetime.now())
        logger.warning(f"Failed authentication attempt for user {username}")
