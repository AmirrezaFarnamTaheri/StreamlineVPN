"""
Alerting Rules
==============

VPN alerting rules for Prometheus monitoring.
"""

from typing import Dict, Any


class AlertingRules:
    """VPN alerting rules for Prometheus."""
    
    def __init__(self):
        """Initialize alerting rules."""
        self.rules = {
            "vpn_server_down": {
                "condition": "up{job='vpn-server'} == 0",
                "duration": "5m",
                "severity": "critical",
                "summary": "VPN server {{ $labels.instance }} is down",
                "description": "VPN server {{ $labels.instance }} has been down for more than 5 minutes"
            },
            "high_vpn_latency": {
                "condition": "vpn_connection_latency_seconds > 0.5",
                "duration": "2m",
                "severity": "warning",
                "summary": "High VPN latency on {{ $labels.server }}",
                "description": "VPN latency on {{ $labels.server }} is {{ $value }}s"
            },
            "high_packet_loss": {
                "condition": "vpn_packet_loss_rate > 0.05",
                "duration": "1m",
                "severity": "warning",
                "summary": "High packet loss on {{ $labels.server }}",
                "description": "Packet loss rate on {{ $labels.server }} is {{ $value }}%"
            },
            "server_cpu_high": {
                "condition": "vpn_server_cpu_usage > 80",
                "duration": "5m",
                "severity": "warning",
                "summary": "High CPU usage on {{ $labels.server }}",
                "description": "CPU usage on {{ $labels.server }} is {{ $value }}%"
            },
            "server_memory_high": {
                "condition": "vpn_server_memory_usage > 90",
                "duration": "2m",
                "severity": "critical",
                "summary": "High memory usage on {{ $labels.server }}",
                "description": "Memory usage on {{ $labels.server }} is {{ $value }}%"
            },
            "cache_hit_rate_low": {
                "condition": "rate(cache_hits_total[5m]) / rate(cache_hits_total[5m] + cache_misses_total[5m]) < 0.8",
                "duration": "5m",
                "severity": "warning",
                "summary": "Low cache hit rate",
                "description": "Cache hit rate is {{ $value }}%"
            }
        }
    
    def get_prometheus_rules(self) -> str:
        """Get alerting rules in Prometheus format."""
        rules_yaml = """
groups:
  - name: vpn_alerts
    rules:
"""
        
        for rule_name, rule_data in self.rules.items():
            rules_yaml += f"""
      - alert: {rule_name.replace('_', '').title()}
        expr: {rule_data['condition']}
        for: {rule_data['duration']}
        labels:
          severity: {rule_data['severity']}
        annotations:
          summary: "{rule_data['summary']}"
          description: "{rule_data['description']}"
"""
        
        return rules_yaml
    
    def get_rule(self, rule_name: str) -> Dict[str, Any]:
        """Get a specific alerting rule.
        
        Args:
            rule_name: Name of the rule to retrieve
            
        Returns:
            Rule configuration or empty dict if not found
        """
        return self.rules.get(rule_name, {})
    
    def add_rule(self, rule_name: str, rule_config: Dict[str, Any]) -> None:
        """Add a new alerting rule.
        
        Args:
            rule_name: Name of the rule
            rule_config: Rule configuration
        """
        self.rules[rule_name] = rule_config
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove an alerting rule.
        
        Args:
            rule_name: Name of the rule to remove
            
        Returns:
            True if rule was removed, False if not found
        """
        if rule_name in self.rules:
            del self.rules[rule_name]
            return True
        return False
