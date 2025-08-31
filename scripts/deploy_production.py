#!/usr/bin/env python3
"""
Production Deployment Script for VPN Subscription Merger
Sets up monitoring, health checks, and production deployment
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from vpn_merger import VPNMerger, UnifiedSources, ConfigResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ProductionDeployment:
    """Production deployment manager with monitoring and health checks."""
    
    def __init__(self):
        self.merger = VPNMerger()
        self.sources = UnifiedSources()
        self.metrics = {
            'start_time': datetime.now(),
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_configs_processed': 0,
            'average_processing_time': 0.0,
            'last_run_time': None,
            'health_status': 'healthy'
        }
        
    async def health_check(self) -> Dict[str, any]:
        """Perform comprehensive health check."""
        logger.info("🔍 Performing health check...")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'checks': {}
        }
        
        # Check sources availability
        try:
            all_sources = self.sources.get_all_sources()
            health_status['checks']['sources'] = {
                'status': 'healthy',
                'total_sources': len(all_sources),
                'message': f"Loaded {len(all_sources)} sources successfully"
            }
        except Exception as e:
            health_status['checks']['sources'] = {
                'status': 'unhealthy',
                'error': str(e),
                'message': "Failed to load sources"
            }
            health_status['status'] = 'unhealthy'
        
        # Check VPNMerger initialization
        try:
            merger_stats = self.merger.get_statistics()
            health_status['checks']['merger'] = {
                'status': 'healthy',
                'stats': merger_stats,
                'message': "VPNMerger initialized successfully"
            }
        except Exception as e:
            health_status['checks']['merger'] = {
                'status': 'unhealthy',
                'error': str(e),
                'message': "Failed to initialize VPNMerger"
            }
            health_status['status'] = 'unhealthy'
        
        # Check output directory
        output_dir = Path("output")
        try:
            output_dir.mkdir(exist_ok=True)
            health_status['checks']['output_directory'] = {
                'status': 'healthy',
                'path': str(output_dir.absolute()),
                'writable': os.access(output_dir, os.W_OK),
                'message': "Output directory is accessible and writable"
            }
        except Exception as e:
            health_status['checks']['output_directory'] = {
                'status': 'unhealthy',
                'error': str(e),
                'message': "Output directory check failed"
            }
            health_status['status'] = 'unhealthy'
        
        # Update global health status
        self.metrics['health_status'] = health_status['status']
        
        logger.info(f"Health check completed: {health_status['status']}")
        return health_status
    
    async def run_production_merge(self, max_sources: int = 50) -> Dict[str, any]:
        """Run production merge with monitoring."""
        logger.info(f"🚀 Starting production merge with max {max_sources} sources...")
        
        start_time = time.time()
        self.metrics['total_runs'] += 1
        
        try:
            # Get prioritized sources
            sources = self.sources.get_prioritized_sources()[:max_sources]
            logger.info(f"Processing {len(sources)} sources...")
            
            # Run comprehensive merge
            results = await self.merger.run_comprehensive_merge()
            
            # Save results
            if results:
                self.merger.save_results(results, output_dir="output")
            
            # Calculate metrics
            processing_time = time.time() - start_time
            total_configs = len(results) if results else 0
            
            # Update metrics
            self.metrics['successful_runs'] += 1
            self.metrics['total_configs_processed'] += total_configs
            self.metrics['last_run_time'] = datetime.now()
            
            # Update average processing time
            if self.metrics['total_runs'] > 1:
                self.metrics['average_processing_time'] = (
                    (self.metrics['average_processing_time'] * (self.metrics['total_runs'] - 1) + processing_time) 
                    / self.metrics['total_runs']
                )
            else:
                self.metrics['average_processing_time'] = processing_time
            
            # Generate report
            report = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'processing_time': processing_time,
                'total_configs': total_configs,
                'sources_processed': len(sources),
                'output_files': self._get_output_files(),
                'metrics': self.metrics.copy()
            }
            
            logger.info(f"✅ Production merge completed successfully in {processing_time:.2f}s")
            logger.info(f"📊 Processed {total_configs} configs from {len(sources)} sources")
            
            return report
            
        except Exception as e:
            self.metrics['failed_runs'] += 1
            logger.error(f"❌ Production merge failed: {e}")
            
            return {
                'status': 'failed',
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'processing_time': time.time() - start_time,
                'metrics': self.metrics.copy()
            }
    
    def _get_output_files(self) -> Dict[str, bool]:
        """Get status of output files."""
        output_dir = Path("output")
        files = {
            'vpn_subscription_raw.txt': False,
            'vpn_subscription_base64.txt': False,
            'vpn_detailed.csv': False,
            'vpn_report.json': False,
            'vpn_singbox.json': False
        }
        
        for filename in files:
            file_path = output_dir / filename
            files[filename] = file_path.exists() and file_path.stat().st_size > 0
        
        return files
    
    async def continuous_monitoring(self, interval_minutes: int = 60):
        """Run continuous monitoring with periodic health checks and merges."""
        logger.info(f"🔄 Starting continuous monitoring (interval: {interval_minutes} minutes)")
        
        while True:
            try:
                # Health check
                health = await self.health_check()
                
                if health['status'] == 'healthy':
                    # Run production merge
                    result = await self.run_production_merge(max_sources=50)
                    
                    # Log results
                    if result['status'] == 'success':
                        logger.info(f"✅ Merge successful: {result['total_configs']} configs")
                    else:
                        logger.error(f"❌ Merge failed: {result['error']}")
                else:
                    logger.warning(f"⚠️ System unhealthy, skipping merge: {health['status']}")
                
                # Wait for next interval
                logger.info(f"⏰ Waiting {interval_minutes} minutes until next run...")
                await asyncio.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Continuous monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def get_system_metrics(self) -> Dict[str, any]:
        """Get comprehensive system metrics."""
        uptime = datetime.now() - self.metrics['start_time']
        
        return {
            'system_info': {
                'uptime': str(uptime),
                'start_time': self.metrics['start_time'].isoformat(),
                'health_status': self.metrics['health_status']
            },
            'performance_metrics': {
                'total_runs': self.metrics['total_runs'],
                'successful_runs': self.metrics['successful_runs'],
                'failed_runs': self.metrics['failed_runs'],
                'success_rate': self.metrics['successful_runs'] / max(self.metrics['total_runs'], 1),
                'total_configs_processed': self.metrics['total_configs_processed'],
                'average_processing_time': self.metrics['average_processing_time'],
                'last_run_time': self.metrics['last_run_time'].isoformat() if self.metrics['last_run_time'] else None
            },
            'source_metrics': {
                'total_sources': len(self.sources.get_all_sources()),
                'prioritized_sources': len(self.sources.get_prioritized_sources())
            }
        }

async def main():
    """Main deployment function."""
    logger.info("🚀 Starting VPN Subscription Merger Production Deployment")
    
    # Initialize deployment
    deployment = ProductionDeployment()
    
    # Initial health check
    health = await deployment.health_check()
    logger.info(f"Initial health status: {health['status']}")
    
    if health['status'] != 'healthy':
        logger.error("❌ System unhealthy, cannot proceed with deployment")
        return 1
    
    # Run initial production merge
    logger.info("🔄 Running initial production merge...")
    result = await deployment.run_production_merge(max_sources=30)
    
    if result['status'] == 'success':
        logger.info("✅ Initial deployment successful!")
        
        # Display metrics
        metrics = deployment.get_system_metrics()
        logger.info("📊 System Metrics:")
        logger.info(f"   - Total configs processed: {metrics['performance_metrics']['total_configs_processed']}")
        logger.info(f"   - Average processing time: {metrics['performance_metrics']['average_processing_time']:.2f}s")
        logger.info(f"   - Success rate: {metrics['performance_metrics']['success_rate']:.2%}")
        
        # Start continuous monitoring (optional)
        if len(sys.argv) > 1 and sys.argv[1] == '--monitor':
            await deployment.continuous_monitoring(interval_minutes=60)
        
        return 0
    else:
        logger.error(f"❌ Initial deployment failed: {result['error']}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        sys.exit(1)
