from __future__ import annotations

from typing import Any, Dict


# Conservative, duplicated defaults to avoid import cycles
MAX_CONCURRENT_LIMIT = 1000
MAX_TIMEOUT = 300
MAX_RETRIES = 10


def check_limits(config: Dict[str, Any], validator: Any) -> None:
    settings = config.get("settings") or {}
    processing = settings.get("processing") or {}

    mc = processing.get("max_concurrent")
    if isinstance(mc, int) and mc > MAX_CONCURRENT_LIMIT:
        validator.warnings.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="settings.processing.max_concurrent",
                message=f"max_concurrent too high; cap at {MAX_CONCURRENT_LIMIT}",
                severity="warning",
            )
        )

    timeout = processing.get("timeout")
    if isinstance(timeout, int) and timeout > MAX_TIMEOUT:
        validator.warnings.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="settings.processing.timeout",
                message=f"timeout too high; cap at {MAX_TIMEOUT}",
                severity="warning",
            )
        )

    retries = processing.get("max_retries")
    if isinstance(retries, int) and retries > MAX_RETRIES:
        validator.warnings.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="settings.processing.max_retries",
                message=f"max_retries too high; cap at {MAX_RETRIES}",
                severity="warning",
            )
        )

