import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import asyncpg


class TenantTier(Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class TenantConfig:
    """Tenant-specific configuration"""

    max_users: int
    max_servers: int
    max_bandwidth_gbps: float
    allowed_protocols: list[str]
    allowed_regions: list[str]
    custom_domain: bool
    white_label: bool
    api_access: bool
    priority: int
    data_retention_days: int
    compliance_features: list[str]


@dataclass
class Tenant:
    """Multi-tenant organization"""

    id: str
    name: str
    domain: str
    tier: TenantTier
    config: TenantConfig
    created_at: datetime
    admin_email: str
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class MultiTenantManager:
    """Multi-tenant VPN infrastructure manager"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.db_pool = None

        # Tier configurations
        self.tier_configs = {
            TenantTier.FREE: TenantConfig(
                max_users=5,
                max_servers=1,
                max_bandwidth_gbps=0.1,
                allowed_protocols=["openvpn"],
                allowed_regions=["us-east"],
                custom_domain=False,
                white_label=False,
                api_access=False,
                priority=1,
                data_retention_days=7,
                compliance_features=[],
            ),
            TenantTier.STARTER: TenantConfig(
                max_users=50,
                max_servers=5,
                max_bandwidth_gbps=1.0,
                allowed_protocols=["openvpn", "wireguard"],
                allowed_regions=["us", "eu"],
                custom_domain=False,
                white_label=False,
                api_access=True,
                priority=5,
                data_retention_days=30,
                compliance_features=["basic-logging"],
            ),
            TenantTier.PROFESSIONAL: TenantConfig(
                max_users=500,
                max_servers=20,
                max_bandwidth_gbps=10.0,
                allowed_protocols=["openvpn", "wireguard", "ipsec", "sstp"],
                allowed_regions=["us", "eu", "asia", "australia"],
                custom_domain=True,
                white_label=False,
                api_access=True,
                priority=10,
                data_retention_days=90,
                compliance_features=["audit-logging", "gdpr", "hipaa"],
            ),
            TenantTier.ENTERPRISE: TenantConfig(
                max_users=99999,
                max_servers=999,
                max_bandwidth_gbps=100.0,
                allowed_protocols=["all"],
                allowed_regions=["all"],
                custom_domain=True,
                white_label=True,
                api_access=True,
                priority=20,
                data_retention_days=365,
                compliance_features=["all"],
            ),
        }

    async def initialize(self):
        """Initialize database connection"""
        self.db_pool = await asyncpg.create_pool(self.db_url)
        await self.create_schema()

    async def create_schema(self):
        """Create multi-tenant database schema"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tenants (
                    id UUID PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    domain VARCHAR(255) UNIQUE NOT NULL,
                    tier VARCHAR(50) NOT NULL,
                    config JSONB NOT NULL,
                    admin_email VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS tenant_users (
                    id UUID PRIMARY KEY,
                    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
                    username VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_login TIMESTAMP,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tenant_id, username)
                );
                
                CREATE TABLE IF NOT EXISTS tenant_servers (
                    id UUID PRIMARY KEY,
                    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    host VARCHAR(255) NOT NULL,
                    port INTEGER NOT NULL,
                    protocol VARCHAR(50) NOT NULL,
                    region VARCHAR(50) NOT NULL,
                    capacity INTEGER NOT NULL,
                    current_load INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    config JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS tenant_usage (
                    id UUID PRIMARY KEY,
                    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
                    user_id UUID REFERENCES tenant_users(id) ON DELETE CASCADE,
                    server_id UUID REFERENCES tenant_servers(id) ON DELETE CASCADE,
                    bytes_in BIGINT DEFAULT 0,
                    bytes_out BIGINT DEFAULT 0,
                    session_start TIMESTAMP NOT NULL,
                    session_end TIMESTAMP,
                    ip_address VARCHAR(45),
                    metadata JSONB DEFAULT '{}'
                );
                
                CREATE INDEX IF NOT EXISTS idx_tenant_usage_tenant_id ON tenant_usage(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_tenant_usage_user_id ON tenant_usage(user_id);
                CREATE INDEX IF NOT EXISTS idx_tenant_usage_session_start ON tenant_usage(session_start);
                """
            )

    async def create_tenant(
        self, name: str, domain: str, admin_email: str, tier: TenantTier = TenantTier.FREE
    ) -> Tenant:
        """Create new tenant"""

        tenant_id = str(uuid.uuid4())
        config = self.tier_configs[tier]

        tenant = Tenant(
            id=tenant_id,
            name=name,
            domain=domain,
            tier=tier,
            config=config,
            admin_email=admin_email,
            created_at=datetime.now(),
        )

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tenants (id, name, domain, tier, config, admin_email, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                tenant.id,
                tenant.name,
                tenant.domain,
                tenant.tier.value,
                json.dumps(self.config_to_dict(config)),
                tenant.admin_email,
                json.dumps(tenant.metadata),
            )

        # Initialize tenant resources
        await self.initialize_tenant_resources(tenant)

        return tenant

    async def initialize_tenant_resources(self, tenant: Tenant):
        """Initialize resources for new tenant"""

        # Create default admin user
        await self.create_tenant_user(
            tenant.id, username=f"admin@{tenant.domain}", email=tenant.admin_email, role="admin"
        )

        # Create default VPN server based on tier
        if tenant.tier != TenantTier.FREE:
            await self.provision_tenant_server(tenant)

        # Setup tenant-specific network policies
        await self.setup_network_policies(tenant)

        # Initialize monitoring
        await self.setup_tenant_monitoring(tenant)

    async def provision_tenant_server(self, tenant: Tenant):
        """Provision VPN server for tenant"""

        server_config = {
            "protocol": tenant.config.allowed_protocols[0],
            "region": tenant.config.allowed_regions[0],
            "capacity": self.calculate_server_capacity(tenant.tier),
            "bandwidth_limit": tenant.config.max_bandwidth_gbps,
            "encryption": "aes-256-gcm",
            "dns_servers": ["1.1.1.1", "8.8.8.8"],
        }

        # Deploy server (integrate with orchestration)
        server_info = await self.deploy_server(server_config)

        # Register server in database
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tenant_servers 
                (id, tenant_id, name, host, port, protocol, region, capacity, config)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                str(uuid.uuid4()),
                tenant.id,
                f"{tenant.name}-server-1",
                server_info["host"],
                server_info["port"],
                server_config["protocol"],
                server_config["region"],
                server_config["capacity"],
                json.dumps(server_config),
            )

    async def deploy_server(self, config: dict) -> dict:
        """Deploy VPN server (integrate with Kubernetes/Docker)"""

        # This would integrate with your orchestration system
        # For now, return mock server info
        return {"host": f"vpn-{uuid.uuid4().hex[:8]}.servers.local", "port": 443}

    def calculate_server_capacity(self, tier: TenantTier) -> int:
        """Calculate server capacity based on tier"""
        capacities = {
            TenantTier.FREE: 10,
            TenantTier.STARTER: 100,
            TenantTier.PROFESSIONAL: 1000,
            TenantTier.ENTERPRISE: 10000,
        }
        return capacities.get(tier, 10)

    async def setup_network_policies(self, tenant: Tenant):
        """Setup network isolation and policies"""

        # Create tenant-specific network namespace
        namespace = f"tenant-{tenant.id}"

        # Network policy configuration
        policy = {
            "namespace": namespace,
            "ingress_rules": self.generate_ingress_rules(tenant),
            "egress_rules": self.generate_egress_rules(tenant),
            "qos": {
                "bandwidth_limit": tenant.config.max_bandwidth_gbps,
                "priority": tenant.config.priority,
            },
        }

        # Apply network policies (integrate with SDN controller)
        await self.apply_network_policy(policy)

    def generate_ingress_rules(self, tenant: Tenant) -> list[dict]:
        """Generate ingress rules for tenant"""
        rules: list[dict] = []

        for protocol in tenant.config.allowed_protocols:
            port = self.get_protocol_port(protocol)
            rules.append({"protocol": "tcp", "port": port, "source": "0.0.0.0/0"})

        return rules

    def generate_egress_rules(self, tenant: Tenant) -> list[dict]:
        """Generate egress rules for tenant"""
        # Allow all egress by default, can be restricted
        return [{"destination": "0.0.0.0/0"}]

    def get_protocol_port(self, protocol: str) -> int:
        """Get default port for protocol"""
        ports = {"openvpn": 1194, "wireguard": 51820, "ipsec": 500, "sstp": 443, "l2tp": 1701}
        return ports.get(protocol, 443)

    async def apply_network_policy(self, policy: dict):
        """Apply network policy using SDN controller"""
        # Integration with SDN controller (OpenDaylight, ONOS, etc.)

    async def setup_tenant_monitoring(self, tenant: Tenant):
        """Setup monitoring for tenant"""

        # Create Prometheus namespace
        monitoring_config = {
            "tenant_id": tenant.id,
            "metrics": [
                "bandwidth_usage",
                "active_connections",
                "authentication_attempts",
                "error_rate",
            ],
            "retention": tenant.config.data_retention_days,
            "alerting": self.generate_alerting_rules(tenant),
        }

        # Deploy monitoring stack
        await self.deploy_monitoring(monitoring_config)

    def generate_alerting_rules(self, tenant: Tenant) -> list[dict]:
        """Generate alerting rules based on tier"""

        base_rules: list[dict] = [
            {"name": "high_error_rate", "condition": "error_rate > 0.05", "severity": "warning"},
            {
                "name": "bandwidth_limit",
                "condition": f"bandwidth_usage > {tenant.config.max_bandwidth_gbps * 0.9}",
                "severity": "warning",
            },
        ]

        if tenant.tier in [TenantTier.PROFESSIONAL, TenantTier.ENTERPRISE]:
            base_rules.extend(
                [
                    {
                        "name": "ddos_detection",
                        "condition": "connection_rate > 1000",
                        "severity": "critical",
                    },
                    {
                        "name": "compliance_violation",
                        "condition": "compliance_check_failed == true",
                        "severity": "critical",
                    },
                ]
            )

        return base_rules

    async def deploy_monitoring(self, config: dict):
        """Deploy monitoring stack for tenant"""
        # Integration with monitoring infrastructure

    async def create_tenant_user(
        self, tenant_id: str, username: str, email: str, role: str = "user"
    ) -> str:
        """Create user within tenant"""

        user_id = str(uuid.uuid4())

        async with self.db_pool.acquire() as conn:
            # Check tenant user limit
            user_count = await conn.fetchval(
                "SELECT COUNT(*) FROM tenant_users WHERE tenant_id = $1", tenant_id
            )

            tenant = await self.get_tenant(tenant_id)
            if user_count >= tenant.config.max_users:
                raise Exception("User limit exceeded for tenant")

            # Create user
            await conn.execute(
                """
                INSERT INTO tenant_users (id, tenant_id, username, email, role)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id,
                tenant_id,
                username,
                email,
                role,
            )

        return user_id

    async def get_tenant(self, tenant_id: str) -> Tenant:
        """Get tenant by ID"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM tenants WHERE id = $1", tenant_id)

            if not row:
                raise Exception("Tenant not found")

            return self.row_to_tenant(row)

    async def get_tenant_by_domain(self, domain: str) -> Tenant | None:
        """Get tenant by domain"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM tenants WHERE domain = $1", domain)

            if not row:
                return None

            return self.row_to_tenant(row)

    def row_to_tenant(self, row) -> Tenant:
        """Convert database row to Tenant object"""
        config_dict = json.loads(row["config"])
        config = TenantConfig(**config_dict)

        return Tenant(
            id=str(row["id"]),
            name=row["name"],
            domain=row["domain"],
            tier=TenantTier(row["tier"]),
            config=config,
            admin_email=row["admin_email"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata"]),
        )

    def config_to_dict(self, config: TenantConfig) -> dict:
        """Convert TenantConfig to dictionary"""
        return {
            "max_users": config.max_users,
            "max_servers": config.max_servers,
            "max_bandwidth_gbps": config.max_bandwidth_gbps,
            "allowed_protocols": config.allowed_protocols,
            "allowed_regions": config.allowed_regions,
            "custom_domain": config.custom_domain,
            "white_label": config.white_label,
            "api_access": config.api_access,
            "priority": config.priority,
            "data_retention_days": config.data_retention_days,
            "compliance_features": config.compliance_features,
        }

    async def track_usage(
        self, tenant_id: str, user_id: str, server_id: str, bytes_in: int, bytes_out: int
    ):
        """Track tenant resource usage"""

        async with self.db_pool.acquire() as conn:
            # Update or insert usage record
            await conn.execute(
                """
                INSERT INTO tenant_usage 
                (id, tenant_id, user_id, server_id, bytes_in, bytes_out, session_start)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                    bytes_in = tenant_usage.bytes_in + EXCLUDED.bytes_in,
                    bytes_out = tenant_usage.bytes_out + EXCLUDED.bytes_out
                """,
                str(uuid.uuid4()),
                tenant_id,
                user_id,
                server_id,
                bytes_in,
                bytes_out,
                datetime.now(),
            )

            # Check bandwidth limits
            await self.check_bandwidth_limits(tenant_id)

    async def check_bandwidth_limits(self, tenant_id: str):
        """Check and enforce bandwidth limits"""

        tenant = await self.get_tenant(tenant_id)

        async with self.db_pool.acquire() as conn:
            # Get current month's usage
            usage = await conn.fetchrow(
                """
                SELECT 
                    SUM(bytes_in + bytes_out) as total_bytes,
                    COUNT(DISTINCT user_id) as active_users,
                    COUNT(DISTINCT server_id) as active_servers
                FROM tenant_usage
                WHERE tenant_id = $1
                    AND session_start >= date_trunc('month', CURRENT_DATE)
                """,
                tenant_id,
            )

            total_gb = (usage["total_bytes"] or 0) / (1024**3)

            # Check limits based on tier
            if tenant.tier == TenantTier.FREE and total_gb > 100:
                # Suspend tenant
                await self.suspend_tenant(tenant_id, "Bandwidth limit exceeded")
            elif tenant.tier == TenantTier.STARTER and total_gb > 1000:
                # Send warning
                await self.send_limit_warning(tenant, "bandwidth", total_gb)

    async def suspend_tenant(self, tenant_id: str, reason: str):
        """Suspend tenant account"""

        async with self.db_pool.acquire() as conn:
            await conn.execute("UPDATE tenants SET is_active = FALSE WHERE id = $1", tenant_id)

            # Disconnect all active sessions
            await self.disconnect_tenant_sessions(tenant_id)

            # Send notification
            await self.notify_tenant_suspension(tenant_id, reason)

    async def disconnect_tenant_sessions(self, tenant_id: str):
        """Disconnect all active sessions for tenant"""
        # Integration with VPN servers to disconnect sessions

    async def notify_tenant_suspension(self, tenant_id: str, reason: str):
        """Notify tenant of suspension"""
        # Send email notification

    async def send_limit_warning(self, tenant: Tenant, limit_type: str, current_value: float):
        """Send limit warning to tenant"""
        # Send warning email
