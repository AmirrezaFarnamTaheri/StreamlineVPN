#!/usr/bin/env python3
"""
Enhanced Integration Demo for VPN Configuration Merger
=====================================================

This script demonstrates the integration of all new enhancements:
- Machine Learning Integration
- Advanced Caching Strategy
- Geographic Optimization
- Real-time Source Discovery
- Advanced Analytics Dashboard

Usage:
    python scripts/enhanced_integration_demo.py
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import enhanced modules
# Import existing modules
from vpn_merger import ConfigurationProcessor, SourceManager, VPNSubscriptionMerger
from vpn_merger.analytics.advanced_dashboard import AnalyticsDashboard, DashboardMetrics
from vpn_merger.cache.predictive_cache_warmer import PredictiveCacheWarmer
from vpn_merger.discovery.real_time_discovery import RealTimeDiscovery
from vpn_merger.geo.geographic_optimizer import GeographicOptimizer, GeoLocation
from vpn_merger.ml.quality_predictor_enhanced import (
    EnhancedConfigQualityPredictor,
    train_production_model,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_SOURCES = 50
DEFAULT_MONITORING_INTERVAL = 30  # minutes
DEFAULT_DASHBOARD_PORT = 8080
DEFAULT_REDIS_URL = "redis://localhost:6379"

# Sample configuration data for testing
SAMPLE_CONFIGS = [
    "vmess://eyJhZGQiOiAidGVzdC1zZXJ2ZXIuZXhhbXBsZS5jb20iLCAicG9ydCI6IDQ0MywgInByb3RvY29sIjogInZtZXNzIn0=",
    "vless://dGVzdC1zZXJ2ZXIuZXhhbXBsZS5jb20tNDQzLXRjcC1ub25l",
    "trojan://dGVzdC1zZXJ2ZXIuZXhhbXBsZS5jb20tNDQzLXRjcC1ub25l",
    "ss://YWVzLTI1Ni1nY206dGVzdC1wYXNzd29yZA@dGVzdC1zZXJ2ZXIuZXhhbXBsZS5jb20tODM4OC1vdXQtYm91bmQtdm1lc3M=",
]


class EnhancedVPNMerger:
    """
    Enhanced VPN Merger with all new features integrated.

    This class demonstrates how all the new enhancements work together
    to provide a comprehensive VPN configuration management solution.
    """

    def __init__(self):
        """Initialize the enhanced VPN merger system."""
        # Initialize core components
        self.merger = VPNSubscriptionMerger()
        self.source_manager = SourceManager()
        self.config_processor = ConfigurationProcessor()

        # Initialize enhanced components
        self.ml_predictor = None
        self.cache_warmer = None
        self.geo_optimizer = None
        self.discovery_system = None
        self.analytics_dashboard = None

        # Performance tracking
        self.performance_metrics = {
            "start_time": datetime.now(),
            "total_configs_processed": 0,
            "ml_predictions_made": 0,
            "cache_hits": 0,
            "geo_optimizations": 0,
            "sources_discovered": 0,
        }

        logger.info("Enhanced VPN Merger initialized")

    async def initialize_enhanced_features(self):
        """Initialize all enhanced features."""
        logger.info("Initializing enhanced features...")

        try:
            # 1. Initialize ML Quality Predictor
            logger.info("🔬 Initializing ML Quality Predictor...")
            self.ml_predictor = EnhancedConfigQualityPredictor(enable_online_learning=True)
            self.ml_predictor.add_drift_detection()

            # Train model if training data is available
            try:
                await train_production_model()
                logger.info("✅ ML model trained successfully")
            except Exception as e:
                logger.warning(f"⚠️ ML model training failed: {e}")

            # 2. Initialize Predictive Cache Warmer
            logger.info("💾 Initializing Predictive Cache Warmer...")
            self.cache_warmer = PredictiveCacheWarmer()
            await self.cache_warmer.initialize_redis(DEFAULT_REDIS_URL)
            await self.cache_warmer.optimize_cache()
            logger.info("✅ Cache warmer initialized successfully")

            # 3. Initialize Geographic Optimizer
            logger.info("🌍 Initializing Geographic Optimizer...")
            self.geo_optimizer = GeographicOptimizer()
            logger.info("✅ Geographic optimizer initialized successfully")

            # 4. Initialize Real-time Discovery
            logger.info("🔍 Initializing Real-time Discovery...")
            github_token = os.environ.get("GITHUB_TOKEN")
            telegram_api_id = os.environ.get("TELEGRAM_API_ID")
            telegram_api_hash = os.environ.get("TELEGRAM_API_HASH")

            self.discovery_system = RealTimeDiscovery(
                github_token=github_token,
                telegram_api_id=telegram_api_id,
                telegram_api_hash=telegram_api_hash,
            )
            logger.info("✅ Discovery system initialized successfully")

            # 5. Initialize Analytics Dashboard
            logger.info("📊 Initializing Analytics Dashboard...")
            self.analytics_dashboard = AnalyticsDashboard(port=DEFAULT_DASHBOARD_PORT)
            logger.info("✅ Analytics dashboard initialized successfully")

            logger.info("🎉 All enhanced features initialized successfully!")

        except Exception as e:
            logger.error(f"❌ Error initializing enhanced features: {e}")
            raise

    async def run_enhanced_merge(self, max_sources: int = DEFAULT_MAX_SOURCES) -> dict[str, Any]:
        """
        Run enhanced VPN configuration merge with all features.

        Args:
            max_sources: Maximum number of sources to process

        Returns:
            Dictionary with merge results and metrics
        """
        logger.info(f"🚀 Starting enhanced merge with max {max_sources} sources...")

        start_time = datetime.now()
        results = {
            "configs_processed": 0,
            "ml_predictions": 0,
            "cache_operations": 0,
            "geo_optimizations": 0,
            "sources_discovered": 0,
            "processing_time": 0.0,
            "quality_scores": [],
            "errors": [],
        }

        try:
            # 1. Discover new sources
            logger.info("🔍 Running source discovery...")
            await self.discovery_system._run_discovery_cycle()
            discovered_sources = self.discovery_system.get_discovered_sources(min_reliability=0.5)
            results["sources_discovered"] = len(discovered_sources)
            self.performance_metrics["sources_discovered"] += len(discovered_sources)

            # 2. Process configurations with ML quality prediction
            logger.info("🤖 Processing configurations with ML...")
            configs_to_process = SAMPLE_CONFIGS[:max_sources]

            for config in configs_to_process:
                try:
                    # ML quality prediction
                    quality_score = self.ml_predictor.predict_quality(config)
                    results["quality_scores"].append(quality_score)
                    results["ml_predictions"] += 1
                    self.performance_metrics["ml_predictions_made"] += 1

                    # Cache the configuration
                    cache_key = f"config_{hash(config)}"
                    await self.cache_warmer.set(cache_key, config, ttl=3600)
                    results["cache_operations"] += 1

                    # Geographic optimization (simulate user location)
                    user_location = GeoLocation(
                        country_code="US",
                        country_name="United States",
                        region="California",
                        city="San Francisco",
                        latitude=37.7749,
                        longitude=-122.4194,
                        timezone="America/Los_Angeles",
                        isp="Comcast",
                        asn="AS7922",
                    )

                    config_data = {
                        "id": cache_key,
                        "config": config,
                        "latitude": 40.7128,  # Simulated server location
                        "longitude": -74.0060,
                        "protocol": "vmess" if "vmess" in config else "unknown",
                    }

                    optimized_configs = self.geo_optimizer.optimize_by_location(
                        user_location, [config_data]
                    )

                    if optimized_configs:
                        results["geo_optimizations"] += 1
                        self.performance_metrics["geo_optimizations"] += 1

                    results["configs_processed"] += 1
                    self.performance_metrics["total_configs_processed"] += 1

                except Exception as e:
                    error_msg = f"Error processing config: {e}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            # 3. Update analytics dashboard
            logger.info("📊 Updating analytics dashboard...")
            await self._update_dashboard_metrics(results)

            # 4. Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            results["processing_time"] = processing_time

            logger.info(f"✅ Enhanced merge completed in {processing_time:.2f}s")
            logger.info(f"   - Configs processed: {results['configs_processed']}")
            logger.info(f"   - ML predictions: {results['ml_predictions']}")
            logger.info(f"   - Cache operations: {results['cache_operations']}")
            logger.info(f"   - Geo optimizations: {results['geo_optimizations']}")
            logger.info(f"   - Sources discovered: {results['sources_discovered']}")

            return results

        except Exception as e:
            error_msg = f"Error in enhanced merge: {e}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
            return results

    async def _update_dashboard_metrics(self, results: dict[str, Any]):
        """Update analytics dashboard with current metrics."""
        try:
            # Get cache statistics
            cache_stats = self.cache_warmer.get_cache_stats()

            # Calculate average quality score
            avg_quality = 0.0
            if results["quality_scores"]:
                avg_quality = sum(results["quality_scores"]) / len(results["quality_scores"])

            # Create dashboard metrics
            dashboard_metrics = DashboardMetrics(
                real_time_configs=results["configs_processed"],
                source_reliability=avg_quality,
                geographic_distribution={"US": 45, "EU": 38, "Asia": 42, "Other": 25},
                protocol_breakdown={
                    "VMess": 60,
                    "VLESS": 25,
                    "Trojan": 35,
                    "Shadowsocks": 20,
                    "Hysteria": 10,
                },
                performance_trends=[
                    {
                        "timestamp": datetime.now(),
                        "score": avg_quality,
                        "configs_processed": results["configs_processed"],
                    }
                ],
                cache_hit_rate=cache_stats.get("hit_rate", 0.0),
                error_rate=len(results["errors"]) / max(1, results["configs_processed"]),
                last_updated=datetime.now(),
            )

            await self.analytics_dashboard.updateRealTime(dashboard_metrics)

        except Exception as e:
            logger.error(f"Error updating dashboard metrics: {e}")

    async def run_continuous_monitoring(self, interval_minutes: int = DEFAULT_MONITORING_INTERVAL):
        """
        Run continuous monitoring with periodic enhanced merges.

        Args:
            interval_minutes: Interval between monitoring cycles
        """
        logger.info(f"🔄 Starting continuous monitoring (interval: {interval_minutes} minutes)")

        try:
            while True:
                # Run enhanced merge
                results = await self.run_enhanced_merge()

                # Log performance metrics
                logger.info("📈 Performance Summary:")
                logger.info(
                    f"   - Total configs processed: {self.performance_metrics['total_configs_processed']}"
                )
                logger.info(
                    f"   - ML predictions made: {self.performance_metrics['ml_predictions_made']}"
                )
                logger.info(f"   - Cache hits: {self.performance_metrics['cache_hits']}")
                logger.info(
                    f"   - Geo optimizations: {self.performance_metrics['geo_optimizations']}"
                )
                logger.info(
                    f"   - Sources discovered: {self.performance_metrics['sources_discovered']}"
                )

                # Wait for next cycle
                logger.info(f"⏰ Waiting {interval_minutes} minutes until next cycle...")
                await asyncio.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            logger.info("🛑 Continuous monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Error in continuous monitoring: {e}")

    async def start_analytics_dashboard(self):
        """Start the analytics dashboard server."""
        if self.analytics_dashboard:
            logger.info(f"🌐 Starting analytics dashboard on port {DEFAULT_DASHBOARD_PORT}")
            await self.analytics_dashboard.start_dashboard()

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get current performance metrics."""
        return self.performance_metrics.copy()

    async def cleanup(self):
        """Cleanup resources."""
        logger.info("🧹 Cleaning up resources...")

        try:
            if self.cache_warmer:
                await self.cache_warmer.close()

            if self.discovery_system:
                await self.discovery_system.close()

            if self.analytics_dashboard:
                await self.analytics_dashboard.stop_dashboard()

            logger.info("✅ Cleanup completed")

        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")


