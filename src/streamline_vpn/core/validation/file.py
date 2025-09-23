import json
import yaml
from pathlib import Path
from typing import List

class FileValidator:
    """Validator for configuration files."""

    def validate(self, file_path: Path) -> List[str]:
        """Validate a configuration file."""
        errors = []
        if not file_path.exists():
            errors.append(f"File '{file_path}' does not exist.")
            return errors

        if not file_path.is_file():
            errors.append(f"Path '{file_path}' is not a file.")
            return errors

        if file_path.stat().st_size == 0:
            errors.append(f"File '{file_path}' is empty.")
            return errors

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            try:
                yaml.safe_load(content)
            except yaml.YAMLError:
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    errors.append(f"File '{file_path}' is not a valid YAML or JSON file.")
        except Exception as e:
            errors.append(f"Error reading file '{file_path}': {e}")

        return errors
