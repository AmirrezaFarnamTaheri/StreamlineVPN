#!/usr/bin/env python3
"""
Performance Monitoring Script for VPN Subscription Merger
Provides real-time metrics, performance insights, and monitoring dashboard
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from vpn_merger import VPNSubscriptionMerger, SourceManager, ConfigurationProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Real-time performance monitoring and metrics collection."""
    
    def __init__(self):
        self.merger = VPNSubscriptionMerger()
        self.sources = SourceManager()
        self.metrics_history = []
        self.performance_data = {
            'start_time': datetime.now(),
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'total_configs_processed': 0,
            'average_processing_time': 0.0,
            'peak_processing_time': 0.0,
            'source_availability': {},
            'error_counts': {},
            'performance_trends': []
        }
    
    async def collect_metrics(self) -> Dict[str, any]:
        """Collect comprehensive system metrics."""
        logger.info("📊 Collecting system metrics...")
        
        current_time = datetime.now()
        
        # Get merger statistics
        try:
            merger_stats = self.merger.get_statistics()
        except Exception as e:
            logger.warning(f"Could not get merger stats: {e}")
            merger_stats = {}
        
        # Get source metrics
        try:
            all_sources = self.sources.get_all_sources()
            prioritized_sources = self.sources.get_prioritized_sources()
        except Exception as e:
            logger.warning(f"Could not get source metrics: {e}")
            all_sources = []
            prioritized_sources = []
        
        # Check output files
        output_files = self._check_output_files()
        
        # Calculate performance metrics
        uptime = current_time - self.performance_data['start_time']
        success_rate = (
            self.performance_data['successful_operations'] / 
            max(self.performance_data['total_operations'], 1)
        )
        
        metrics = {
            'timestamp': current_time.isoformat(),
            'system_info': {
                'uptime': str(uptime),
                'start_time': self.performance_data['start_time'].isoformat(),
                'version': '2.0'
            },
            'performance_metrics': {
                'total_operations': self.performance_data['total_operations'],
                'successful_operations': self.performance_data['successful_operations'],
                'failed_operations': self.performance_data['failed_operations'],
                'success_rate': success_rate,
                'total_configs_processed': self.performance_data['total_configs_processed'],
                'average_processing_time': self.performance_data['average_processing_time'],
                'peak_processing_time': self.performance_data['peak_processing_time']
            },
            'source_metrics': {
                'total_sources': len(all_sources),
                'prioritized_sources': len(prioritized_sources),
                'source_availability': self.performance_data['source_availability']
            },
            'output_status': output_files,
            'merger_stats': merger_stats,
            'error_summary': self.performance_data['error_counts']
        }
        
        # Store in history (keep last 100 entries)
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)
        
        return metrics
    
    def _check_output_files(self) -> Dict[str, any]:
        """Check status of output files."""
        output_dir = Path("output")
        files = {
            'vpn_subscription_raw.txt': {'exists': False, 'size': 0, 'last_modified': None},
            'vpn_subscription_base64.txt': {'exists': False, 'size': 0, 'last_modified': None},
            'vpn_detailed.csv': {'exists': False, 'size': 0, 'last_modified': None},
            'vpn_report.json': {'exists': False, 'size': 0, 'last_modified': None},
            'vpn_singbox.json': {'exists': False, 'size': 0, 'last_modified': None}
        }
        
        for filename in files:
            file_path = output_dir / filename
            if file_path.exists():
                stat = file_path.stat()
                files[filename] = {
                    'exists': True,
                    'size': stat.st_size,
                    'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
        
        return files
    
    async def run_performance_test(self, test_sources: int = 10) -> Dict[str, any]:
        """Run a performance test with a subset of sources."""
        logger.info(f"🧪 Running performance test with {test_sources} sources...")
        
        start_time = time.time()
        self.performance_data['total_operations'] += 1
        
        try:
            # Get test sources
            sources = self.sources.get_prioritized_sources()[:test_sources]
            
            # Run test merge
            results = await self.merger.run_comprehensive_merge()
            
            # Save results
            if results:
                self.merger.save_results(results, output_dir="output_test")
            
            # Calculate metrics
            processing_time = time.time() - start_time
            total_configs = len(results) if results else 0
            
            # Update performance data
            self.performance_data['successful_operations'] += 1
            self.performance_data['total_configs_processed'] += total_configs
            
            # Update processing time metrics
            if self.performance_data['total_operations'] > 1:
                self.performance_data['average_processing_time'] = (
                    (self.performance_data['average_processing_time'] * (self.performance_data['total_operations'] - 1) + processing_time) 
                    / self.performance_data['total_operations']
                )
            else:
                self.performance_data['average_processing_time'] = processing_time
            
            # Update peak processing time
            if processing_time > self.performance_data['peak_processing_time']:
                self.performance_data['peak_processing_time'] = processing_time
            
            # Store performance trend
            trend = {
                'timestamp': datetime.now().isoformat(),
                'processing_time': processing_time,
                'configs_processed': total_configs,
                'sources_processed': len(sources)
            }
            self.performance_data['performance_trends'].append(trend)
            
            # Keep only last 50 trends
            if len(self.performance_data['performance_trends']) > 50:
                self.performance_data['performance_trends'].pop(0)
            
            logger.info(f"✅ Performance test completed in {processing_time:.2f}s")
            
            return {
                'status': 'success',
                'processing_time': processing_time,
                'total_configs': total_configs,
                'sources_processed': len(sources),
                'configs_per_second': total_configs / processing_time if processing_time > 0 else 0
            }
            
        except Exception as e:
            self.performance_data['failed_operations'] += 1
            error_type = type(e).__name__
            self.performance_data['error_counts'][error_type] = self.performance_data['error_counts'].get(error_type, 0) + 1
            
            logger.error(f"❌ Performance test failed: {e}")
            
            return {
                'status': 'failed',
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def generate_performance_report(self) -> Dict[str, any]:
        """Generate comprehensive performance report."""
        current_metrics = self.performance_data
        
        # Calculate trends
        if len(self.performance_data['performance_trends']) >= 2:
            recent_trends = self.performance_data['performance_trends'][-10:]
            avg_processing_time = sum(t['processing_time'] for t in recent_trends) / len(recent_trends)
            avg_configs_per_second = sum(t['configs_processed'] / t['processing_time'] for t in recent_trends if t['processing_time'] > 0) / len(recent_trends)
        else:
            avg_processing_time = 0
            avg_configs_per_second = 0
        
        report = {
            'report_generated': datetime.now().isoformat(),
            'summary': {
                'total_operations': current_metrics['total_operations'],
                'success_rate': current_metrics['successful_operations'] / max(current_metrics['total_operations'], 1),
                'total_configs_processed': current_metrics['total_configs_processed'],
                'uptime': str(datetime.now() - current_metrics['start_time'])
            },
            'performance_analysis': {
                'average_processing_time': current_metrics['average_processing_time'],
                'peak_processing_time': current_metrics['peak_processing_time'],
                'recent_avg_processing_time': avg_processing_time,
                'recent_avg_configs_per_second': avg_configs_per_second,
                'performance_trend': 'improving' if avg_processing_time < current_metrics['average_processing_time'] else 'stable'
            },
            'error_analysis': {
                'total_errors': current_metrics['failed_operations'],
                'error_distribution': current_metrics['error_counts'],
                'most_common_error': max(current_metrics['error_counts'].items(), key=lambda x: x[1])[0] if current_metrics['error_counts'] else None
            },
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        success_rate = self.performance_data['successful_operations'] / max(self.performance_data['total_operations'], 1)
        if success_rate < 0.8:
            recommendations.append("⚠️ Success rate is below 80%. Consider reviewing source reliability and error handling.")
        
        if self.performance_data['average_processing_time'] > 60:
            recommendations.append("🐌 Average processing time is high. Consider optimizing source processing or reducing concurrent operations.")
        
        if self.performance_data['peak_processing_time'] > 120:
            recommendations.append("🔥 Peak processing time is very high. Consider implementing better timeout handling and circuit breakers.")
        
        if not recommendations:
            recommendations.append("✅ System performance is within acceptable parameters.")
        
        return recommendations
    
    async def continuous_monitoring(self, interval_seconds: int = 30):
        """Run continuous monitoring with real-time metrics collection."""
        logger.info(f"🔄 Starting continuous monitoring (interval: {interval_seconds}s)")
        
        while True:
            try:
                # Collect metrics
                metrics = await self.collect_metrics()
                
                # Display real-time status
                self._display_status(metrics)
                
                # Save metrics to file
                self._save_metrics(metrics)
                
                # Wait for next interval
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("🛑 Continuous monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(10)
    
    def _display_status(self, metrics: Dict[str, any]):
        """Display real-time status."""
        success_rate = metrics['performance_metrics']['success_rate']
        total_configs = metrics['performance_metrics']['total_configs_processed']
        avg_time = metrics['performance_metrics']['average_processing_time']
        
        status_emoji = "✅" if success_rate > 0.8 else "⚠️" if success_rate > 0.6 else "❌"
        
        print(f"\n{status_emoji} VPN Merger Status - {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Success Rate: {success_rate:.1%}")
        print(f"   Total Configs: {total_configs:,}")
        print(f"   Avg Processing Time: {avg_time:.2f}s")
        print(f"   Sources Available: {metrics['source_metrics']['total_sources']}")
        
        # Show recent errors if any
        if metrics['error_summary']:
            print(f"   Recent Errors: {sum(metrics['error_summary'].values())}")
    
    def _save_metrics(self, metrics: Dict[str, any]):
        """Save metrics to file for historical analysis."""
        metrics_file = Path("output/metrics_history.json")
        metrics_file.parent.mkdir(exist_ok=True)
        
        try:
            # Load existing metrics
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    history = json.load(f)
            else:
                history = []
            
            # Add new metrics
            history.append(metrics)
            
            # Keep only last 1000 entries
            if len(history) > 1000:
                history = history[-1000:]
            
            # Save updated history
            with open(metrics_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Could not save metrics: {e}")

async def main():
    """Main monitoring function."""
    logger.info("📊 Starting VPN Subscription Merger Performance Monitor")
    
    monitor = PerformanceMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'test':
            # Run performance test
            result = await monitor.run_performance_test(test_sources=20)
            print(f"Performance Test Result: {result}")
            
        elif command == 'report':
            # Generate performance report
            report = monitor.generate_performance_report()
            print(json.dumps(report, indent=2))
            
        elif command == 'monitor':
            # Start continuous monitoring
            await monitor.continuous_monitoring(interval_seconds=30)
            
        else:
            print("Usage: python monitor_performance.py [test|report|monitor]")
            return 1
    else:
        # Default: collect current metrics
        metrics = await monitor.collect_metrics()
        print(json.dumps(metrics, indent=2))
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Monitoring interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Monitoring failed: {e}")
        sys.exit(1)
