from __future__ import annotations

from typing import Any, Dict


def check_security(config: Dict[str, Any], validator: Any) -> None:
    settings = config.get("settings") or {}
    security = settings.get("security")
    if security is None:
        return
    if not isinstance(security, dict):
        validator.errors.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="settings.security",
                message="Security settings must be a dictionary",
            )
        )
        return

    ssl_val = security.get("ssl_validation")
    if ssl_val is not None and not isinstance(ssl_val, dict):
        validator.errors.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="settings.security.ssl_validation",
                message="ssl_validation must be a dictionary",
            )
        )
        return
    if isinstance(ssl_val, dict) and "enabled" in ssl_val and not isinstance(ssl_val.get("enabled"), bool):
        validator.warnings.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="settings.security.ssl_validation.enabled",
                message="ssl_validation.enabled should be a boolean",
                severity="warning",
            )
        )

