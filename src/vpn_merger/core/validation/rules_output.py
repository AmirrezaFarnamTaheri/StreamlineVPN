from __future__ import annotations

from typing import Any, Dict

VALID_COMPRESSION_ALGORITHMS = {"gzip", "bzip2", "lzma", "zstd"}


def check_output(config: Dict[str, Any], validator: Any) -> None:
    settings = config.get("settings") or {}
    output = settings.get("output")
    if output is None:
        return
    if not isinstance(output, dict):
        validator.errors.append(
            validator.__class__.ValidationError(  # type: ignore[attr-defined]
                field="settings.output", message="Output settings must be a dictionary"
            )
        )
        return

    formats = output.get("formats")
    if formats is not None:
        if not isinstance(formats, dict):
            validator.errors.append(
                validator.__class__.ValidationError(  # type: ignore[attr-defined]
                    field="settings.output.formats",
                    message="Output formats must be a dictionary",
                )
            )
        else:
            for fmt, enabled in formats.items():
                if not isinstance(enabled, bool):
                    validator.errors.append(
                        validator.__class__.ValidationError(  # type: ignore[attr-defined]
                            field=f"settings.output.formats.{fmt}",
                            message="Format enable flag must be a boolean",
                        )
                    )

    compression = output.get("compression")
    if compression is not None:
        if not isinstance(compression, dict):
            validator.errors.append(
                validator.__class__.ValidationError(  # type: ignore[attr-defined]
                    field="settings.output.compression",
                    message="Compression settings must be a dictionary",
                )
            )
        else:
            algorithm = compression.get("algorithm")
            if algorithm is not None and algorithm not in VALID_COMPRESSION_ALGORITHMS:
                validator.errors.append(
                    validator.__class__.ValidationError(  # type: ignore[attr-defined]
                        field="settings.output.compression.algorithm",
                        message=(
                            "Compression algorithm must be one of: "
                            + ", ".join(sorted(VALID_COMPRESSION_ALGORITHMS))
                        ),
                    )
                )

