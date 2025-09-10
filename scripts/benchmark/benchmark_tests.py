#!/usr/bin/env python3
"""
Benchmark Test Classes
=====================

Individual benchmark test implementations.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.core.source_manager import SourceManager
from streamline_vpn.core.output_manager import OutputManager

logger = logging.getLogger(__name__)


class BaseBenchmark:
    """Base class for benchmark tests."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize benchmark test.
        
        Args:
            config: Benchmark configuration
        """
        self.config = config or {}
        self.benchmark_config = self.config.get("benchmark", {
            "iterations": 5,
            "warmup_iterations": 2,
            "timeout_seconds": 300
        })
    
    async def run_benchmark(self) -> Dict[str, Any]:
        """Run the benchmark test."""
        raise NotImplementedError("Subclasses must implement run_benchmark")


class CoreMergerBenchmark(BaseBenchmark):
    """Benchmark core merger functionality."""
    
    async def run_benchmark(self) -> Dict[str, Any]:
        """Run core merger benchmark."""
        logger.info("Benchmarking core merger functionality...")
        
        results = {
            "test_name": "core_merger",
            "iterations": self.benchmark_config["iterations"],
            "warmup_iterations": self.benchmark_config["warmup_iterations"],
            "metrics": {}
        }
        
        try:
            # Warmup iterations
            for i in range(self.benchmark_config["warmup_iterations"]):
                merger = StreamlineVPNMerger()
                await merger.merge_subscriptions()
                logger.debug(f"Warmup iteration {i+1} completed")
            
            # Benchmark iterations
            durations = []
            memory_usage = []
            cpu_usage = []
            
            for i in range(self.benchmark_config["iterations"]):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
                start_cpu = psutil.cpu_percent()
                
                # Run the benchmark
                merger = StreamlineVPNMerger()
                configs = await merger.merge_subscriptions()
                
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
                end_cpu = psutil.cpu_percent()
                
                duration = end_time - start_time
                memory_delta = end_memory - start_memory
                cpu_delta = end_cpu - start_cpu
                
                durations.append(duration)
                memory_usage.append(memory_delta)
                cpu_usage.append(cpu_delta)
                
                logger.debug(f"Benchmark iteration {i+1}: {duration:.2f}s, {memory_delta:.1f}MB, {cpu_delta:.1f}%")
            
            # Calculate statistics
            from .benchmark_utils import BenchmarkUtils
            results["metrics"] = {
                "duration": BenchmarkUtils.calculate_statistics(durations),
                "memory_usage": BenchmarkUtils.calculate_statistics(memory_usage),
                "cpu_usage": BenchmarkUtils.calculate_statistics(cpu_usage),
                "configs_generated": len(configs) if configs else 0
            }
            
            logger.info("Core merger benchmark completed")
            
        except Exception as e:
            logger.error(f"Core merger benchmark failed: {e}")
            results["error"] = str(e)
        
        return results


class SourceProcessingBenchmark(BaseBenchmark):
    """Benchmark source processing functionality."""
    
    async def run_benchmark(self) -> Dict[str, Any]:
        """Run source processing benchmark."""
        logger.info("Benchmarking source processing...")
        
        results = {
            "test_name": "source_processing",
            "iterations": self.benchmark_config["iterations"],
            "metrics": {}
        }
        
        try:
            source_manager = SourceManager()
            
            # Get sources
            sources = source_manager.get_prioritized_sources()
            
            durations = []
            processed_count = []
            
            for i in range(self.benchmark_config["iterations"]):
                start_time = time.time()
                
                # Process sources using merger
                merger = StreamlineVPNMerger()
                processed_sources = await merger.merge_subscriptions()
                
                end_time = time.time()
                duration = end_time - start_time
                
                durations.append(duration)
                processed_count.append(len(processed_sources) if processed_sources else 0)
                
                logger.debug(f"Source processing iteration {i+1}: {duration:.2f}s, {len(processed_sources) if processed_sources else 0} sources")
            
            from .benchmark_utils import BenchmarkUtils
            results["metrics"] = {
                "duration": BenchmarkUtils.calculate_statistics(durations),
                "sources_processed": BenchmarkUtils.calculate_statistics(processed_count)
            }
            
            logger.info("Source processing benchmark completed")
            
        except Exception as e:
            logger.error(f"Source processing benchmark failed: {e}")
            results["error"] = str(e)
        
        return results


class OutputGenerationBenchmark(BaseBenchmark):
    """Benchmark output generation functionality."""
    
    async def run_benchmark(self) -> Dict[str, Any]:
        """Run output generation benchmark."""
        logger.info("Benchmarking output generation...")
        
        results = {
            "test_name": "output_generation",
            "iterations": self.benchmark_config["iterations"],
            "metrics": {}
        }
        
        try:
            output_manager = OutputManager()
            
            # Generate test configurations
            merger = StreamlineVPNMerger()
            configs = await merger.merge_subscriptions()
            
            durations = []
            file_sizes = []
            
            for i in range(self.benchmark_config["iterations"]):
                start_time = time.time()
                
                # Generate outputs
                output_files = await output_manager.generate_outputs(configs)
                
                end_time = time.time()
                duration = end_time - start_time
                
                durations.append(duration)
                
                # Calculate total file size
                total_size = 0
                for output_file in output_files:
                    if Path(output_file).exists():
                        total_size += Path(output_file).stat().st_size
                file_sizes.append(total_size)
                
                logger.debug(f"Output generation iteration {i+1}: {duration:.2f}s, {total_size} bytes")
            
            from .benchmark_utils import BenchmarkUtils
            results["metrics"] = {
                "duration": BenchmarkUtils.calculate_statistics(durations),
                "file_size": BenchmarkUtils.calculate_statistics(file_sizes)
            }
            
            logger.info("Output generation benchmark completed")
            
        except Exception as e:
            logger.error(f"Output generation benchmark failed: {e}")
            results["error"] = str(e)
        
        return results


class MemoryUsageBenchmark(BaseBenchmark):
    """Benchmark memory usage patterns."""
    
    async def run_benchmark(self) -> Dict[str, Any]:
        """Run memory usage benchmark."""
        logger.info("Benchmarking memory usage...")
        
        results = {
            "test_name": "memory_usage",
            "iterations": self.benchmark_config["iterations"],
            "metrics": {}
        }
        
        try:
            memory_samples = []
            
            for i in range(self.benchmark_config["iterations"]):
                # Force garbage collection
                import gc
                gc.collect()
                
                # Measure memory before
                memory_before = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
                
                # Run memory-intensive operation
                merger = StreamlineVPNMerger()
                configs = await merger.merge_subscriptions()
                
                # Measure memory after
                memory_after = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
                
                memory_delta = memory_after - memory_before
                memory_samples.append({
                    "before": memory_before,
                    "after": memory_after,
                    "delta": memory_delta
                })
                
                logger.debug(f"Memory usage iteration {i+1}: {memory_before:.1f}MB -> {memory_after:.1f}MB (Δ{memory_delta:.1f}MB)")
            
            # Calculate statistics
            deltas = [sample["delta"] for sample in memory_samples]
            before_values = [sample["before"] for sample in memory_samples]
            after_values = [sample["after"] for sample in memory_samples]
            
            from .benchmark_utils import BenchmarkUtils
            results["metrics"] = {
                "memory_delta": BenchmarkUtils.calculate_statistics(deltas),
                "memory_before": BenchmarkUtils.calculate_statistics(before_values),
                "memory_after": BenchmarkUtils.calculate_statistics(after_values)
            }
            
            logger.info("Memory usage benchmark completed")
            
        except Exception as e:
            logger.error(f"Memory usage benchmark failed: {e}")
            results["error"] = str(e)
        
        return results


class ConcurrentProcessingBenchmark(BaseBenchmark):
    """Benchmark concurrent processing capabilities."""
    
    async def run_benchmark(self) -> Dict[str, Any]:
        """Run concurrent processing benchmark."""
        logger.info("Benchmarking concurrent processing...")
        
        results = {
            "test_name": "concurrent_processing",
            "iterations": self.benchmark_config["iterations"],
            "metrics": {}
        }
        
        try:
            concurrent_levels = [1, 2, 4, 8]
            concurrent_results = {}
            
            for concurrency in concurrent_levels:
                durations = []
                
                for i in range(self.benchmark_config["iterations"]):
                    start_time = time.time()
                    
                    # Run concurrent operations
                    tasks = []
                    for j in range(concurrency):
                        merger = StreamlineVPNMerger()
                        task = asyncio.create_task(merger.merge_subscriptions())
                        tasks.append(task)
                    
                    # Wait for all tasks to complete
                    await asyncio.gather(*tasks)
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    durations.append(duration)
                    
                    logger.debug(f"Concurrent processing (level {concurrency}) iteration {i+1}: {duration:.2f}s")
                
                from .benchmark_utils import BenchmarkUtils
                concurrent_results[concurrency] = BenchmarkUtils.calculate_statistics(durations)
            
            results["metrics"] = concurrent_results
            
            logger.info("Concurrent processing benchmark completed")
            
        except Exception as e:
            logger.error(f"Concurrent processing benchmark failed: {e}")
            results["error"] = str(e)
        
        return results


class PerformanceOptimizationBenchmark(BaseBenchmark):
    """Benchmark performance optimization features."""
    
    async def run_benchmark(self) -> Dict[str, Any]:
        """Run performance optimization benchmark."""
        logger.info("Benchmarking performance optimization...")
        
        results = {
            "test_name": "performance_optimization",
            "iterations": self.benchmark_config["iterations"],
            "metrics": {}
        }
        
        try:
            # Test with and without optimization
            optimization_results = {}
            
            for optimized in [False, True]:
                durations = []
                
                for i in range(self.benchmark_config["iterations"]):
                    start_time = time.time()
                    
                    if optimized:
                        # Use performance optimization (example)
                        # PerformanceOptimizer would be implemented here
                        pass
                    
                    # Run benchmark
                    merger = StreamlineVPNMerger()
                    configs = await merger.merge_subscriptions()
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    durations.append(duration)
                    
                    logger.debug(f"Performance optimization ({'enabled' if optimized else 'disabled'}) iteration {i+1}: {duration:.2f}s")
                
                from .benchmark_utils import BenchmarkUtils
                optimization_results[f"optimized_{optimized}"] = BenchmarkUtils.calculate_statistics(durations)
            
            results["metrics"] = optimization_results
            
            # Calculate improvement
            if "optimized_True" in optimization_results and "optimized_False" in optimization_results:
                avg_without = optimization_results["optimized_False"]["avg"]
                avg_with = optimization_results["optimized_True"]["avg"]
                improvement = ((avg_without - avg_with) / avg_without) * 100
                results["metrics"]["improvement_percent"] = improvement
            
            logger.info("Performance optimization benchmark completed")
            
        except Exception as e:
            logger.error(f"Performance optimization benchmark failed: {e}")
            results["error"] = str(e)
        
        return results


class StressTestBenchmark(BaseBenchmark):
    """Benchmark stress testing capabilities."""
    
    async def run_benchmark(self) -> Dict[str, Any]:
        """Run stress test benchmark."""
        logger.info("Benchmarking stress test...")
        
        results = {
            "test_name": "stress_test",
            "iterations": 10,  # More iterations for stress test
            "metrics": {}
        }
        
        try:
            durations = []
            memory_usage = []
            cpu_usage = []
            success_count = 0
            
            for i in range(results["iterations"]):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
                start_cpu = psutil.cpu_percent()
                
                try:
                    # Run stress test
                    merger = StreamlineVPNMerger()
                    configs = await merger.merge_subscriptions()
                    
                    if configs:
                        success_count += 1
                    
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
                    end_cpu = psutil.cpu_percent()
                    
                    duration = end_time - start_time
                    memory_delta = end_memory - start_memory
                    cpu_delta = end_cpu - start_cpu
                    
                    durations.append(duration)
                    memory_usage.append(memory_delta)
                    cpu_usage.append(cpu_delta)
                    
                    logger.debug(f"Stress test iteration {i+1}: {duration:.2f}s, {memory_delta:.1f}MB, {cpu_delta:.1f}%")
                    
                except Exception as e:
                    logger.warning(f"Stress test iteration {i+1} failed: {e}")
                    durations.append(float('inf'))
                    memory_usage.append(0)
                    cpu_usage.append(0)
            
            # Calculate statistics (excluding failed iterations)
            valid_durations = [d for d in durations if d != float('inf')]
            valid_memory = [m for m in memory_usage if m != 0]
            valid_cpu = [c for c in cpu_usage if c != 0]
            
            from .benchmark_utils import BenchmarkUtils
            results["metrics"] = {
                "success_rate": (success_count / results["iterations"]) * 100,
                "duration": BenchmarkUtils.calculate_statistics(valid_durations),
                "memory_usage": BenchmarkUtils.calculate_statistics(valid_memory),
                "cpu_usage": BenchmarkUtils.calculate_statistics(valid_cpu)
            }
            
            logger.info("Stress test benchmark completed")
            
        except Exception as e:
            logger.error(f"Stress test benchmark failed: {e}")
            results["error"] = str(e)
        
        return results
