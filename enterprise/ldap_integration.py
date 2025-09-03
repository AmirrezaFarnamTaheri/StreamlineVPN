import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

import jwt
import redis
from cryptography.fernet import Fernet
from ldap3 import ALL, NTLM, SASL, Connection, Server
from ldap3.core.exceptions import LDAPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    username: str
    email: str
    full_name: str
    department: str
    groups: list[str]
    permissions: dict[str, bool]
    vpn_profiles: list[str]
    mfa_enabled: bool
    last_login: datetime | None
    session_token: str | None


class EnterpriseAuthManager:
    """Enterprise authentication and authorization manager"""

    def __init__(
        self,
        ldap_server: str,
        ldap_port: int = 389,
        base_dn: str = "",
        use_ssl: bool = True,
        redis_url: str = "redis://localhost:6379",
    ):
        self.ldap_server = Server(ldap_server, port=ldap_port, use_ssl=use_ssl, get_info=ALL)
        self.base_dn = base_dn
        self.redis_client = redis.from_url(redis_url)
        self.jwt_secret = secrets.token_hex(32)
        self.encryption_key = Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)

        # VPN access policies
        self.access_policies = {
            "admin": {
                "max_bandwidth": "unlimited",
                "allowed_protocols": ["all"],
                "allowed_regions": ["all"],
                "priority": 10,
                "session_limit": 10,
            },
            "developer": {
                "max_bandwidth": 1000,  # Mbps
                "allowed_protocols": ["wireguard", "openvpn", "ipsec"],
                "allowed_regions": ["us", "eu", "asia"],
                "priority": 7,
                "session_limit": 5,
            },
            "employee": {
                "max_bandwidth": 100,
                "allowed_protocols": ["wireguard", "openvpn"],
                "allowed_regions": ["us", "eu"],
                "priority": 5,
                "session_limit": 2,
            },
            "guest": {
                "max_bandwidth": 10,
                "allowed_protocols": ["openvpn"],
                "allowed_regions": ["us"],
                "priority": 1,
                "session_limit": 1,
            },
        }

    async def authenticate_user(
        self, username: str, password: str, mfa_token: str | None = None
    ) -> UserProfile | None:
        """Authenticate user against LDAP/AD"""

        try:
            # Bind with user credentials
            user_dn = f"uid={username},{self.base_dn}"

            conn = Connection(
                self.ldap_server,
                user=user_dn,
                password=password,
                authentication=NTLM if self.is_active_directory() else SASL,
            )

            if not conn.bind():
                logger.warning(f"Authentication failed for user: {username}")
                return None

            # Search for user attributes
            search_filter = f"(uid={username})"
            conn.search(
                self.base_dn,
                search_filter,
                attributes=[
                    "cn",
                    "mail",
                    "department",
                    "memberOf",
                    "accountStatus",
                    "vpnAccess",
                    "lastLogon",
                ],
            )

            if not conn.entries:
                return None

            user_entry = conn.entries[0]

            # Extract user groups
            groups = self.extract_groups(user_entry.memberOf)

            # Determine VPN access level
            vpn_access_level = self.determine_access_level(groups)

            # Check MFA if required
            if self.is_mfa_required(vpn_access_level) and mfa_token:
                if not await self.verify_mfa(username, mfa_token):
                    logger.warning(f"MFA verification failed for user: {username}")
                    return None

            # Create user profile
            profile = UserProfile(
                username=username,
                email=str(user_entry.mail),
                full_name=str(user_entry.cn),
                department=str(user_entry.department),
                groups=groups,
                permissions=self.get_permissions(vpn_access_level),
                vpn_profiles=self.get_vpn_profiles(vpn_access_level),
                mfa_enabled=self.is_mfa_required(vpn_access_level),
                last_login=datetime.now(),
                session_token=None,
            )

            # Generate session token
            profile.session_token = self.generate_session_token(profile)

            # Cache user session
            await self.cache_user_session(profile)

            # Log authentication
            await self.log_authentication(username, True)

            conn.unbind()
            return profile

        except LDAPException as e:
            logger.error(f"LDAP error during authentication: {e}")
            await self.log_authentication(username, False, str(e))
            return None

    def is_active_directory(self) -> bool:
        """Check if LDAP server is Active Directory"""
        return "dc=" in self.base_dn.lower()

    def extract_groups(self, member_of: list[str]) -> list[str]:
        """Extract group names from memberOf attributes"""
        groups: list[str] = []
        for dn in member_of:
            # Extract CN from DN
            parts = str(dn).split(",")
            for part in parts:
                if part.startswith("CN="):
                    groups.append(part[3:])
                    break
        return groups

    def determine_access_level(self, groups: list[str]) -> str:
        """Determine VPN access level based on groups"""
        if "VPN-Admins" in groups or "Domain Admins" in groups:
            return "admin"
        elif "VPN-Developers" in groups or "Developers" in groups:
            return "developer"
        elif "VPN-Users" in groups or "Employees" in groups:
            return "employee"
        else:
            return "guest"

    def get_permissions(self, access_level: str) -> dict[str, bool]:
        """Get permissions for access level"""
        permissions: dict[str, bool] = {
            "can_create_server": False,
            "can_modify_config": False,
            "can_view_logs": False,
            "can_manage_users": False,
            "can_access_premium": False,
            "can_use_api": False,
        }

        if access_level == "admin":
            return dict.fromkeys(permissions.keys(), True)
        elif access_level == "developer":
            permissions["can_modify_config"] = True
            permissions["can_view_logs"] = True
            permissions["can_access_premium"] = True
            permissions["can_use_api"] = True
        elif access_level == "employee":
            permissions["can_view_logs"] = True
            permissions["can_use_api"] = True

        return permissions

    def get_vpn_profiles(self, access_level: str) -> list[str]:
        """Get available VPN profiles for access level"""
        profiles: dict[str, list[str]] = {
            "admin": ["enterprise-unlimited", "developer-high", "standard", "mobile"],
            "developer": ["developer-high", "standard", "mobile"],
            "employee": ["standard", "mobile"],
            "guest": ["guest-limited"],
        }
        return profiles.get(access_level, ["guest-limited"])

    def is_mfa_required(self, access_level: str) -> bool:
        """Check if MFA is required for access level"""
        return access_level in ["admin", "developer"]

    async def verify_mfa(self, username: str, token: str) -> bool:
        """Verify MFA token"""
        # Get stored secret from secure storage
        secret_key = await self.get_mfa_secret(username)
        if not secret_key:
            return False

        # Verify TOTP token
        import pyotp

        totp = pyotp.TOTP(secret_key)

        return totp.verify(token, valid_window=1)

    async def get_mfa_secret(self, username: str) -> str | None:
        """Get MFA secret for user"""
        encrypted_secret = self.redis_client.get(f"mfa:{username}")
        if encrypted_secret:
            return self.fernet.decrypt(encrypted_secret).decode()
        return None

    def generate_session_token(self, profile: UserProfile) -> str:
        """Generate JWT session token"""
        payload = {
            "username": profile.username,
            "email": profile.email,
            "groups": profile.groups,
            "permissions": profile.permissions,
            "vpn_profiles": profile.vpn_profiles,
            "exp": datetime.utcnow() + timedelta(hours=8),
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    async def cache_user_session(self, profile: UserProfile):
        """Cache user session in Redis"""
        session_data = {
            "username": profile.username,
            "email": profile.email,
            "groups": profile.groups,
            "permissions": profile.permissions,
            "vpn_profiles": profile.vpn_profiles,
            "last_login": profile.last_login.isoformat() if profile.last_login else None,
        }

        # Store session with TTL
        self.redis_client.setex(f"session:{profile.username}", 28800, json.dumps(session_data))

    async def log_authentication(self, username: str, success: bool, error: str | None = None):
        """Log authentication attempt"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "success": success,
            "error": error,
            "ip_address": await self.get_client_ip(),
        }

        # Store in Redis list
        self.redis_client.lpush("auth_logs", json.dumps(log_entry))

        # Trim to keep only last 10000 entries
        self.redis_client.ltrim("auth_logs", 0, 9999)

    async def get_client_ip(self) -> str:
        """Get client IP address"""
        # In production, get from request context
        return "0.0.0.0"


# SAML 2.0 Integration
class SAML2Provider:
    """SAML 2.0 authentication provider"""

    def __init__(self, idp_metadata_url: str, sp_entity_id: str, sp_acs_url: str):
        from saml2 import BINDING_HTTP_POST
        from saml2.client import Saml2Client
        from saml2.config import Config as Saml2Config

        self.settings = {
            "metadata": {
                "remote": [
                    {
                        "url": idp_metadata_url,
                    }
                ]
            },
            "service": {
                "sp": {
                    "endpoints": {"assertion_consumer_service": [(sp_acs_url, BINDING_HTTP_POST)]},
                    "allow_unsolicited": False,
                    "authn_requests_signed": False,
                    "logout_requests_signed": True,
                    "want_assertions_signed": True,
                    "want_response_signed": True,
                }
            },
            "entityid": sp_entity_id,
            "debug": False,
            "key_file": "keys/sp.key",
            "cert_file": "certs/sp.crt",
        }

        saml_config = Saml2Config()
        saml_config.load(self.settings)
        self.client = Saml2Client(config=saml_config)

    def create_auth_request(self, relay_state: str = "") -> tuple[str, str]:
        """Create SAML authentication request"""
        session_id, info = self.client.prepare_for_authenticate(relay_state=relay_state)

        redirect_url = None
        for key, value in info.items():
            if isinstance(value, list):
                redirect_url = value[0]
                break

        return session_id, redirect_url

    def process_auth_response(self, saml_response: str) -> dict | None:
        """Process SAML authentication response"""
        try:
            authn_response = self.client.parse_authn_request_response(
                saml_response, BINDING_HTTP_POST
            )

            if authn_response:
                user_info = {
                    "username": authn_response.get_subject().text,
                    "attributes": authn_response.get_identity(),
                    "session_id": authn_response.session_id(),
                }
                return user_info

        except Exception as e:
            logger.error(f"SAML response processing error: {e}")

        return None
