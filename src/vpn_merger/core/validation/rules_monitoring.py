from __future__ import annotations

from typing import Any, Dict

VALID_ALERT_TYPES = {"webhook", "email", "slack", "discord", "telegram"}


def _append_error(v: Any, field: str, message: str) -> None:
    v.errors.append(v.__class__.ValidationError(field=field, message=message))  # type: ignore[attr-defined]


def _append_warning(v: Any, field: str, message: str) -> None:
    v.warnings.append(
        v.__class__.ValidationError(field=field, message=message, severity="warning")  # type: ignore[attr-defined]
    )


def _check_alert_channel(field_path: str, ch: Dict[str, Any], v: Any) -> None:
    if not isinstance(ch, dict):
        _append_error(v, field_path, "Alert channel must be a dictionary")
        return
    t = ch.get("type")
    if t is not None and t not in VALID_ALERT_TYPES:
        _append_error(v, f"{field_path}.type", f"Alert channel type must be one of: {', '.join(sorted(VALID_ALERT_TYPES))}")


def check_monitoring(config: Dict[str, Any], validator: Any) -> None:
    settings = config.get("settings") or {}
    monitoring = settings.get("monitoring")
    if monitoring is None:
        return
    if not isinstance(monitoring, dict):
        _append_error(validator, "settings.monitoring", "Monitoring settings must be a dictionary")
        return

    interval = monitoring.get("health_check_interval")
    if interval is not None and (not isinstance(interval, int) or interval <= 0):
        _append_error(
            validator,
            "settings.monitoring.health_check_interval",
            "Health check interval must be a positive integer",
        )

    failure = monitoring.get("failure_threshold")
    if failure is not None and (not isinstance(failure, int) or failure < 0):
        _append_error(
            validator,
            "settings.monitoring.failure_threshold",
            "Failure threshold must be a non-negative integer",
        )

    channels = monitoring.get("alert_channels")
    if channels is not None:
        if not isinstance(channels, list):
            _append_error(validator, "settings.monitoring.alert_channels", "Alert channels must be a list")
        else:
            for i, ch in enumerate(channels):
                _check_alert_channel(f"settings.monitoring.alert_channels[{i}]", ch, validator)

