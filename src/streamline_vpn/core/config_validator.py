from pathlib import Path
from typing import Any, Dict, List

from .validation.file import FileValidator
from .validation.protocols import ProtocolValidator
from .validation.sections import SectionValidator
from ..models.configuration import Protocol
from ..utils.helpers import load_config_file

class ConfigurationValidator:
    """Comprehensive configuration validator for StreamlineVPN."""

    def __init__(self):
        self.file_validator = FileValidator()
        self.protocol_validator = ProtocolValidator()
        self.section_validator = SectionValidator()

    def validate_config_file(self, config_path: str) -> List[str]:
        """Validate a configuration file."""
        errors = self.file_validator.validate(Path(config_path))
        if errors:
            return errors

        config = load_config_file(Path(config_path))
        return self.validate_config(config)

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration data structure."""
        return self.section_validator.validate(config)
