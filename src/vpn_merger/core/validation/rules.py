from __future__ import annotations

from typing import Any, Dict

from .rules_structure import check_structure
from .rules_limits import check_limits
from .rules_security import check_security
from .rules_sources import check_sources_light
from .rules_output import check_output
from .rules_processing import check_processing_extras


def run_additional_rules(config: Dict[str, Any], validator: Any) -> None:
    """Run a minimal set of modular rules.

    The validator is expected to expose `.errors` and `.warnings` lists and
    a `ValidationError` dataclass on its type for consistent messages.
    """
    check_structure(config, validator)
    check_limits(config, validator)
    check_security(config, validator)
    check_sources_light(config, validator)
    check_output(config, validator)
    check_processing_extras(config, validator)

__all__ = ["run_additional_rules"]
