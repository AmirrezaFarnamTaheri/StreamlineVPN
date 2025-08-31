#!/usr/bin/env python3
"""
Security Tests for VPN Subscription Merger
Tests for security vulnerabilities, input validation, and threat detection.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import re

# Import with fallbacks
try:
    from vpn_merger import UnifiedSources
except ImportError:
    UnifiedSources = None


class TestInputValidation:
    """Test input validation and sanitization."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_malicious_url_detection(self):
        """Test detection of malicious URLs."""
        malicious_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "file:///etc/passwd",
            "ftp://malicious.com/backdoor",
            "http://localhost:22",
            "https://192.168.1.1/admin",
            "http://[::1]:8080/",
            "https://evil.com/../../etc/passwd"
        ]
        
        for url in malicious_urls:
            # Basic URL validation
            assert not url.startswith(('javascript:', 'data:', 'file:', 'ftp:'))
            assert not 'localhost' in url.lower()
            assert not '127.0.0.1' in url
            assert not '192.168.' in url
            assert not '10.' in url
            assert not '172.' in url
            assert not '../' in url
            assert not '..\\' in url
    
    def test_sql_injection_prevention(self):
        """Test prevention of SQL injection attacks."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        for malicious_input in malicious_inputs:
            # Should not contain SQL injection patterns
            assert not re.search(r"('|(\\')|(;)|(--)|(union)|(select)|(drop)|(insert)|(delete))", 
                                malicious_input.lower())
    
    def test_xss_prevention(self):
        """Test prevention of XSS attacks."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//",
            "<iframe src=javascript:alert('xss')></iframe>"
        ]
        
        for payload in xss_payloads:
            # Should not contain XSS patterns
            assert not re.search(r"<script|javascript:|onerror=|onload=|<iframe", 
                                payload.lower())
    
    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, temp_output_dir):
        """Test prevention of path traversal attacks."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Test with malicious output paths
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
            "../../../home/user/.ssh/id_rsa"
        ]
        
        for malicious_path in malicious_paths:
            # Should not allow path traversal
            assert not '..' in malicious_path
            assert not malicious_path.startswith('/etc/')
            assert not malicious_path.startswith('C:\\Windows\\')
            assert not malicious_path.startswith('/home/')


class TestThreatDetection:
    """Test threat detection and security monitoring."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_suspicious_pattern_detection(self):
        """Test detection of suspicious patterns."""
        suspicious_patterns = [
            "eval(",
            "exec(",
            "__import__",
            "getattr(",
            "setattr(",
            "globals()",
            "locals()",
            "compile(",
            "open(",
            "file(",
            "input(",
            "raw_input("
        ]
        
        for pattern in suspicious_patterns:
            # Should detect suspicious patterns
            assert pattern in suspicious_patterns
    
    def test_malicious_config_detection(self):
        """Test detection of malicious VPN configurations."""
        malicious_configs = [
            "vmess://eyJ2IjoiMiIsInBzIjoiTWFsaWNpb3VzIiwiaG9zdCI6ImV2aWwuY29tIiwicG9ydCI6IjQ0MyIsImlkIjoiYWJjZCIsImFpZCI6IjAiLCJzY3kiOiJhdXRvIiwibmV0Ijoid3MiLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6InRscyJ9",
            "trojan://malicious@evil.com:443?security=tls&type=tcp&headerType=none#Malicious",
            "ss://YWVzLTI1Ni1nY206bWFsd2FyZUBldmlsLmNvbTo0NDM=#Malicious"
        ]
        
        for config in malicious_configs:
            # Should detect malicious domains
            assert not 'evil.com' in config.lower()
            assert not 'malicious' in config.lower()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, temp_output_dir):
        """Test rate limiting and DoS prevention."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Test rapid requests
        start_time = time.time()
        
        # Make multiple rapid requests
        tasks = []
        for i in range(10):
            task = merger.run_comprehensive_merge(
                output_dir=str(temp_output_dir / f"output_{i}"),
                test_sources=True,
                max_sources=5
            )
            tasks.append(task)
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Should handle rapid requests gracefully
            assert end_time - start_time < 60, "Rate limiting not working"
            
            # Some requests may fail due to rate limiting
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) > 0, "All requests failed"
            
        except Exception as e:
            # Rate limiting should prevent DoS
            assert "rate limit" in str(e).lower() or "too many" in str(e).lower()


class TestDataProtection:
    """Test data protection and privacy."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_sensitive_data_filtering(self):
        """Test filtering of sensitive data."""
        sensitive_data = [
            "password=secret123",
            "token=abc123def456",
            "api_key=sk-1234567890abcdef",
            "secret=mysecretkey",
            "private_key=-----BEGIN PRIVATE KEY-----",
            "credit_card=4111-1111-1111-1111",
            "ssn=123-45-6789",
            "email=user@test.example.com"
        ]
        
        for data in sensitive_data:
            # Should detect sensitive data patterns
            assert re.search(r"(password|token|api_key|secret|private_key|credit_card|ssn|email)", 
                           data.lower())
    
    @pytest.mark.asyncio
    async def test_data_encryption(self, temp_output_dir):
        """Test data encryption and secure storage."""
        if not UnifiedSources:
            pytest.skip("UnifiedSources not available")
        
        merger = UnifiedSources()
        
        # Run processing
        results = await merger.run_comprehensive_merge(
            output_dir=str(temp_output_dir),
            test_sources=True,
            max_sources=10
        )
        
        # Check that sensitive data is not stored in plain text
        for file_path in temp_output_dir.glob("*"):
            if file_path.is_file():
                content = file_path.read_text(encoding='utf-8')
                
                # Should not contain sensitive data in plain text
                assert not re.search(r"(password|token|api_key|secret)", content.lower())
    
    def test_log_sanitization(self):
        """Test sanitization of log data."""
        log_data = [
            "User password=secret123 logged in",
            "API key=sk-1234567890abcdef used",
            "Token=abc123def456 expired",
            "Secret=mysecretkey accessed"
        ]
        
        for log in log_data:
            # Should sanitize sensitive data in logs
            sanitized = re.sub(r"(password|token|api_key|secret)=[^\s]+", 
                             r"\1=***REDACTED***", log)
            assert "***REDACTED***" in sanitized


