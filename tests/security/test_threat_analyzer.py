"""
Tests for ThreatAnalyzer.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.security.threat_analyzer import ThreatAnalyzer


class TestThreatAnalyzer:
    """Test ThreatAnalyzer class"""
    
    def test_initialization(self):
        """Test threat analyzer initialization"""
        analyzer = ThreatAnalyzer()
        assert hasattr(analyzer, 'threat_patterns')
        assert hasattr(analyzer, 'risk_levels')
    
    def test_add_threat_pattern(self):
        """Test adding threat pattern"""
        analyzer = ThreatAnalyzer()
        analyzer.add_threat_pattern("malware", "Malware pattern", "high")
        assert "malware" in analyzer.threat_patterns
        assert analyzer.threat_patterns["malware"]["description"] == "Malware pattern"
        assert analyzer.threat_patterns["malware"]["risk_level"] == "high"
    
    def test_remove_threat_pattern(self):
        """Test removing threat pattern"""
        analyzer = ThreatAnalyzer()
        analyzer.add_threat_pattern("malware", "Malware pattern", "high")
        assert "malware" in analyzer.threat_patterns
        
        analyzer.remove_threat_pattern("malware")
        assert "malware" not in analyzer.threat_patterns
    
    def test_analyze_threat(self):
        """Test analyzing threat"""
        analyzer = ThreatAnalyzer()
        analyzer.add_threat_pattern("malware", "Malware pattern", "high")
        analyzer.add_threat_pattern("phishing", "Phishing pattern", "medium")
        
        # Test with high-risk content
        result = analyzer.analyze_threat("This contains malware")
        assert result["risk_level"] == "high"
        assert result["threats_detected"] > 0
        assert "malware" in result["threats"]
        
        # Test with medium-risk content
        result = analyzer.analyze_threat("This is a phishing attempt")
        assert result["risk_level"] == "medium"
        assert result["threats_detected"] > 0
        assert "phishing" in result["threats"]
        
        # Test with safe content
        result = analyzer.analyze_threat("This is normal content")
        assert result["risk_level"] == "none"
        assert result["threats_detected"] == 0
    
    def test_get_threat_count(self):
        """Test getting threat pattern count"""
        analyzer = ThreatAnalyzer()
        assert analyzer.get_threat_count() == 0
        
        analyzer.add_threat_pattern("pattern1", "Test 1", "high")
        analyzer.add_threat_pattern("pattern2", "Test 2", "medium")
        
        assert analyzer.get_threat_count() == 2
    
    def test_clear_threats(self):
        """Test clearing all threat patterns"""
        analyzer = ThreatAnalyzer()
        analyzer.add_threat_pattern("pattern1", "Test 1", "high")
        analyzer.add_threat_pattern("pattern2", "Test 2", "medium")
        
        assert analyzer.get_threat_count() == 2
        
        analyzer.clear_threats()
        assert analyzer.get_threat_count() == 0

