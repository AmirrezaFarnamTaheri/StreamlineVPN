"""Tests for core validation file module."""

import json
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from streamline_vpn.core.validation.file import FileValidator


class TestFileValidator:
    """Test cases for FileValidator."""

    @pytest.fixture
    def validator(self):
        """Create FileValidator instance."""
        return FileValidator()

    def test_validate_nonexistent_file(self, validator):
        """Test validation of non-existent file."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        mock_path.__str__ = lambda self: "/nonexistent/file.yaml"
        
        errors = validator.validate(mock_path)
        
        assert len(errors) == 1
        assert "does not exist" in errors[0]
        assert "/nonexistent/file.yaml" in errors[0]

    def test_validate_not_a_file(self, validator):
        """Test validation when path is not a file."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = False
        mock_path.__str__ = lambda self: "/some/directory"
        
        errors = validator.validate(mock_path)
        
        assert len(errors) == 1
        assert "is not a file" in errors[0]
        assert "/some/directory" in errors[0]

    def test_validate_empty_file(self, validator):
        """Test validation of empty file."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_size = 0
        mock_path.stat.return_value = mock_stat
        mock_path.__str__ = lambda self: "/empty/file.yaml"
        
        errors = validator.validate(mock_path)
        
        assert len(errors) == 1
        assert "is empty" in errors[0]
        assert "/empty/file.yaml" in errors[0]

    def test_validate_valid_yaml_file(self, validator):
        """Test validation of valid YAML file."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_size = 100
        mock_path.stat.return_value = mock_stat
        
        yaml_content = "key: value\nlist:\n  - item1\n  - item2"
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('yaml.safe_load') as mock_yaml_load:
                mock_yaml_load.return_value = {"key": "value", "list": ["item1", "item2"]}
                
                errors = validator.validate(mock_path)
                
                assert len(errors) == 0
                mock_yaml_load.assert_called_once_with(yaml_content)

    def test_validate_valid_json_file(self, validator):
        """Test validation of valid JSON file (when YAML parsing fails)."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_size = 50
        mock_path.stat.return_value = mock_stat
        
        json_content = '{"key": "value", "number": 42}'
        
        with patch('builtins.open', mock_open(read_data=json_content)):
            with patch('yaml.safe_load') as mock_yaml_load:
                with patch('json.loads') as mock_json_loads:
                    # YAML parsing fails, JSON parsing succeeds
                    mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")
                    mock_json_loads.return_value = {"key": "value", "number": 42}
                    
                    errors = validator.validate(mock_path)
                    
                    assert len(errors) == 0
                    mock_yaml_load.assert_called_once_with(json_content)
                    mock_json_loads.assert_called_once_with(json_content)

    def test_validate_invalid_yaml_and_json(self, validator):
        """Test validation of file that's neither valid YAML nor JSON."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_size = 30
        mock_path.stat.return_value = mock_stat
        mock_path.__str__ = lambda self: "/invalid/file.txt"
        
        invalid_content = "This is not valid YAML or JSON content: [invalid syntax"
        
        with patch('builtins.open', mock_open(read_data=invalid_content)):
            with patch('yaml.safe_load') as mock_yaml_load:
                with patch('json.loads') as mock_json_loads:
                    # Both YAML and JSON parsing fail
                    mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")
                    mock_json_loads.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
                    
                    errors = validator.validate(mock_path)
                    
                    assert len(errors) == 1
                    assert "not a valid YAML or JSON file" in errors[0]
                    assert "/invalid/file.txt" in errors[0]

    def test_validate_file_read_error(self, validator):
        """Test validation when file reading fails."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_size = 100
        mock_path.stat.return_value = mock_stat
        mock_path.__str__ = lambda self: "/permission/denied.yaml"
        
        with patch('builtins.open') as mock_open_func:
            mock_open_func.side_effect = PermissionError("Permission denied")
            
            errors = validator.validate(mock_path)
            
            assert len(errors) == 1
            assert "Error reading file" in errors[0]
            assert "Permission denied" in errors[0]
            assert "/permission/denied.yaml" in errors[0]

    def test_validate_yaml_parsing_with_specific_error(self, validator):
        """Test YAML parsing with specific error handling."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_size = 50
        mock_path.stat.return_value = mock_stat
        
        yaml_content = "key: value\n  invalid_indentation: bad"
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('yaml.safe_load') as mock_yaml_load:
                with patch('json.loads') as mock_json_loads:
                    # YAML parsing fails with specific error
                    mock_yaml_load.side_effect = yaml.YAMLError("mapping values are not allowed here")
                    mock_json_loads.return_value = {"key": "value"}  # JSON succeeds
                    
                    errors = validator.validate(mock_path)
                    
                    # Should succeed because JSON parsing works
                    assert len(errors) == 0

    def test_validate_json_parsing_with_specific_error(self, validator):
        """Test JSON parsing with specific error handling."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_size = 40
        mock_path.stat.return_value = mock_stat
        mock_path.__str__ = lambda self: "/bad/file.json"
        
        json_content = '{"key": "value", "bad": }'
        
        with patch('builtins.open', mock_open(read_data=json_content)):
            with patch('yaml.safe_load') as mock_yaml_load:
                with patch('json.loads') as mock_json_loads:
                    # Both parsing methods fail
                    mock_yaml_load.side_effect = yaml.YAMLError("Invalid YAML")
                    mock_json_loads.side_effect = json.JSONDecodeError("Expecting value", json_content, 20)
                    
                    errors = validator.validate(mock_path)
                    
                    assert len(errors) == 1
                    assert "not a valid YAML or JSON file" in errors[0]

    def test_validate_unicode_decode_error(self, validator):
        """Test validation with unicode decode error."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_size = 20
        mock_path.stat.return_value = mock_stat
        mock_path.__str__ = lambda self: "/binary/file.dat"
        
        with patch('builtins.open') as mock_open_func:
            mock_open_func.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")
            
            errors = validator.validate(mock_path)
            
            assert len(errors) == 1
            assert "Error reading file" in errors[0]
            assert "invalid start byte" in errors[0]

    def test_validate_with_real_path_object(self, validator, tmp_path):
        """Test validation with real Path object and temporary file."""
        # Create a temporary YAML file
        yaml_file = tmp_path / "test.yaml"
        yaml_content = "name: test\nversion: 1.0\nfeatures:\n  - feature1\n  - feature2"
        yaml_file.write_text(yaml_content, encoding="utf-8")
        
        errors = validator.validate(yaml_file)
        
        assert len(errors) == 0

    def test_validate_with_real_json_file(self, validator, tmp_path):
        """Test validation with real JSON file."""
        # Create a temporary JSON file
        json_file = tmp_path / "test.json"
        json_content = '{"name": "test", "version": "1.0", "features": ["feature1", "feature2"]}'
        json_file.write_text(json_content, encoding="utf-8")
        
        errors = validator.validate(json_file)
        
        assert len(errors) == 0

    def test_validate_with_real_invalid_file(self, validator, tmp_path):
        """Test validation with real invalid file."""
        # Create a temporary invalid file
        invalid_file = tmp_path / "invalid.txt"
        invalid_content = "This is not YAML or JSON: [invalid syntax {"
        invalid_file.write_text(invalid_content, encoding="utf-8")
        
        errors = validator.validate(invalid_file)
        
        assert len(errors) == 1
        assert "not a valid YAML or JSON file" in errors[0]

    def test_validate_with_real_empty_file(self, validator, tmp_path):
        """Test validation with real empty file."""
        # Create a temporary empty file
        empty_file = tmp_path / "empty.yaml"
        empty_file.touch()
        
        errors = validator.validate(empty_file)
        
        assert len(errors) == 1
        assert "is empty" in errors[0]


