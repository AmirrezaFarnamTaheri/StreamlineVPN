from typing import Any, Dict, List
from urllib.parse import urlparse

SUPPORTED_PROTOCOLS = {
    "vless",
    "vmess",
    "trojan",
    "shadowsocks",
    "shadowsocksr",
    "ss",
    "ssr",
    "http",
    "socks5",
    "tuic",
}

class SectionValidator:
    """Validator for configuration sections."""

    def validate(self, config: Dict[str, Any]) -> List[str]:
        """Validate all sections of a configuration."""
        errors = []
        warnings = []
        self._validate_sources_section(config, errors, warnings)
        self._validate_processing_section(config, errors, warnings)
        self._validate_output_section(config, errors, warnings)
        self._validate_security_section(config, errors)
        self._validate_cache_section(config, errors)
        return errors + [f"Warning: {w}" for w in warnings]

    def _validate_sources_section(self, config: Dict[str, Any], issues: list, warnings: list) -> None:
        """Validate sources section."""
        if "sources" not in config:
            issues.append("Missing 'sources' section")
            return

        sources = config["sources"]
        if not isinstance(sources, dict):
            issues.append("Sources must be a dictionary")
            return

        if not sources:
            warnings.append("Sources section is empty")
            return

        # Validate each tier
        for tier_name, tier_data in sources.items():
            self._validate_source_tier(tier_name, tier_data, issues, warnings)

    def _validate_source_tier(self, tier_name: str, tier_data: Any, issues: list, warnings: list) -> None:
        """Validate a source tier."""
        tier_path = f"sources.{tier_name}"

        # Handle both list and dict formats
        if isinstance(tier_data, list):
            sources_list = tier_data
        elif isinstance(tier_data, dict):
            if "urls" in tier_data:
                sources_list = tier_data["urls"]
            else:
                issues.append(f'Tier dictionary must contain "urls" key: {tier_path}')
                return
        else:
            issues.append(f'Tier must be a list or dictionary with "urls" key: {tier_path}')
            return

        if not isinstance(sources_list, list):
            issues.append(f"URLs must be a list: {tier_path}.urls")
            return

        if not sources_list:
            warnings.append(f'Tier "{tier_name}" has no sources')
            return

        # Validate each source in the tier
        for i, source in enumerate(sources_list):
            self._validate_source_entry(f"{tier_path}[{i}]", source, issues, warnings)

    def _validate_source_entry(self, source_path: str, source: Any, issues: list, warnings: list) -> None:
        """Validate a single source entry."""
        if isinstance(source, str):
            # Simple URL string
            self._validate_url(source_path, source, issues, warnings)
        elif isinstance(source, dict):
            # Source object with metadata
            if "url" not in source:
                issues.append(f'Source object must contain "url" field: {source_path}')
                return

            self._validate_url(f"{source_path}.url", source["url"], issues, warnings)

            # Validate optional fields
            if "weight" in source:
                self._validate_weight(f"{source_path}.weight", source["weight"], issues, warnings)

            if "protocols" in source:
                self._validate_protocols(
                    f"{source_path}.protocols", source["protocols"], issues, warnings
                )

            if "timeout" in source:
                self._validate_timeout(f"{source_path}.timeout", source["timeout"], issues, warnings)

            if "headers" in source:
                self._validate_headers(f"{source_path}.headers", source["headers"], issues)
        else:
            issues.append(f"Source must be a URL string or object: {source_path}")

    def _validate_url(self, field_path: str, url: Any, issues: list, warnings: list) -> None:
        """Validate URL format."""
        if not isinstance(url, str):
            issues.append(f"URL must be a string: {field_path}")
            return

        if not url.strip():
            issues.append(f"URL cannot be empty: {field_path}")
            return

        try:
            parsed = urlparse(url)
            if not parsed.scheme:
                issues.append(f"URL must include scheme (http/https): {field_path}")
            elif parsed.scheme not in ["http", "https"]:
                warnings.append(f"Unusual URL scheme: {parsed.scheme} in {field_path}")

            if not parsed.netloc:
                issues.append(f"URL must include hostname: {field_path}")

        except Exception as e:
            issues.append(f"Invalid URL format: {e} in {field_path}")

    def _validate_weight(self, field_path: str, weight: Any, issues: list, warnings: list) -> None:
        """Validate source weight."""
        if not isinstance(weight, (int, float)):
            issues.append(f"Weight must be a number: {field_path}")
            return

        if weight < 0:
            issues.append(f"Weight cannot be negative: {field_path}")
        elif weight > 1.0:
            warnings.append(f"Weight greater than 1.0 may cause unexpected behavior: {field_path}")

    def _validate_protocols(self, field_path: str, protocols: Any, issues: list, warnings: list) -> None:
        """Validate protocol list."""
        if not isinstance(protocols, list):
            issues.append(f"Protocols must be a list: {field_path}")
            return

        for i, protocol in enumerate(protocols):
            if not isinstance(protocol, str):
                issues.append(f"Protocol must be a string: {field_path}[{i}]")
                continue

            if protocol.lower() not in SUPPORTED_PROTOCOLS:
                warnings.append(f"Unknown protocol: {protocol} in {field_path}[{i}]")

    def _validate_timeout(self, field_path: str, timeout: Any, issues: list, warnings: list) -> None:
        """Validate timeout value."""
        if not isinstance(timeout, (int, float)):
            issues.append(f"Timeout must be a number: {field_path}")
            return

        if timeout <= 0:
            issues.append(f"Timeout must be positive: {field_path}")
        elif timeout > 300:
            warnings.append(f"Timeout greater than 300 seconds may cause delays: {field_path}")

    def _validate_headers(self, field_path: str, headers: Any, issues: list) -> None:
        """Validate HTTP headers."""
        if not isinstance(headers, dict):
            issues.append(f"Headers must be a dictionary: {field_path}")
            return

        for key, value in headers.items():
            if not isinstance(key, str):
                issues.append(f"Header name must be a string: {field_path}.{key}")
            if not isinstance(value, str):
                issues.append(f"Header value must be a string: {field_path}.{key}")

    def _validate_processing_section(self, config: Dict[str, Any], issues: list, warnings: list) -> None:
        """Validate processing configuration."""
        if "processing" not in config:
            return  # Optional section

        processing = config["processing"]
        if not isinstance(processing, dict):
            issues.append("Processing section must be a dictionary")
            return

        # Validate specific processing options
        if "max_concurrent" in processing:
            max_concurrent = processing["max_concurrent"]
            if not isinstance(max_concurrent, int):
                issues.append("max_concurrent must be an integer")
            elif max_concurrent < 1:
                issues.append("max_concurrent must be at least 1")
            elif max_concurrent > 1000:
                warnings.append("Very high concurrency may cause performance issues")

        if "timeout" in processing:
            self._validate_timeout("processing.timeout", processing["timeout"], issues, warnings)

        if "retry_attempts" in processing:
            retry_attempts = processing["retry_attempts"]
            if not isinstance(retry_attempts, int):
                issues.append("retry_attempts must be an integer")
            elif retry_attempts < 0:
                issues.append("retry_attempts cannot be negative")

    def _validate_output_section(self, config: Dict[str, Any], issues: list, warnings: list) -> None:
        """Validate output configuration."""
        if "output" not in config:
            return  # Optional section

        output = config["output"]
        if not isinstance(output, dict):
            issues.append("Output section must be a dictionary")
            return

        if "formats" in output:
            formats = output["formats"]
            if not isinstance(formats, list):
                issues.append("Formats must be a list")
            else:
                for i, fmt in enumerate(formats):
                    if not isinstance(fmt, str):
                        issues.append(f"Format must be a string: output.formats[{i}]")
                    elif fmt.lower() not in {"json", "yaml", "clash", "singbox", "base64", "csv"}:
                        warnings.append(f"Unknown output format: {fmt} in output.formats[{i}]")

        if "directory" in output:
            directory = output["directory"]
            if not isinstance(directory, str):
                issues.append("Output directory must be a string")
            elif not directory.strip():
                issues.append("Output directory cannot be empty")

    def _validate_security_section(self, config: Dict[str, Any], issues: list) -> None:
        """Validate security configuration."""
        if "security" not in config:
            return  # Optional section

        security = config["security"]
        if not isinstance(security, dict):
            issues.append("Security section must be a dictionary")
            return

        # Validate specific security options
        boolean_fields = ["enable_validation", "strict_mode", "allow_insecure"]
        for field in boolean_fields:
            if field in security:
                if not isinstance(security[field], bool):
                    issues.append(f"{field} must be a boolean")

        if "blacklist" in security:
            blacklist = security["blacklist"]
            if not isinstance(blacklist, list):
                issues.append("Blacklist must be a list")
            else:
                for i, item in enumerate(blacklist):
                    if not isinstance(item, str):
                        issues.append(f"Blacklist item must be a string: security.blacklist[{i}]")

    def _validate_cache_section(self, config: Dict[str, Any], issues: list) -> None:
        """Validate cache configuration."""
        if "cache" not in config:
            return  # Optional section

        cache = config["cache"]
        if not isinstance(cache, dict):
            issues.append("Cache section must be a dictionary")
            return

        if "enabled" in cache:
            if not isinstance(cache["enabled"], bool):
                issues.append("Cache enabled must be a boolean")

        if "ttl" in cache:
            ttl = cache["ttl"]
            if not isinstance(ttl, int):
                issues.append("Cache TTL must be an integer")
            elif ttl < 0:
                issues.append("Cache TTL cannot be negative")
