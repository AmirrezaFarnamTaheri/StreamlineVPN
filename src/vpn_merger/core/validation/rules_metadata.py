from __future__ import annotations

import re
from typing import Any, Dict


def check_metadata(config: Dict[str, Any], validator: Any) -> None:
    md = config.get("metadata") or {}
    if not isinstance(md, dict):
        validator.errors.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="metadata", message="Metadata must be a dictionary"
            )
        )
        return

    version = md.get("version")
    if version is not None:
        if not isinstance(version, str):
            validator.errors.append(
                validator.__class__.ValidationError(  # type: ignore[attr-defined]
                    field="metadata.version", message="Version must be a string"
                )
            )
        elif not re.match(r"^\d+\.\d+\.\d+$", version):
            validator.warnings.append(
                validator.__class__.ValidationError(  # type: ignore[attr-defined]
                    field="metadata.version",
                    message="Version should follow semantic versioning (e.g., '1.0.0')",
                    severity="warning",
                )
            )

    last_updated = md.get("last_updated")
    if last_updated is not None:
        if not isinstance(last_updated, str):
            validator.errors.append(
                validator.__class__.ValidationError(  # type: ignore[attr-defined]
                    field="metadata.last_updated", message="Last updated must be a string"
                )
            )
        elif not re.match(r"^\d{4}-\d{2}-\d{2}$", last_updated):
            validator.warnings.append(
                validator.__class__.ValidationError(  # type: ignore[attr-defined]
                    field="metadata.last_updated",
                    message="Last updated should be in YYYY-MM-DD format",
                    severity="warning",
                )
            )