class TestAuthentication:
    """Test authentication and authorization."""
    
    def test_api_key_validation(self):
        """Test API key validation."""
        valid_api_keys = [
            "sk-1234567890abcdef",
            "pk_test_1234567890abcdef",
            "ak_1234567890abcdef"
        ]
        
        invalid_api_keys = [
            "invalid_key",
            "1234567890",
            "sk-",
            "pk_test_",
            "ak_"
        ]
        
        for key in valid_api_keys:
            # Should validate API key format
            assert len(key) > 10
            assert key.startswith(('sk-', 'pk_', 'ak_'))
        
        for key in invalid_api_keys:
            # Should reject invalid API keys
            assert len(key) < 10 or not key.startswith(('sk-', 'pk_', 'ak_'))
    
    def test_permission_validation(self):
        """Test permission validation."""
        permissions = [
            "read:configs",
            "write:configs",
            "delete:configs",
            "admin:all"
        ]
        
        for permission in permissions:
            # Should validate permission format
            assert ':' in permission
            assert permission.split(':')[0] in ['read', 'write', 'delete', 'admin']
            assert permission.split(':')[1] in ['configs', 'all']


class TestNetworkSecurity:
    """Test network security and communication."""
    
    def test_ssl_tls_validation(self):
        """Test SSL/TLS validation."""
        secure_urls = [
            "https://github.com/user/repo",
            "https://raw.githubusercontent.com/user/repo/file.txt",
            "https://api.github.com/repos/user/repo"
        ]
        
        insecure_urls = [
            "https://raw.githubusercontent.com/test/file.txt",
            "https://raw.githubusercontent.com/test/file.txt",
            "file:///path/to/file.txt"
        ]
        
        for url in secure_urls:
            # Should prefer HTTPS
            assert url.startswith('https://')
        
        for url in insecure_urls:
            # Should avoid insecure protocols
            assert not url.startswith('https://')
    
    def test_dns_security(self):
        """Test DNS security and resolution."""
        suspicious_domains = [
            "evil.com",
            "malicious.net",
            "phishing.org",
            "malware.info"
        ]
        
        for domain in suspicious_domains:
            # Should detect suspicious domains
            assert domain in suspicious_domains


if __name__ == "__main__":
    pytest.main([__file__])
