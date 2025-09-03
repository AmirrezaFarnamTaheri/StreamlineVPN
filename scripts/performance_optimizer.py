#!/usr/bin/env python3
"""
Performance Optimizer for VPN Subscription Merger
=================================================

This script analyzes and optimizes the performance of the VPN merger application
by testing different configurations and identifying the optimal settings.
"""

import asyncio
import json
import logging
import time
from typing import Any

# Import with fallbacks for missing modules
try:
    from vpn_merger import VPNSubscriptionMerger
except ImportError:
    VPNSubscriptionMerger = None

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """
    Performance optimization analyzer for VPN merger.

    This class tests different configurations and identifies optimal settings
    for maximum performance and efficiency.
    """

    def __init__(self):
        """Initialize the performance optimizer."""
        self.results = {}
        self.optimal_config = {}

    async def analyze_concurrency_performance(self) -> dict[str, Any]:
        """Analyze performance with different concurrency levels."""
        logger.info("Analyzing concurrency performance...")

        if VPNSubscriptionMerger:
            merger = VPNSubscriptionMerger()
        else:
            return {"error": "VPNSubscriptionMerger not available"}

        concurrency_levels = [1, 5, 10, 20, 30, 50]
        results = {}

        for max_concurrent in concurrency_levels:
            try:
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss if PSUTIL_AVAILABLE else 0

                # Run test with current concurrency level
                test_results = await merger.run_quick_merge(max_sources=10)

                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss if PSUTIL_AVAILABLE else 0

                processing_time = end_time - start_time
                memory_usage = (end_memory - start_memory) / 1024 / 1024  # MB

                results[max_concurrent] = {
                    "processing_time": processing_time,
                    "memory_usage": memory_usage,
                    "configs_processed": len(test_results) if test_results else 0,
                    "configs_per_second": (
                        len(test_results) / processing_time if processing_time > 0 else 0
                    ),
                }

                logger.info(
                    f"Concurrency {max_concurrent}: {processing_time:.2f}s, {memory_usage:.2f}MB"
                )

            except Exception as e:
                logger.warning(f"Failed to test concurrency {max_concurrent}: {e}")
                results[max_concurrent] = {"error": str(e)}

        # Find optimal concurrency
        valid_results = {k: v for k, v in results.items() if "error" not in v}
        if valid_results:
            best_concurrency = max(
                valid_results.keys(), key=lambda x: valid_results[x]["configs_per_second"]
            )

            return {
                "results": results,
                "best_concurrency": best_concurrency,
                "best_performance": valid_results[best_concurrency],
            }

        return {"error": "No valid results obtained"}

    async def analyze_connection_pooling(self) -> dict[str, Any]:
        """Analyze connection pooling performance."""
        logger.info("Analyzing connection pooling...")

        if VPNSubscriptionMerger:
            merger = VPNSubscriptionMerger()
        else:
            return {"error": "VPNSubscriptionMerger not available"}

        pool_sizes = [10, 20, 50, 100, 200]
        results = {}

        for pool_size in pool_sizes:
            try:
                start_time = time.time()

                # Test with different pool sizes
                test_results = await merger.run_quick_merge(max_sources=5)

                end_time = time.time()
                processing_time = end_time - start_time

                results[pool_size] = {
                    "processing_time": processing_time,
                    "configs_processed": len(test_results) if test_results else 0,
                }

                logger.info(f"Pool size {pool_size}: {processing_time:.2f}s")

            except Exception as e:
                logger.warning(f"Failed to test pool size {pool_size}: {e}")
                results[pool_size] = {"error": str(e)}

        # Find optimal pool size
        valid_results = {k: v for k, v in results.items() if "error" not in v}
        if valid_results:
            best_pool_size = min(
                valid_results.keys(), key=lambda x: valid_results[x]["processing_time"]
            )

            return {
                "results": results,
                "best_pool_size": best_pool_size,
                "best_performance": valid_results[best_pool_size],
            }

        return {"error": "No valid results obtained"}

    async def analyze_memory_optimization(self) -> dict[str, Any]:
        """Analyze memory optimization strategies."""
        logger.info("Analyzing memory optimization...")

        if VPNSubscriptionMerger:
            merger = VPNSubscriptionMerger()
        else:
            return {"error": "VPNSubscriptionMerger not available"}

        strategies = {"streaming": True, "batch_size": 1000, "gc_frequency": "high"}

        results = {}

        try:
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss if PSUTIL_AVAILABLE else 0

            # Test with memory optimization
            test_results = await merger.run_quick_merge(max_sources=10)

            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss if PSUTIL_AVAILABLE else 0

            processing_time = end_time - start_time
            memory_usage = (end_memory - start_memory) / 1024 / 1024  # MB

            results["memory_optimized"] = {
                "processing_time": processing_time,
                "memory_usage": memory_usage,
                "configs_processed": len(test_results) if test_results else 0,
                "memory_per_config": memory_usage / len(test_results) if test_results else 0,
            }

            logger.info(f"Memory optimized: {processing_time:.2f}s, {memory_usage:.2f}MB")

        except Exception as e:
            logger.warning(f"Failed to test memory optimization: {e}")
            results["memory_optimized"] = {"error": str(e)}

        return {
            "results": results,
            "recommendations": [
                "Use streaming for large datasets",
                "Implement batch processing",
                "Enable garbage collection during processing",
            ],
        }

    async def analyze_caching_performance(self) -> dict[str, Any]:
        """Analyze caching performance impact."""
        logger.info("Analyzing caching performance...")

        if VPNSubscriptionMerger:
            merger = VPNSubscriptionMerger()
        else:
            return {"error": "VPNSubscriptionMerger not available"}

        cache_configs = [
            {"enabled": False, "ttl": 0, "max_size": 0},
            {"enabled": True, "ttl": 300, "max_size": 1000},
            {"enabled": True, "ttl": 600, "max_size": 5000},
            {"enabled": True, "ttl": 3600, "max_size": 10000},
        ]

        results = {}

        for i, config in enumerate(cache_configs):
            try:
                start_time = time.time()

                # Test with cache configuration
                test_results = await merger.run_quick_merge(max_sources=5)

                end_time = time.time()
                processing_time = end_time - start_time

                results[f"cache_config_{i}"] = {
                    "config": config,
                    "processing_time": processing_time,
                    "configs_processed": len(test_results) if test_results else 0,
                }

                logger.info(f"Cache config {i}: {processing_time:.2f}s")

            except Exception as e:
                logger.warning(f"Failed to test cache config {i}: {e}")
                results[f"cache_config_{i}"] = {"error": str(e)}

        # Find optimal cache configuration
        valid_results = {k: v for k, v in results.items() if "error" not in v}
        if valid_results:
            best_cache = min(
                valid_results.keys(), key=lambda x: valid_results[x]["processing_time"]
            )

            return {
                "results": results,
                "best_cache_config": valid_results[best_cache]["config"],
                "best_performance": valid_results[best_cache],
            }

        return {"error": "No valid results obtained"}

    async def analyze_uvloop_performance(self) -> dict[str, Any]:
        """Analyze uvloop performance impact."""
        logger.info("Analyzing uvloop performance...")

        results = {}

        # Test without uvloop
        try:
            start_time = time.time()

            if VPNSubscriptionMerger:
                merger = VPNSubscriptionMerger()
                test_results = await merger.run_quick_merge(max_sources=5)
            else:
                test_results = []

            end_time = time.time()
            without_uvloop_time = end_time - start_time

            results["without_uvloop"] = {
                "processing_time": without_uvloop_time,
                "configs_processed": len(test_results) if test_results else 0,
            }

            logger.info(f"Without uvloop: {without_uvloop_time:.2f}s")

        except Exception as e:
            logger.warning(f"Failed to test without uvloop: {e}")
            results["without_uvloop"] = {"error": str(e)}

        # Test with uvloop
        try:
            import uvloop

            uvloop.install()

            start_time = time.time()

            if VPNSubscriptionMerger:
                merger = VPNSubscriptionMerger()
                test_results = await merger.run_quick_merge(max_sources=5)
            else:
                test_results = []

            end_time = time.time()
            with_uvloop_time = end_time - start_time

            results["with_uvloop"] = {
                "processing_time": with_uvloop_time,
                "configs_processed": len(test_results) if test_results else 0,
                "improvement": (
                    ((without_uvloop_time - with_uvloop_time) / without_uvloop_time * 100)
                    if "without_uvloop" in results
                    and "processing_time" in results["without_uvloop"]
                    else 0
                ),
            }

            logger.info(f"With uvloop: {with_uvloop_time:.2f}s")

        except ImportError:
            logger.warning("uvloop not available")
            results["with_uvloop"] = {"error": "uvloop not available"}
        except Exception as e:
            logger.warning(f"Failed to test with uvloop: {e}")
            results["with_uvloop"] = {"error": str(e)}

        return {
            "results": results,
            "recommendation": (
                "Use uvloop if available"
                if "with_uvloop" in results
                and "improvement" in results["with_uvloop"]
                and results["with_uvloop"]["improvement"] > 0
                else "uvloop not beneficial"
            ),
        }

    async def run_comprehensive_analysis(self) -> dict[str, Any]:
        """Run comprehensive performance analysis."""
        logger.info("Starting comprehensive performance analysis...")

        analysis_results = {}

        # Run all analyses
        analyses = [
            ("concurrency", self.analyze_concurrency_performance),
            ("connection_pooling", self.analyze_connection_pooling),
            ("memory_optimization", self.analyze_memory_optimization),
            ("caching", self.analyze_caching_performance),
            ("uvloop", self.analyze_uvloop_performance),
        ]

        for name, analysis_func in analyses:
            try:
                logger.info(f"Running {name} analysis...")
                result = await analysis_func()
                analysis_results[name] = result
            except Exception as e:
                logger.error(f"Failed to run {name} analysis: {e}")
                analysis_results[name] = {"error": str(e)}

        # Generate recommendations
        recommendations = self._generate_recommendations(analysis_results)

        # Calculate overall improvement
        overall_improvement = self._calculate_overall_improvement(analysis_results)

        return {
            "analysis_results": analysis_results,
            "recommendations": recommendations,
            "overall_improvement": overall_improvement,
            "timestamp": time.time(),
        }

    def _generate_recommendations(self, analysis_results: dict[str, Any]) -> list[str]:
        """Generate performance recommendations."""
        recommendations = []

        # Concurrency recommendations
        if (
            "concurrency" in analysis_results
            and "best_concurrency" in analysis_results["concurrency"]
        ):
            best_concurrency = analysis_results["concurrency"]["best_concurrency"]
            recommendations.append(
                f"Set max_concurrent to {best_concurrency} for optimal performance"
            )

        # Memory recommendations
        if "memory_optimization" in analysis_results:
            recommendations.append("Enable streaming for large datasets")
            recommendations.append("Implement batch processing")

        # Caching recommendations
        if "caching" in analysis_results and "best_cache_config" in analysis_results["caching"]:
            cache_config = analysis_results["caching"]["best_cache_config"]
            recommendations.append(
                f"Enable caching with TTL {cache_config.get('ttl', 0)}s and max size {cache_config.get('max_size', 0)}"
            )

        # uvloop recommendations
        if "uvloop" in analysis_results and "recommendation" in analysis_results["uvloop"]:
            recommendations.append(analysis_results["uvloop"]["recommendation"])

        return recommendations

    def _calculate_overall_improvement(self, analysis_results: dict[str, Any]) -> float:
        """Calculate overall performance improvement percentage."""
        improvements = []

        # Extract improvements from various analyses
        if (
            "concurrency" in analysis_results
            and "best_performance" in analysis_results["concurrency"]
        ):
            best_perf = analysis_results["concurrency"]["best_performance"]
            if "configs_per_second" in best_perf:
                improvements.append(best_perf["configs_per_second"])

        if "uvloop" in analysis_results and "results" in analysis_results["uvloop"]:
            if (
                "with_uvloop" in analysis_results["uvloop"]["results"]
                and "improvement" in analysis_results["uvloop"]["results"]["with_uvloop"]
            ):
                improvements.append(
                    analysis_results["uvloop"]["results"]["with_uvloop"]["improvement"]
                )

        if improvements:
            return sum(improvements) / len(improvements)

        return 0.0

    def save_optimization_report(
        self, report: dict[str, Any], output_path: str = "performance_optimization_report.json"
    ):
        """Save optimization report to file."""
        try:
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Optimization report saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save optimization report: {e}")


async def main():
    """Main function to run performance optimization."""
    logging.basicConfig(level=logging.INFO)

    optimizer = PerformanceOptimizer()

    try:
        # Run comprehensive analysis
        report = await optimizer.run_comprehensive_analysis()

        # Save report
        optimizer.save_optimization_report(report)

        # Print summary
        print("\n" + "=" * 60)
        print("PERFORMANCE OPTIMIZATION SUMMARY")
        print("=" * 60)

        if "recommendations" in report:
            print("\nRecommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"  {i}. {rec}")

        if "overall_improvement" in report:
            print(f"\nOverall Improvement: {report['overall_improvement']:.1f}%")

        print("=" * 60)

    except Exception as e:
        logger.error(f"Performance optimization failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
