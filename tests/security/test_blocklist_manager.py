"""
Tests for BlocklistManager.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.security.blocklist_manager import BlocklistManager


class TestBlocklistManager:
    """Test BlocklistManager class"""
    
    def test_initialization(self):
        """Test blocklist manager initialization"""
        manager = BlocklistManager()
        assert hasattr(manager, 'blocked_ips')
        assert hasattr(manager, 'blocked_domains')
        assert hasattr(manager, 'blocked_patterns')
    
    def test_add_blocked_ip(self):
        """Test adding blocked IP"""
        manager = BlocklistManager()
        manager.add_blocked_ip("192.168.1.1", "Test reason")
        assert "192.168.1.1" in manager.blocked_ips
        assert manager.blocked_ips["192.168.1.1"] == "Test reason"
    
    def test_remove_blocked_ip(self):
        """Test removing blocked IP"""
        manager = BlocklistManager()
        manager.add_blocked_ip("192.168.1.1", "Test reason")
        assert "192.168.1.1" in manager.blocked_ips
        
        manager.remove_blocked_ip("192.168.1.1")
        assert "192.168.1.1" not in manager.blocked_ips
    
    def test_is_ip_blocked(self):
        """Test checking if IP is blocked"""
        manager = BlocklistManager()
        manager.add_blocked_ip("192.168.1.1", "Test reason")
        
        assert manager.is_ip_blocked("192.168.1.1") is True
        assert manager.is_ip_blocked("192.168.1.2") is False
    
    def test_add_blocked_domain(self):
        """Test adding blocked domain"""
        manager = BlocklistManager()
        manager.add_blocked_domain("example.com", "Malicious domain")
        assert "example.com" in manager.blocked_domains
        assert manager.blocked_domains["example.com"] == "Malicious domain"
    
    def test_remove_blocked_domain(self):
        """Test removing blocked domain"""
        manager = BlocklistManager()
        manager.add_blocked_domain("example.com", "Malicious domain")
        assert "example.com" in manager.blocked_domains
        
        manager.remove_blocked_domain("example.com")
        assert "example.com" not in manager.blocked_domains
    
    def test_is_domain_blocked(self):
        """Test checking if domain is blocked"""
        manager = BlocklistManager()
        manager.add_blocked_domain("example.com", "Malicious domain")
        
        assert manager.is_domain_blocked("example.com") is True
        assert manager.is_domain_blocked("google.com") is False
    
    def test_add_blocked_pattern(self):
        """Test adding blocked pattern"""
        manager = BlocklistManager()
        manager.add_blocked_pattern("malware*", "Malware pattern")
        assert "malware*" in manager.blocked_patterns
        assert manager.blocked_patterns["malware*"] == "Malware pattern"
    
    def test_remove_blocked_pattern(self):
        """Test removing blocked pattern"""
        manager = BlocklistManager()
        manager.add_blocked_pattern("malware*", "Malware pattern")
        assert "malware*" in manager.blocked_patterns
        
        manager.remove_blocked_pattern("malware*")
        assert "malware*" not in manager.blocked_patterns
    
    def test_is_pattern_blocked(self):
        """Test checking if pattern is blocked"""
        manager = BlocklistManager()
        manager.add_blocked_pattern("malware*", "Malware pattern")
        
        assert manager.is_pattern_blocked("malware.exe") is True
        assert manager.is_pattern_blocked("legitimate.exe") is False
    
    def test_get_blocked_count(self):
        """Test getting blocked item count"""
        manager = BlocklistManager()
        assert manager.get_blocked_count() == 0
        
        manager.add_blocked_ip("192.168.1.1", "Test")
        manager.add_blocked_domain("example.com", "Test")
        manager.add_blocked_pattern("test*", "Test")
        
        assert manager.get_blocked_count() == 3
    
    def test_clear_all(self):
        """Test clearing all blocked items"""
        manager = BlocklistManager()
        manager.add_blocked_ip("192.168.1.1", "Test")
        manager.add_blocked_domain("example.com", "Test")
        manager.add_blocked_pattern("test*", "Test")
        
        assert manager.get_blocked_count() == 3
        
        manager.clear_all()
        assert manager.get_blocked_count() == 0

