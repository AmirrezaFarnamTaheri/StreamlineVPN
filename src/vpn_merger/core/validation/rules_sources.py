from __future__ import annotations

from typing import Any, Dict, List


# Local copy to avoid import cycles
VALID_PROTOCOLS = {
    "vmess",
    "vless",
    "trojan",
    "shadowsocks",
    "shadowsocksr",
    "http",
    "https",
    "socks",
    "socks5",
    "hysteria",
    "hysteria2",
    "tuic",
    "wireguard",
    "all",
}

MAX_URL_LENGTH = 2048


def _append_error(validator: Any, field: str, message: str) -> None:
    validator.errors.append(
        validator.__class__.ValidationError(field=field, message=message)  # type: ignore[attr-defined]
    )


def _append_warning(validator: Any, field: str, message: str) -> None:
    validator.warnings.append(
        validator.__class__.ValidationError(  # type: ignore[attr-defined]
            field=field, message=message, severity="warning"
        )
    )


def _check_one_url(field_path: str, entry: Any, validator: Any) -> None:
    if isinstance(entry, str):
        url = entry
        if len(url) > MAX_URL_LENGTH:
            _append_error(validator, f"{field_path}", f"URL too long (max {MAX_URL_LENGTH})")
        if not (url.startswith("http://") or url.startswith("https://")):
            _append_warning(validator, f"{field_path}", "URL should start with http:// or https://")
        return

    if not isinstance(entry, dict):
        _append_error(validator, field_path, "URL entry must be a string or dictionary")
        return

    url = entry.get("url")
    if not isinstance(url, str):
        _append_error(validator, f"{field_path}.url", "URL must be a string")
    else:
        if len(url) > MAX_URL_LENGTH:
            _append_error(validator, f"{field_path}.url", f"URL too long (max {MAX_URL_LENGTH})")
        if not (url.startswith("http://") or url.startswith("https://")):
            _append_warning(validator, f"{field_path}.url", "URL should start with http:// or https://")

    weight = entry.get("weight")
    if weight is not None and not (isinstance(weight, (int, float)) and 0 <= weight <= 1):
        _append_error(validator, f"{field_path}.weight", "Weight must be a number between 0 and 1")

    protos = entry.get("protocols")
    if protos is not None:
        if not isinstance(protos, list):
            _append_error(validator, f"{field_path}.protocols", "Protocols must be a list of strings")
        else:
            for j, p in enumerate(protos):
                if not isinstance(p, str):
                    _append_error(validator, f"{field_path}.protocols[{j}]", "Protocol must be a string")
                elif p not in VALID_PROTOCOLS:
                    _append_warning(validator, f"{field_path}.protocols[{j}]", f"Unknown protocol '{p}'")


def check_sources_light(config: Dict[str, Any], validator: Any) -> None:
    """Lightweight validation for the sources section.

    This complements the built-in validator logic and helps keep
    `config_validator.py` smaller over time.
    """
    sources = config.get("sources")
    if sources is None:
        return
    if not isinstance(sources, dict):
        _append_error(validator, "sources", "Sources must be a dictionary")
        return

    for tier_name, tier_cfg in sources.items():
        if not isinstance(tier_cfg, dict):
            _append_error(validator, f"sources.{tier_name}", "Tier configuration must be a dictionary")
            continue
        # Tier-level properties parity with inline validator
        if "reliability_score" in tier_cfg:
            score = tier_cfg.get("reliability_score")
            if not isinstance(score, (int, float)) or not (0 <= score <= 1):
                _append_error(
                    validator,
                    f"sources.{tier_name}.reliability_score",
                    "Reliability score must be a number between 0 and 1",
                )

        if "priority" in tier_cfg:
            priority = tier_cfg.get("priority")
            if not isinstance(priority, int) or priority < 1:
                _append_error(
                    validator,
                    f"sources.{tier_name}.priority",
                    "Priority must be a positive integer",
                )
        urls = tier_cfg.get("urls")
        if urls is not None:
            if not isinstance(urls, list):
                _append_error(validator, f"sources.{tier_name}.urls", "URLs must be a list")
            else:
                for i, item in enumerate(urls):
                    _check_one_url(f"sources.{tier_name}.urls[{i}]", item, validator)


def check_sources_full(config: Dict[str, Any], validator: Any) -> None:
    """Full validation for sources (currently same as light).

    This function is intended as the target for migrating the rest of the
    in-file validations; for now it reuses the light checks.
    """
    check_sources_light(config, validator)