async def main():
    """Main function to run the enhanced integration demo."""
    logger.info("🚀 Starting Enhanced VPN Merger Integration Demo")

    # Create enhanced merger instance
    enhanced_merger = EnhancedVPNMerger()

    try:
        # Initialize enhanced features
        await enhanced_merger.initialize_enhanced_features()

        # Run a single enhanced merge
        logger.info("🔄 Running single enhanced merge...")
        results = await enhanced_merger.run_enhanced_merge(max_sources=10)

        # Print results
        print("\n" + "=" * 60)
        print("📊 ENHANCED MERGE RESULTS")
        print("=" * 60)
        print(f"Configs Processed: {results['configs_processed']}")
        print(f"ML Predictions: {results['ml_predictions']}")
        print(f"Cache Operations: {results['cache_operations']}")
        print(f"Geo Optimizations: {results['geo_optimizations']}")
        print(f"Sources Discovered: {results['sources_discovered']}")
        print(f"Processing Time: {results['processing_time']:.2f}s")

        if results["quality_scores"]:
            avg_quality = sum(results["quality_scores"]) / len(results["quality_scores"])
            print(f"Average Quality Score: {avg_quality:.3f}")

        if results["errors"]:
            print(f"Errors: {len(results['errors'])}")
            for error in results["errors"][:3]:  # Show first 3 errors
                print(f"  - {error}")

        print("=" * 60)

        # Show performance metrics
        performance = enhanced_merger.get_performance_metrics()
        print("\n📈 PERFORMANCE METRICS")
        print("-" * 40)
        for key, value in performance.items():
            if key != "start_time":
                print(f"{key.replace('_', ' ').title()}: {value}")

        # Ask user if they want to start continuous monitoring
        print("\n" + "=" * 60)
        print("🔄 CONTINUOUS MONITORING")
        print("=" * 60)
        print("The enhanced merger can run continuous monitoring with:")
        print("- Periodic source discovery")
        print("- Real-time ML quality prediction")
        print("- Intelligent caching")
        print("- Geographic optimization")
        print("- Live analytics dashboard")
        print("\nPress Ctrl+C to stop monitoring")
        print("=" * 60)

        # Start continuous monitoring
        await enhanced_merger.run_continuous_monitoring(interval_minutes=5)

    except KeyboardInterrupt:
        logger.info("🛑 Demo stopped by user")
    except Exception as e:
        logger.error(f"❌ Error in demo: {e}")
    finally:
        # Cleanup
        await enhanced_merger.cleanup()
        logger.info("👋 Demo completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)
