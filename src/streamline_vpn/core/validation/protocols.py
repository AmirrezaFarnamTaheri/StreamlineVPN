from typing import Any, Dict, List

from ...models.configuration import Protocol

class ProtocolValidator:
    """Validator for protocol-specific configurations."""

    def validate(self, config: Dict[str, Any], protocol: Protocol) -> List[str]:
        """Validate a protocol-specific configuration."""
        errors = []
        if protocol == Protocol.VMESS:
            self._validate_vmess(config, errors)
        elif protocol == Protocol.VLESS:
            self._validate_vless(config, errors)
        elif protocol == Protocol.TROJAN:
            self._validate_trojan(config, errors)
        elif protocol == Protocol.SHADOWSOCKS:
            self._validate_shadowsocks(config, errors)
        elif protocol == Protocol.SHADOWSOCKSR:
            self._validate_shadowsocksr(config, errors)
        return errors

    def _validate_vmess(self, config: Dict[str, Any], errors: List[str]):
        required_fields = ["server", "port"]
        for field in required_fields:
            if field not in config:
                errors.append(f"VMess config missing required field: {field}")
        if "user_id" not in config and "uuid" not in config:
            errors.append("VMess config missing required field: user_id or uuid")

    def _validate_vless(self, config: Dict[str, Any], errors: List[str]):
        required_fields = ["server", "port", "uuid"]
        for field in required_fields:
            if field not in config:
                errors.append(f"VLESS config missing required field: {field}")

    def _validate_trojan(self, config: Dict[str, Any], errors: List[str]):
        required_fields = ["server", "port", "password"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Trojan config missing required field: {field}")

    def _validate_shadowsocks(self, config: Dict[str, Any], errors: List[str]):
        required_fields = ["server", "port", "password", "method"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Shadowsocks config missing required field: {field}")

    def _validate_shadowsocksr(self, config: Dict[str, Any], errors: List[str]):
        required_fields = ["server", "port", "password", "method", "protocol", "obfs"]
        for field in required_fields:
            if field not in config:
                errors.append(f"ShadowsocksR config missing required field: {field}")
