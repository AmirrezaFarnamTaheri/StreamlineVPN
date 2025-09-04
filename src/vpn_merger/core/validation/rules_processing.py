from __future__ import annotations

from typing import Any, Dict

# Upper bounds (duplicated to avoid import cycles)
MAX_CONCURRENT_LIMIT = 1000
MAX_TIMEOUT = 300
MAX_RETRIES = 10


def check_processing_extras(config: Dict[str, Any], validator: Any) -> None:
    settings = config.get("settings") or {}
    processing = settings.get("processing")
    if processing is None:
        return
    if not isinstance(processing, dict):
        validator.errors.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="settings.processing", message="Processing settings must be a dictionary"
            )
        )
        return

    # basic ranges
    cl = processing.get("concurrent_limit")
    if cl is not None and (not isinstance(cl, int) or not 1 <= cl <= MAX_CONCURRENT_LIMIT):
        validator.errors.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="settings.processing.concurrent_limit",
                message=f"Concurrent limit must be an integer between 1 and {MAX_CONCURRENT_LIMIT}",
            )
        )

    timeout = processing.get("timeout")
    if timeout is not None and (not isinstance(timeout, int) or not 1 <= timeout <= MAX_TIMEOUT):
        validator.errors.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="settings.processing.timeout",
                message=f"Timeout must be an integer between 1 and {MAX_TIMEOUT}",
            )
        )

    retries = processing.get("max_retries")
    if retries is not None and (not isinstance(retries, int) or not 0 <= retries <= MAX_RETRIES):
        validator.errors.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="settings.processing.max_retries",
                message=f"Max retries must be an integer between 0 and {MAX_RETRIES}",
            )
        )

    # rate_limiting shape
    rl = processing.get("rate_limiting")
    if rl is not None:
        if not isinstance(rl, dict):
            validator.errors.append(
                validator.__class__.ValidationError(  # type: ignore[attr-defined]
                    field="settings.processing.rate_limiting",
                    message="Rate limiting settings must be a dictionary",
                )
            )
        else:
            rpm = rl.get("requests_per_minute")
            if rpm is not None and (not isinstance(rpm, int) or rpm <= 0):
                validator.errors.append(
                    validator.__class__.ValidationError(  # type: ignore[attr-defined]
                        field="settings.processing.rate_limiting.requests_per_minute",
                        message="Requests per minute must be a positive integer",
                    )
                )
            burst = rl.get("burst_limit")
            if burst is not None and (not isinstance(burst, int) or burst <= 0):
                validator.errors.append(
                    validator.__class__.ValidationError(  # type: ignore[attr-defined]
                        field="settings.processing.rate_limiting.burst_limit",
                        message="Burst limit must be a positive integer",
                    )
                )

    # caching shape
    caching = processing.get("caching")
    if caching is not None and not isinstance(caching, dict):
        validator.errors.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="settings.processing.caching", message="Caching must be a dictionary"
            )
        )
