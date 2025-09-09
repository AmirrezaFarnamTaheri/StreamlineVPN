#!/usr/bin/env python3
"""
monitor.py
==========

Monitoring and health check script for StreamlineVPN.
"""

import asyncio
import json
import time
import requests
import redis
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from streamline_vpn.utils.logging import get_logger

logger = get_logger(__name__)


class StreamlineVPNMonitor:
    """Monitor StreamlineVPN services and health."""
    
    def __init__(self, api_url: str = "http://localhost:8080", redis_url: str = "redis://localhost:6379"):
        self.api_url = api_url
        self.redis_url = redis_url
        self.redis_client = None
        self.metrics = {
            'api_health': False,
            'redis_health': False,
            'last_check': None,
            'uptime': 0,
            'errors': []
        }
    
    async def check_api_health(self) -> bool:
        """Check API health."""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('status') == 'healthy'
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            self.metrics['errors'].append(f"API: {e}")
        
        return False
    
    async def check_redis_health(self) -> bool:
        """Check Redis health."""
        try:
            if not self.redis_client:
                self.redis_client = redis.from_url(self.redis_url)
            
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            self.metrics['errors'].append(f"Redis: {e}")
        
        return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            response = requests.get(f"{self.api_url}/api/v1/statistics", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
        
        return {}
    
    async def check_jobs(self) -> Dict[str, Any]:
        """Check job status."""
        try:
            response = requests.get(f"{self.api_url}/api/v1/jobs", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get jobs: {e}")
        
        return {}
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run complete health check."""
        logger.info("Running health check...")
        
        # Check services
        api_health = await self.check_api_health()
        redis_health = await self.check_redis_health()
        
        # Update metrics
        self.metrics['api_health'] = api_health
        self.metrics['redis_health'] = redis_health
        self.metrics['last_check'] = datetime.now().isoformat()
        
        # Get additional data
        stats = await self.get_statistics()
        jobs = await self.check_jobs()
        
        # Overall health
        overall_health = api_health and redis_health
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_health': overall_health,
            'services': {
                'api': api_health,
                'redis': redis_health
            },
            'statistics': stats,
            'jobs': jobs,
            'metrics': self.metrics
        }
    
    async def monitor_loop(self, interval: int = 30):
        """Run continuous monitoring."""
        logger.info(f"Starting monitoring loop (interval: {interval}s)")
        
        while True:
            try:
                health_data = await self.run_health_check()
                
                # Log status
                status = "✅ HEALTHY" if health_data['overall_health'] else "❌ UNHEALTHY"
                logger.info(f"System status: {status}")
                
                # Save metrics
                self.save_metrics(health_data)
                
                # Alert on issues
                if not health_data['overall_health']:
                    await self.send_alert(health_data)
                
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval)
    
    def save_metrics(self, data: Dict[str, Any]):
        """Save metrics to file."""
        metrics_file = Path("logs/metrics.json")
        metrics_file.parent.mkdir(exist_ok=True)
        
        # Load existing metrics
        if metrics_file.exists():
            try:
                with open(metrics_file) as f:
                    all_metrics = json.load(f)
            except:
                all_metrics = []
        else:
            all_metrics = []
        
        # Add new data
        all_metrics.append(data)
        
        # Keep only last 1000 entries
        all_metrics = all_metrics[-1000:]
        
        # Save
        with open(metrics_file, 'w') as f:
            json.dump(all_metrics, f, indent=2)
    
    async def send_alert(self, data: Dict[str, Any]):
        """Send alert for unhealthy status."""
        logger.warning("System is unhealthy - sending alert")
        
        # Here you could integrate with:
        # - Email notifications
        # - Slack/Discord webhooks
        # - PagerDuty
        # - Custom alerting system
        
        # For now, just log the alert
        alert_data = {
            'timestamp': data['timestamp'],
            'services': data['services'],
            'errors': self.metrics['errors']
        }
        
        alert_file = Path("logs/alerts.json")
        alert_file.parent.mkdir(exist_ok=True)
        
        if alert_file.exists():
            with open(alert_file) as f:
                alerts = json.load(f)
        else:
            alerts = []
        
        alerts.append(alert_data)
        
        with open(alert_file, 'w') as f:
            json.dump(alerts, f, indent=2)
    
    def generate_report(self) -> str:
        """Generate monitoring report."""
        metrics_file = Path("logs/metrics.json")
        
        if not metrics_file.exists():
            return "No metrics data available"
        
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        if not metrics:
            return "No metrics data available"
        
        # Calculate uptime
        total_checks = len(metrics)
        healthy_checks = sum(1 for m in metrics if m['overall_health'])
        uptime_percent = (healthy_checks / total_checks) * 100
        
        # Get latest data
        latest = metrics[-1]
        
        report = f"""
StreamlineVPN Monitoring Report
==============================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Overall Status: {'✅ HEALTHY' if latest['overall_health'] else '❌ UNHEALTHY'}
Uptime: {uptime_percent:.1f}% ({healthy_checks}/{total_checks} checks)

Services:
  API: {'✅' if latest['services']['api'] else '❌'}
  Redis: {'✅' if latest['services']['redis'] else '❌'}

Statistics:
  Sources: {latest['statistics'].get('total_sources', 'N/A')}
  Configurations: {latest['statistics'].get('total_configs', 'N/A')}
  Success Rate: {latest['statistics'].get('success_rate', 0)*100:.1f}%

Recent Errors:
"""
        
        if latest['metrics']['errors']:
            for error in latest['metrics']['errors'][-5:]:  # Last 5 errors
                report += f"  - {error}\n"
        else:
            report += "  None\n"
        
        return report


async def main():
    """Main monitoring function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='StreamlineVPN Monitor')
    parser.add_argument('--interval', '-i', type=int, default=30, help='Check interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run once instead of continuously')
    parser.add_argument('--report', action='store_true', help='Generate and print report')
    
    args = parser.parse_args()
    
    monitor = StreamlineVPNMonitor()
    
    if args.report:
        print(monitor.generate_report())
        return
    
    if args.once:
        health_data = await monitor.run_health_check()
        print(json.dumps(health_data, indent=2))
    else:
        await monitor.monitor_loop(args.interval)


if __name__ == '__main__':
    asyncio.run(main())
