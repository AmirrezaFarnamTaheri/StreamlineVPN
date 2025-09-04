#!/usr/bin/env python3
"""
Enhanced Security Test Suite for VPN Merger
===========================================

Advanced security testing focusing on the specific vulnerabilities
mentioned in the comprehensive analysis report.
"""

import asyncio
import base64
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from vpn_merger.core.source_manager import SourceManager
from vpn_merger.core.source_validator import UnifiedSourceValidator
from vpn_merger.core.output.manager import OutputManager
from vpn_merger.web.config_generator import VPNConfigGenerator


class TestPathTraversalSecurity:
    """Test path traversal vulnerability fixes."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_output_path_validation(self):
        """Test output path validation prevents directory traversal."""
        output_manager = OutputManager()
        
        # Test malicious paths
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
            "../../../home/user/.ssh/id_rsa",
            "..%2F..%2F..%2Fetc%2Fpasswd",  # URL encoded
            "..%5C..%5C..%5Cwindows%5Csystem32%5Cconfig%5Csam",  # URL encoded
            "\\x2e\\x2e\\x2f\\x2e\\x2e\\x2f\\x2e\\x2e\\x2fetc\\x2fpasswd",  # Hex encoded
        ]
        
        for malicious_path in malicious_paths:
            # Test path validation
            is_safe = output_manager.validate_output_path(str(malicious_path))
            # Should reject malicious paths
            assert not is_safe, "Path traversal vulnerability detected"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_safe_path_acceptance(self):
        """Test that safe paths are accepted."""
        output_manager = OutputManager()
        
        # Test safe paths
        safe_paths = [
            "output/vpn_config.txt",
            "output/subdir/config.yaml",
            "temp/test_file.json",
            "C:\\Users\\test\\Documents\\config.txt",
            "/tmp/vpn_config.txt",
            "/var/tmp/test_config.yaml",
        ]
        
        for safe_path in safe_paths:
            path = Path(safe_path)
            
            # Test path validation
            is_safe = output_manager.validate_output_path(path)
            
            # Should accept safe paths
            assert is_safe, f"Safe path incorrectly rejected: {safe_path}"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_path_safety_validation(self):
        """Test path safety validation method."""
        output_manager = OutputManager()
        
        # Test dangerous patterns
        dangerous_patterns = [
            "..",  # Directory traversal
            "\\x",  # Hex encoding
            "%00",  # Null byte encoding
            "%2e%2e",  # URL encoded ..
            "%2f",  # URL encoded /
            "%5c",  # URL encoded backslash
        ]
        
        for pattern in dangerous_patterns:
            is_safe = output_manager.is_path_safe(f"test{pattern}file.txt")
            
            # Should reject dangerous patterns
            assert not is_safe, f"Dangerous pattern not detected: {pattern}"


class TestInputValidationSecurity:
    """Test input validation security fixes."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_config_generator_input_validation(self):
        """Test config generator input validation."""
        generator = VPNConfigGenerator()
        
        # Test malicious inputs
        malicious_inputs = [
            {"host": "<script>alert('xss')</script>", "port": 443, "uuid": "test"},
            {"host": "javascript:alert('xss')", "port": 443, "uuid": "test"},
            {"host": "<img src=x onerror=alert('xss')>", "port": 443, "uuid": "test"},
            {"host": "<svg onload=alert('xss')>", "port": 443, "uuid": "test"},
            {"host": "';alert('xss');//", "port": 443, "uuid": "test"},
            {"host": "<iframe src=javascript:alert('xss')></iframe>", "port": 443, "uuid": "test"},
            {"host": "eval('malicious_code')", "port": 443, "uuid": "test"},
            {"host": "exec('rm -rf /')", "port": 443, "uuid": "test"},
            {"host": "__import__('os').system('ls')", "port": 443, "uuid": "test"},
            {"host": "getattr(__import__('os'), 'system')('ls')", "port": 443, "uuid": "test"},
        ]
        
        for malicious_input in malicious_inputs:
            # Test input validation
            is_safe = generator._validate_input_security(malicious_input)
            
            # Should reject malicious input
            assert not is_safe, f"Malicious input not detected: {malicious_input}"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_input_size_validation(self):
        """Test input size validation."""
        generator = VPNConfigGenerator()
        
        # Test oversized input
        oversized_input = {
            "host": "a" * 10000,  # 10KB string
            "port": 443,
            "uuid": "test"
        }
        
        # Test input validation
        is_safe = generator._validate_input_security(oversized_input)
        
        # Should reject oversized input
        assert not is_safe, "Oversized input not detected"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_safe_input_acceptance(self):
        """Test that safe inputs are accepted."""
        generator = VPNConfigGenerator()
        
        # Test safe inputs
        safe_inputs = [
            {"host": "example.com", "port": 443, "uuid": "12345678-1234-1234-1234-123456789012"},
            {"host": "192.168.1.1", "port": 8080, "uuid": "87654321-4321-4321-4321-210987654321"},
            {"host": "vpn-server.example.org", "port": 443, "uuid": "11111111-2222-3333-4444-555555555555"},
        ]
        
        for safe_input in safe_inputs:
            # Test input validation
            is_safe = generator._validate_input_security(safe_input)
            
            # Should accept safe input
            assert is_safe, f"Safe input incorrectly rejected: {safe_input}"


