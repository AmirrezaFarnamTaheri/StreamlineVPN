#!/usr/bin/env python3
"""
Benchmark Runner
===============

Main benchmark runner that orchestrates all benchmark tests.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from .benchmark_tests import (
    CoreMergerBenchmark,
    SourceProcessingBenchmark,
    OutputGenerationBenchmark,
    MemoryUsageBenchmark,
    ConcurrentProcessingBenchmark,
    PerformanceOptimizationBenchmark,
    StressTestBenchmark
)
from .benchmark_utils import BenchmarkUtils

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Main benchmark runner that orchestrates all benchmark tests."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the benchmark runner.
        
        Args:
            config: Benchmark configuration
        """
        self.config = config or {}
        self.benchmark_results: List[Dict[str, Any]] = []
        
        # Benchmark configuration
        self.benchmark_config = self.config.get("benchmark", {
            "iterations": 5,
            "warmup_iterations": 2,
            "timeout_seconds": 300,
            "memory_threshold_mb": 1000,
            "cpu_threshold_percent": 80
        })
        
        # Initialize benchmark tests
        self.benchmark_tests = [
            CoreMergerBenchmark(self.config),
            SourceProcessingBenchmark(self.config),
            OutputGenerationBenchmark(self.config),
            MemoryUsageBenchmark(self.config),
            ConcurrentProcessingBenchmark(self.config),
            PerformanceOptimizationBenchmark(self.config),
            StressTestBenchmark(self.config)
        ]
        
        logger.info("Benchmark runner initialized")
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmark."""
        logger.info("Starting comprehensive performance benchmark...")
        
        benchmark_start = time.time()
        results = {
            "timestamp": datetime.now().isoformat(),
            "config": self.benchmark_config,
            "system_info": BenchmarkUtils.get_system_info(),
            "benchmarks": {}
        }
        
        try:
            # Run all benchmark tests
            for benchmark_test in self.benchmark_tests:
                test_name = benchmark_test.__class__.__name__.replace("Benchmark", "").lower()
                logger.info(f"Running {test_name} benchmark...")
                
                try:
                    test_results = await benchmark_test.run_benchmark()
                    results["benchmarks"][test_name] = test_results
                    logger.info(f"{test_name} benchmark completed")
                except Exception as e:
                    logger.error(f"{test_name} benchmark failed: {e}")
                    results["benchmarks"][test_name] = {"error": str(e)}
            
            # Calculate overall performance score
            results["overall_score"] = BenchmarkUtils.calculate_overall_score(results["benchmarks"])
            
            # Generate recommendations
            results["recommendations"] = BenchmarkUtils.generate_performance_recommendations(results)
            
            benchmark_duration = time.time() - benchmark_start
            results["total_duration"] = benchmark_duration
            
            logger.info(f"Comprehensive benchmark completed in {benchmark_duration:.2f} seconds")
            
            # Save results
            await BenchmarkUtils.save_benchmark_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            results["error"] = str(e)
            return results
    
    async def run_specific_benchmark(self, benchmark_name: str) -> Dict[str, Any]:
        """Run a specific benchmark test.
        
        Args:
            benchmark_name: Name of the benchmark to run
            
        Returns:
            Benchmark results
        """
        logger.info(f"Running specific benchmark: {benchmark_name}")
        
        # Find the benchmark test
        benchmark_test = None
        for test in self.benchmark_tests:
            test_name = test.__class__.__name__.replace("Benchmark", "").lower()
            if test_name == benchmark_name:
                benchmark_test = test
                break
        
        if not benchmark_test:
            raise ValueError(f"Unknown benchmark: {benchmark_name}")
        
        try:
            results = await benchmark_test.run_benchmark()
            logger.info(f"Specific benchmark {benchmark_name} completed")
            return results
        except Exception as e:
            logger.error(f"Specific benchmark {benchmark_name} failed: {e}")
            return {"error": str(e)}
    
    def get_available_benchmarks(self) -> List[str]:
        """Get list of available benchmark tests."""
        return [
            test.__class__.__name__.replace("Benchmark", "").lower()
            for test in self.benchmark_tests
        ]
    
    def get_benchmark_config(self) -> Dict[str, Any]:
        """Get current benchmark configuration."""
        return self.benchmark_config.copy()
    
    def update_benchmark_config(self, new_config: Dict[str, Any]) -> None:
        """Update benchmark configuration.
        
        Args:
            new_config: New configuration values
        """
        self.benchmark_config.update(new_config)
        
        # Update configuration for all benchmark tests
        for benchmark_test in self.benchmark_tests:
            benchmark_test.benchmark_config.update(new_config)
        
        logger.info("Benchmark configuration updated")
    
    async def run_quick_benchmark(self) -> Dict[str, Any]:
        """Run a quick benchmark with reduced iterations."""
        logger.info("Running quick benchmark...")
        
        # Save original config
        original_config = self.benchmark_config.copy()
        
        # Update config for quick benchmark
        quick_config = {
            "iterations": 2,
            "warmup_iterations": 1,
            "timeout_seconds": 60
        }
        
        self.update_benchmark_config(quick_config)
        
        try:
            # Run only core benchmarks
            core_benchmarks = [
                CoreMergerBenchmark(self.config),
                MemoryUsageBenchmark(self.config)
            ]
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "config": self.benchmark_config,
                "system_info": BenchmarkUtils.get_system_info(),
                "benchmarks": {},
                "type": "quick"
            }
            
            for benchmark_test in core_benchmarks:
                test_name = benchmark_test.__class__.__name__.replace("Benchmark", "").lower()
                logger.info(f"Running quick {test_name} benchmark...")
                
                try:
                    test_results = await benchmark_test.run_benchmark()
                    results["benchmarks"][test_name] = test_results
                except Exception as e:
                    logger.error(f"Quick {test_name} benchmark failed: {e}")
                    results["benchmarks"][test_name] = {"error": str(e)}
            
            # Calculate overall score
            results["overall_score"] = BenchmarkUtils.calculate_overall_score(results["benchmarks"])
            
            # Generate recommendations
            results["recommendations"] = BenchmarkUtils.generate_performance_recommendations(results)
            
            logger.info("Quick benchmark completed")
            return results
            
        finally:
            # Restore original config
            self.update_benchmark_config(original_config)
    
    async def run_continuous_benchmark(self, interval_minutes: int = 60) -> None:
        """Run continuous benchmarking at specified intervals.
        
        Args:
            interval_minutes: Interval between benchmark runs in minutes
        """
        logger.info(f"Starting continuous benchmarking with {interval_minutes} minute intervals")
        
        while True:
            try:
                logger.info("Starting scheduled benchmark run...")
                results = await self.run_comprehensive_benchmark()
                
                # Log results summary
                overall_score = results.get("overall_score", 0)
                logger.info(f"Scheduled benchmark completed - Overall Score: {overall_score:.2f}/100")
                
                # Check if performance has degraded
                if overall_score < 70:
                    logger.warning(f"Performance degradation detected - Score: {overall_score:.2f}")
                
                # Wait for next interval
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Continuous benchmark error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

