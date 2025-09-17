"""
Authentication Service
=====================

JWT-based authentication service for the API.
"""

import hashlib
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Optional

from ...utils.logging import get_logger
from .models import User, UserTier

logger = get_logger(__name__)


class AuthenticationService:
    """JWT-based authentication service."""

    def __init__(self, secret_key: str):
        """Initialize authentication service.

        Args:
            secret_key: JWT secret key
        """
        self.secret_key = secret_key
        self.users: Dict[str, User] = {}
        self._initialize_demo_users()

    def _initialize_demo_users(self) -> None:
        """Initialize demo users."""
        # In production, these should be loaded from a secure database
        # with properly hashed passwords
        self.users["user_admin"] = User(
            id="user_admin",
            username="admin",
            email="admin@streamlinevpn.com",
            tier=UserTier.ENTERPRISE,
            created_at=datetime.now(),
            last_login=datetime.now(),
        )

        self.users["user_user"] = User(
            id="user_user",
            username="user",
            email="user@streamlinevpn.com",
            tier=UserTier.PREMIUM,
            created_at=datetime.now(),
            last_login=datetime.now(),
        )

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with credentials.

        Args:
            username: Username
            password: Password

        Returns:
            User if authentication successful, None otherwise
        """
        # WARNING: This is for demo purposes only!
        # In production, use proper password hashing (bcrypt, scrypt, etc.)
        # and store credentials in a secure database
        demo_users = {
            "admin": {
                "password_hash": bcrypt.hashpw(
                    "admin123".encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8"),
                "email": "admin@streamlinevpn.com",
                "tier": UserTier.ENTERPRISE,
            },
            "user": {
                "password_hash": bcrypt.hashpw(
                    "user123".encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8"),
                "email": "user@streamlinevpn.com",
                "tier": UserTier.PREMIUM,
            },
        }

        if username in demo_users:
            user_data = demo_users[username]
            stored_hash = user_data["password_hash"].encode("utf-8")
            if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
                return User(
                    id=f"user_{username}",
                    username=username,
                    email=user_data["email"],
                    tier=user_data["tier"],
                    created_at=datetime.now(),
                    last_login=datetime.now(),
                )

        return None

    def generate_access_token(self, user: User) -> str:
        """Generate JWT access token.

        Args:
            user: User object

        Returns:
            JWT access token
        """
        payload = {
            "sub": user.id,
            "username": user.username,
            "tier": user.tier.value,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def generate_refresh_token(self, user: User) -> str:
        """Generate JWT refresh token.

        Args:
            user: User object

        Returns:
            JWT refresh token
        """
        payload = {
            "sub": user.id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=7),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[User]:
        """Verify JWT token and return user.

        Args:
            token: JWT token

        Returns:
            User if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            user_id = payload.get("sub")

            if user_id in self.users:
                return self.users[user_id]

            return None

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New access token if valid, None otherwise
        """
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=["HS256"])
            user_id = payload.get("sub")

            if user_id in self.users:
                user = self.users[user_id]
                return self.generate_access_token(user)

            return None

        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid refresh token")
            return None
