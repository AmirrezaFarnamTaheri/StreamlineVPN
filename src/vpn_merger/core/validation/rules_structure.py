from __future__ import annotations

from typing import Any, Dict


def check_structure(config: Dict[str, Any], validator: Any) -> None:
    """Lightweight structural sanity checks.

    - Ensure top-level keys are dicts when present.
    """
    for key in ("metadata", "sources", "settings"):
        if key in config and not isinstance(config.get(key), dict):
            validator.errors.append(
                validator.__class__.ValidationError(  # type: ignore[attr-defined]
                    field=key, message=f"Section '{key}' must be a dictionary"
                )
            )

