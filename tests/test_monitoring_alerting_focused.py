"""
Focused tests for Monitoring Alerting
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamline_vpn.monitoring.alerting_rules import AlertingRules


class TestAlertingRules:
    """Test AlertingRules class"""
    
    def test_initialization(self):
        """Test alerting rules initialization"""
        rules = AlertingRules()
        assert hasattr(rules, 'rules')
        assert hasattr(rules, 'alert_thresholds')
        assert hasattr(rules, 'is_monitoring')
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test alerting rules initialization"""
        rules = AlertingRules()
        result = await rules.initialize()
        assert result is True
    
    def test_add_rule(self):
        """Test adding alerting rule"""
        rules = AlertingRules()
        
        with patch.object(rules, 'add_rule') as mock_add:
            mock_add.return_value = True
            
            result = rules.add_rule("cpu_high", "cpu_usage > 80", "warning")
            assert result is True
            mock_add.assert_called_once_with("cpu_high", "cpu_usage > 80", "warning")
    
    def test_remove_rule(self):
        """Test removing alerting rule"""
        rules = AlertingRules()
        
        with patch.object(rules, 'remove_rule') as mock_remove:
            mock_remove.return_value = True
            
            result = rules.remove_rule("cpu_high")
            assert result is True
            mock_remove.assert_called_once_with("cpu_high")
    
    def test_check_rules(self):
        """Test checking alerting rules"""
        rules = AlertingRules()
        
        metrics = {"cpu_usage": 90, "memory_usage": 70}
        
        with patch.object(rules, 'check_rules') as mock_check:
            mock_check.return_value = {
                "alerts_triggered": 1,
                "alerts": [{"rule": "cpu_high", "severity": "warning"}]
            }
            
            result = rules.check_rules(metrics)
            assert result["alerts_triggered"] == 1
            assert len(result["alerts"]) == 1
            mock_check.assert_called_once_with(metrics)
    
    def test_set_alert_threshold(self):
        """Test setting alert threshold"""
        rules = AlertingRules()
        
        with patch.object(rules, 'set_alert_threshold') as mock_set:
            mock_set.return_value = None
            
            rules.set_alert_threshold("cpu_usage", 80.0)
            mock_set.assert_called_once_with("cpu_usage", 80.0)
    
    def test_get_alert_threshold(self):
        """Test getting alert threshold"""
        rules = AlertingRules()
        
        with patch.object(rules, 'get_alert_threshold') as mock_get:
            mock_get.return_value = 80.0
            
            result = rules.get_alert_threshold("cpu_usage")
            assert result == 80.0
            mock_get.assert_called_once_with("cpu_usage")
    
    def test_start_monitoring(self):
        """Test starting monitoring"""
        rules = AlertingRules()
        
        with patch.object(rules, 'start_monitoring') as mock_start:
            mock_start.return_value = None
            
            result = rules.start_monitoring()
            assert result is None
            mock_start.assert_called_once()
    
    def test_stop_monitoring(self):
        """Test stopping monitoring"""
        rules = AlertingRules()
        
        with patch.object(rules, 'stop_monitoring') as mock_stop:
            mock_stop.return_value = None
            
            result = rules.stop_monitoring()
            assert result is None
            mock_stop.assert_called_once()
    
    def test_get_rules_status(self):
        """Test getting rules status"""
        rules = AlertingRules()
        
        with patch.object(rules, 'get_rules_status') as mock_status:
            mock_status.return_value = {
                "total_rules": 5,
                "active_rules": 3,
                "monitoring_active": True
            }
            
            result = rules.get_rules_status()
            assert "total_rules" in result
            assert "active_rules" in result
            assert "monitoring_active" in result
            mock_status.assert_called_once()
    
    def test_clear_rules(self):
        """Test clearing all rules"""
        rules = AlertingRules()
        
        with patch.object(rules, 'clear_rules') as mock_clear:
            mock_clear.return_value = None
            
            result = rules.clear_rules()
            assert result is None
            mock_clear.assert_called_once()
