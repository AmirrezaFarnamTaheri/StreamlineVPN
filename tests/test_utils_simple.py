"""
Simple tests for utils modules
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.utils.helpers import *
from streamline_vpn.utils.error_handling import *
from streamline_vpn.utils.validation import *
from streamline_vpn.utils.logging import *


class TestHelpers:
    """Test helper functions"""
    
    def test_generate_uuid(self):
        """Test UUID generation"""
        uuid1 = generate_uuid()
        uuid2 = generate_uuid()
        
        assert uuid1 != uuid2
        assert len(uuid1) == 36
    
    def test_generate_random_string(self):
        """Test random string generation"""
        string1 = generate_random_string(10)
        string2 = generate_random_string(10)
        
        assert len(string1) == 10
        assert len(string2) == 10
        assert string1 != string2
    
    def test_hash_string(self):
        """Test string hashing"""
        string = "test string"
        hash1 = hash_string(string)
        hash2 = hash_string(string)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_validate_url(self):
        """Test URL validation"""
        assert validate_url("https://example.com") is True
        assert validate_url("http://example.com") is True
        assert validate_url("ftp://example.com") is False
        assert validate_url("invalid") is False
        assert validate_url("") is False
    
    def test_validate_email(self):
        """Test email validation"""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.co.uk") is True
        assert validate_email("invalid") is False
        assert validate_email("@example.com") is False
        assert validate_email("") is False
    
    def test_validate_ip_address(self):
        """Test IP address validation"""
        assert validate_ip_address("192.168.1.1") is True
        assert validate_ip_address("10.0.0.1") is True
        assert validate_ip_address("2001:db8::1") is True
        assert validate_ip_address("invalid") is False
        assert validate_ip_address("") is False
    
    def test_validate_port(self):
        """Test port validation"""
        assert validate_port(80) is True
        assert validate_port(443) is True
        assert validate_port(65535) is True
        assert validate_port(0) is False
        assert validate_port(65536) is False
        assert validate_port(-1) is False
    
    def test_validate_uuid(self):
        """Test UUID validation"""
        valid_uuid = "12345678-1234-1234-1234-123456789012"
        assert validate_uuid(valid_uuid) is True
        assert validate_uuid("invalid") is False
        assert validate_uuid("") is False
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        assert sanitize_filename("test file.txt") == "test_file.txt"
        assert sanitize_filename("file/with\\path") == "file_with_path"
        assert sanitize_filename("file:with*chars?") == "file_with_chars_"
        assert sanitize_filename("") == ""
    
    def test_format_bytes(self):
        """Test byte formatting"""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1048576) == "1.0 MB"
        assert format_bytes(1073741824) == "1.0 GB"
        assert format_bytes(0) == "0 B"
    
    def test_format_duration(self):
        """Test duration formatting"""
        assert format_duration(60) == "1m 0s"
        assert format_duration(3661) == "1h 1m 1s"
        assert format_duration(0) == "0s"
    
    def test_parse_duration(self):
        """Test duration parsing"""
        assert parse_duration("1h") == 3600
        assert parse_duration("30m") == 1800
        assert parse_duration("45s") == 45
        assert parse_duration("1h30m") == 5400
        assert parse_duration("invalid") == 0


class TestErrorHandling:
    """Test error handling functions"""
    
    def test_handle_exception(self):
        """Test exception handling"""
        def test_function():
            raise ValueError("Test error")
        
        result = handle_exception(test_function)
        assert result is None
    
    def test_handle_exception_with_return_value(self):
        """Test exception handling with return value"""
        def test_function():
            raise ValueError("Test error")
        
        result = handle_exception(test_function, return_value="error")
        assert result == "error"
    
    def test_handle_exception_success(self):
        """Test exception handling with successful function"""
        def test_function():
            return "success"
        
        result = handle_exception(test_function)
        assert result == "success"
    
    def test_async_handle_exception(self):
        """Test async exception handling"""
        async def test_async_function():
            raise ValueError("Test error")
        
        result = asyncio.run(async_handle_exception(test_async_function))
        assert result is None
    
    def test_async_handle_exception_success(self):
        """Test async exception handling with successful function"""
        async def test_async_function():
            return "success"
        
        result = asyncio.run(async_handle_exception(test_async_function))
        assert result == "success"


class TestValidation:
    """Test validation functions"""
    
    def test_validate_required_fields(self):
        """Test required fields validation"""
        data = {"name": "test", "email": "test@example.com"}
        required = ["name", "email"]
        
        result = validate_required_fields(data, required)
        assert result["is_valid"] is True
        assert result["errors"] == []
    
    def test_validate_required_fields_missing(self):
        """Test required fields validation with missing fields"""
        data = {"name": "test"}
        required = ["name", "email"]
        
        result = validate_required_fields(data, required)
        assert result["is_valid"] is False
        assert "email" in result["errors"][0]
    
    def test_validate_field_types(self):
        """Test field types validation"""
        data = {"name": "test", "age": 25, "active": True}
        types = {"name": str, "age": int, "active": bool}
        
        result = validate_field_types(data, types)
        assert result["is_valid"] is True
        assert result["errors"] == []
    
    def test_validate_field_types_invalid(self):
        """Test field types validation with invalid types"""
        data = {"name": "test", "age": "25", "active": "true"}
        types = {"name": str, "age": int, "active": bool}
        
        result = validate_field_types(data, types)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0


class TestLogging:
    """Test logging functions"""
    
    def test_setup_logging(self):
        """Test logging setup"""
        setup_logging()
        # This should not raise an exception
    
    def test_setup_logging_with_level(self):
        """Test logging setup with specific level"""
        setup_logging(level="DEBUG")
        # This should not raise an exception
    
    def test_get_logger(self):
        """Test getting logger"""
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "streamline_vpn.test"
    
    def test_log_function_call(self):
        """Test logging function calls"""
        @log_function_call
        def test_function(x, y):
            return x + y
        
        result = test_function(1, 2)
        assert result == 3
    
    def test_log_async_function_call(self):
        """Test logging async function calls"""
        @log_async_function_call
        async def test_async_function(x, y):
            return x + y
        
        result = asyncio.run(test_async_function(1, 2))
        assert result == 3
