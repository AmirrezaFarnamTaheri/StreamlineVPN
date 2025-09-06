"""
Configuration Validator
=======================

Handles validation of VPN configurations.
"""

import re
import ipaddress
from typing import List, Dict, Any, Optional, Tuple

from ...models.configuration import VPNConfiguration, Protocol
from ...utils.logging import get_logger

logger = get_logger(__name__)


class ConfigurationValidator:
    """Validates VPN configurations."""

    def __init__(self):
        """Initialize validator."""
        self.port_range = (1, 65535)
        self.valid_protocols = [p.value for p in Protocol]

    def validate_configuration(
        self, config: VPNConfiguration, rules: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]:
        """Validate a VPN configuration.

        Args:
            config: VPN configuration to validate
            rules: Optional validation rules

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Basic validation
        if not self._validate_basic_fields(config, errors):
            return False, errors

        # Protocol-specific validation
        if not self._validate_protocol_specific(config, errors):
            return False, errors

        # Custom rules validation
        if rules and not self._validate_custom_rules(config, rules, errors):
            return False, errors

        return len(errors) == 0, errors

    def _validate_basic_fields(
        self, config: VPNConfiguration, errors: List[str]
    ) -> bool:
        """Validate basic configuration fields.

        Args:
            config: Configuration to validate
            errors: List to append errors to

        Returns:
            True if valid
        """
        valid = True

        # Validate protocol
        if (
            not config.protocol
            or config.protocol.value not in self.valid_protocols
        ):
            errors.append(f"Invalid protocol: {config.protocol}")
            valid = False

        # Validate server
        if not config.server or not self._is_valid_server(config.server):
            errors.append(f"Invalid server: {config.server}")
            valid = False

        # Validate port
        if not self._is_valid_port(config.port):
            errors.append(f"Invalid port: {config.port}")
            valid = False

        return valid

    def _validate_protocol_specific(
        self, config: VPNConfiguration, errors: List[str]
    ) -> bool:
        """Validate protocol-specific fields.

        Args:
            config: Configuration to validate
            errors: List to append errors to

        Returns:
            True if valid
        """
        valid = True

        if config.protocol == Protocol.VMESS:
            if not config.user_id:
                errors.append("VMess requires user_id")
                valid = False

        elif config.protocol == Protocol.VLESS:
            if not config.user_id:
                errors.append("VLESS requires user_id")
                valid = False

        elif config.protocol in [
            Protocol.TROJAN,
            Protocol.SHADOWSOCKS,
            Protocol.SHADOWSOCKSR,
        ]:
            if not config.password:
                errors.append(f"{config.protocol.value} requires password")
                valid = False

        return valid

    def _validate_custom_rules(
        self,
        config: VPNConfiguration,
        rules: Dict[str, Any],
        errors: List[str],
    ) -> bool:
        """Validate against custom rules."""
        valid = True

        # Check minimum quality score
        min_quality = rules.get("min_quality_score", 0)
        if (
            config.quality_score is not None
            and config.quality_score < min_quality
        ):
            errors.append(
                f"Quality score {config.quality_score} below minimum {min_quality}"
            )
            valid = False

        # Check allowed protocols
        allowed_protocols = rules.get("allowed_protocols", [])
        if (
            allowed_protocols
            and config.protocol.value not in allowed_protocols
        ):
            errors.append(
                f"Protocol {config.protocol.value} not in allowed list"
            )
            valid = False

        # Check server whitelist/blacklist
        server_whitelist = rules.get("server_whitelist", [])
        if server_whitelist and config.server not in server_whitelist:
            errors.append(f"Server {config.server} not in whitelist")
            valid = False

        server_blacklist = rules.get("server_blacklist", [])
        if server_blacklist and config.server in server_blacklist:
            errors.append(f"Server {config.server} is blacklisted")
            valid = False

        return valid

    def _is_valid_server(self, server: str) -> bool:
        """Check if server is valid.

        Args:
            server: Server address to validate

        Returns:
            True if valid
        """
        if not server:
            return False

        # Check if it's a valid IP address
        try:
            ipaddress.ip_address(server)
            return True
        except ValueError:
            pass

        # Check if it's a valid domain name
        if self._is_valid_domain(server):
            return True

        return False

    def _is_valid_domain(self, domain: str) -> bool:
        """Check if domain is valid.

        Args:
            domain: Domain name to validate

        Returns:
            True if valid
        """
        if not domain:
            return False

        # Basic domain validation
        if len(domain) > 253:
            return False

        # Check for valid characters
        if not re.match(r"^[a-zA-Z0-9.-]+$", domain):
            return False

        # Check for valid structure
        parts = domain.split(".")
        if len(parts) < 2:
            return False

        for part in parts:
            if not part or len(part) > 63:
                return False
            if part.startswith("-") or part.endswith("-"):
                return False

        return True

    def _is_valid_port(self, port: int) -> bool:
        """Check if port is valid.

        Args:
            port: Port number to validate

        Returns:
            True if valid
        """
        return (
            isinstance(port, int)
            and self.port_range[0] <= port <= self.port_range[1]
        )

    def validate_configurations(
        self,
        configs: List[VPNConfiguration],
        rules: Optional[Dict[str, Any]] = None,
    ) -> List[VPNConfiguration]:
        """Validate a list of configurations."""
        valid_configs = []

        for config in configs:
            is_valid, errors = self.validate_configuration(config, rules)
            if is_valid:
                valid_configs.append(config)
            else:
                logger.debug(
                    f"Invalid configuration {config.id}: {', '.join(errors)}"
                )

        logger.info(
            f"Validated {len(configs)} configurations, {len(valid_configs)} valid"
        )
        return valid_configs
