"""
Tests for PatternAnalyzer.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from streamline_vpn.security.pattern_analyzer import PatternAnalyzer


class TestPatternAnalyzer:
    """Test PatternAnalyzer class"""
    
    def test_initialization(self):
        """Test pattern analyzer initialization"""
        analyzer = PatternAnalyzer()
        assert hasattr(analyzer, 'patterns')
        assert hasattr(analyzer, 'threshold')
    
    def test_add_pattern(self):
        """Test adding pattern"""
        analyzer = PatternAnalyzer()
        analyzer.add_pattern("test_pattern", "Test pattern", 0.8)
        assert "test_pattern" in analyzer.patterns
        assert analyzer.patterns["test_pattern"]["description"] == "Test pattern"
        assert analyzer.patterns["test_pattern"]["confidence"] == 0.8
    
    def test_remove_pattern(self):
        """Test removing pattern"""
        analyzer = PatternAnalyzer()
        analyzer.add_pattern("test_pattern", "Test pattern", 0.8)
        assert "test_pattern" in analyzer.patterns
        
        analyzer.remove_pattern("test_pattern")
        assert "test_pattern" not in analyzer.patterns
    
    def test_analyze_text(self):
        """Test analyzing text for patterns"""
        analyzer = PatternAnalyzer()
        analyzer.add_pattern("malware", "Malware pattern", 0.9)
        analyzer.add_pattern("phishing", "Phishing pattern", 0.7)
        
        # Test with matching text
        result = analyzer.analyze_text("This is malware content")
        assert result["matches"] > 0
        assert "malware" in result["patterns"]
        
        # Test with non-matching text
        result = analyzer.analyze_text("This is normal content")
        assert result["matches"] == 0
    
    def test_get_pattern_count(self):
        """Test getting pattern count"""
        analyzer = PatternAnalyzer()
        assert analyzer.get_pattern_count() == 0
        
        analyzer.add_pattern("pattern1", "Test 1", 0.8)
        analyzer.add_pattern("pattern2", "Test 2", 0.9)
        
        assert analyzer.get_pattern_count() == 2
    
    def test_clear_patterns(self):
        """Test clearing all patterns"""
        analyzer = PatternAnalyzer()
        analyzer.add_pattern("pattern1", "Test 1", 0.8)
        analyzer.add_pattern("pattern2", "Test 2", 0.9)
        
        assert analyzer.get_pattern_count() == 2
        
        analyzer.clear_patterns()
        assert analyzer.get_pattern_count() == 0