class TestFileValidatorEdgeCases:
    """Edge case tests for FileValidator."""

    @pytest.fixture
    def validator(self):
        """Create FileValidator instance."""
        return FileValidator()

    def test_validate_file_with_bom(self, validator):
        """Test validation of file with BOM (Byte Order Mark)."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_size = 50
        mock_path.stat.return_value = mock_stat
        
        # Content with BOM
        yaml_content = "\ufeffkey: value\nother: data"
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('yaml.safe_load') as mock_yaml_load:
                mock_yaml_load.return_value = {"key": "value", "other": "data"}
                
                errors = validator.validate(mock_path)
                
                assert len(errors) == 0

    def test_validate_very_large_file(self, validator):
        """Test validation of very large file."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_size = 1024 * 1024 * 10  # 10MB
        mock_path.stat.return_value = mock_stat
        
        # Large YAML content
        yaml_content = "key: value\n" * 1000
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('yaml.safe_load') as mock_yaml_load:
                mock_yaml_load.return_value = {"key": "value"}
                
                errors = validator.validate(mock_path)
                
                assert len(errors) == 0

    def test_validate_file_with_special_characters(self, validator):
        """Test validation of file with special characters in path."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_size = 30
        mock_path.stat.return_value = mock_stat
        mock_path.__str__ = lambda: "/path/with spaces/and-special_chars@file.yaml"
        
        yaml_content = "test: data"
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            with patch('yaml.safe_load') as mock_yaml_load:
                mock_yaml_load.return_value = {"test": "data"}
                
                errors = validator.validate(mock_path)
                
                assert len(errors) == 0

    def test_validate_nested_yaml_structure(self, validator):
        """Test validation of complex nested YAML structure."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_stat = MagicMock()
        mock_stat.st_size = 200
        mock_path.stat.return_value = mock_stat
        
        complex_yaml = """
        database:
          host: localhost
          port: 5432
          credentials:
            username: user
            password: pass
        services:
          - name: web
            port: 8080
            config:
              debug: true
          - name: api
            port: 3000
            config:
              debug: false
        """
        
        with patch('builtins.open', mock_open(read_data=complex_yaml)):
            with patch('yaml.safe_load') as mock_yaml_load:
                mock_yaml_load.return_value = {
                    "database": {"host": "localhost", "port": 5432},
                    "services": [{"name": "web"}, {"name": "api"}]
                }
                
                errors = validator.validate(mock_path)
                
                assert len(errors) == 0