class TestAsyncContextManagerSecurity:
    """Test async context manager security fixes."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_source_validator_session_management(self):
        """Test source validator session management."""
        validator = UnifiedSourceValidator()
        
        # Test async context manager
        async with validator:
            # Session should be initialized
            assert validator.session is not None
            
            # Test session properties
            assert validator.session.timeout.total == validator.timeout
            assert "User-Agent" in validator.session.headers
            
        # Session should be closed after context exit
        assert validator.session is None or validator.session.closed

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_session_cleanup_on_exception(self):
        """Test session cleanup on exception."""
        validator = UnifiedSourceValidator()
        
        try:
            async with validator:
                # Session should be initialized
                assert validator.session is not None
                
                # Raise an exception
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Session should be closed even after exception
        assert validator.session is None or validator.session.closed

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_multiple_context_usage(self):
        """Test multiple context manager usage."""
        validator = UnifiedSourceValidator()
        
        # First usage
        async with validator:
            session1 = validator.session
            assert session1 is not None
        
        # Second usage
        async with validator:
            session2 = validator.session
            assert session2 is not None
            # Should be a new session
            assert session2 is not session1


class TestErrorHandlingSecurity:
    """Test error handling security fixes."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_source_manager_error_handling(self):
        """Test source manager error handling."""
        # Test with non-existent config file
        source_manager = SourceManager("non_existent_config.yaml")
        
        # Should handle FileNotFoundError gracefully
        sources = source_manager.get_all_sources()
        assert sources is not None
        assert len(sources) > 0  # Should have fallback sources

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_yaml_error_handling(self):
        """Test YAML error handling."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            # Write invalid YAML
            f.write("invalid: yaml: content: [")
            f.flush()
            
            try:
                source_manager = SourceManager(f.name)
                
                # Should handle YAML error gracefully
                sources = source_manager.get_all_sources()
                assert sources is not None
                assert len(sources) > 0  # Should have fallback sources
                
            finally:
                # Clean up (Windows needs the file closed before unlink)
                try:
                    f.close()
                except Exception:
                    pass
                Path(f.name).unlink()

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_permission_error_handling(self):
        """Test permission error handling."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("sources:\n  test: []")
            f.flush()
            
            try:
                # Make file read-only
                Path(f.name).chmod(0o000)
                
                source_manager = SourceManager(f.name)
                
                # Should handle permission error gracefully
                sources = source_manager.get_all_sources()
                assert sources is not None
                assert len(sources) > 0  # Should have fallback sources
                
            finally:
                # Restore permissions and clean up (ensure file is closed on Windows)
                try:
                    f.close()
                except Exception:
                    pass
                try:
                    Path(f.name).chmod(0o644)
                except Exception:
                    pass
                Path(f.name).unlink()


class TestWireGuardKeyGenerationSecurity:
    """Test WireGuard key generation security."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_wireguard_key_generation(self):
        """Test WireGuard key generation security."""
        generator = VPNConfigGenerator()
        
        # Test key generation
        result = await generator._handle_generate_wg_key(AsyncMock())
        
        # Verify response
        assert result.status == 200
        
        # Parse response
        response_data = await result.json()
        
        # Verify key properties
        assert "key" in response_data
        assert "key_type" in response_data
        assert "key_length" in response_data
        assert "format" in response_data
        
        # Verify key format
        key = response_data["key"]
        assert len(key) > 0
        assert response_data["key_type"] == "private"
        assert response_data["key_length"] == 32
        assert response_data["format"] == "base64"
        
        # Verify key is base64 encoded
        try:
            decoded_key = base64.b64decode(key)
            assert len(decoded_key) == 32
        except Exception:
            pytest.fail("Generated key is not valid base64")

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_wireguard_key_uniqueness(self):
        """Test WireGuard key uniqueness."""
        generator = VPNConfigGenerator()
        
        # Generate multiple keys
        keys = []
        for _ in range(10):
            result = await generator._handle_generate_wg_key(AsyncMock())
            response_data = await result.json()
            keys.append(response_data["key"])
        
        # Verify all keys are unique
        assert len(set(keys)) == len(keys), "Generated keys are not unique"

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_wireguard_key_cryptographic_strength(self):
        """Test WireGuard key cryptographic strength."""
        generator = VPNConfigGenerator()
        
        # Generate key
        result = await generator._handle_generate_wg_key(AsyncMock())
        response_data = await result.json()
        key = response_data["key"]
        
        # Decode key
        decoded_key = base64.b64decode(key)
        
        # Test entropy (basic check)
        # A truly random 32-byte key should have high entropy
        byte_counts = {}
        for byte in decoded_key:
            byte_counts[byte] = byte_counts.get(byte, 0) + 1
        
        # No single byte should appear more than 3 times in a 32-byte key
        max_count = max(byte_counts.values())
        assert max_count <= 3, "Generated key shows low entropy"


class TestMLModelSecurity:
    """Test ML model security."""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_ml_model_input_validation(self):
        """Test ML model input validation."""
        from vpn_merger.ml.quality_predictor_enhanced import EnhancedConfigQualityPredictor
        
        predictor = EnhancedConfigQualityPredictor()
        
        # Test malicious inputs
        malicious_inputs = [
            "eval('malicious_code')",
            "exec('rm -rf /')",
            "__import__('os').system('ls')",
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
        ]
        
        for malicious_input in malicious_inputs:
            # Test prediction with malicious input
            result = await predictor.predict_quality(malicious_input, source_reliability=0.8)
            
            # Should handle malicious input gracefully
            assert result is not None
            assert 0.0 <= result.quality_score <= 1.0
            assert result.confidence >= 0.0

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_ml_model_file_operations(self):
        """Test ML model file operations security."""
        from vpn_merger.ml.quality_predictor_enhanced import EnhancedConfigQualityPredictor
        
        predictor = EnhancedConfigQualityPredictor()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "test_model.pkl"
            
            # Test model saving
            success = predictor.save_model(str(model_path))
            assert success, "Model saving failed"
            assert model_path.exists(), "Model file not created"
            
            # Test model loading
            new_predictor = EnhancedConfigQualityPredictor()
            success = new_predictor.load_model(str(model_path))
            assert success, "Model loading failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "security"])
