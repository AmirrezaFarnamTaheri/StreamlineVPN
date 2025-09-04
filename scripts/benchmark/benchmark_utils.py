#!/usr/bin/env python3
"""
Benchmark Utilities
==================

Utility functions for performance benchmarking.
"""

import json
import logging
import psutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BenchmarkUtils:
    """Utility functions for performance benchmarking."""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get system information for benchmark context."""
        try:
            return {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                "disk_total_gb": psutil.disk_usage('/').total / (1024**3),
                "disk_free_gb": psutil.disk_usage('/').free / (1024**3),
                "python_version": sys.version,
                "platform": sys.platform
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def calculate_statistics(values: List[float]) -> Dict[str, float]:
        """Calculate statistics for a list of values."""
        if not values:
            return {"min": 0, "max": 0, "avg": 0, "median": 0}
        
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "median": sorted(values)[len(values) // 2]
        }
    
    @staticmethod
    def calculate_overall_score(benchmarks: Dict[str, Any]) -> float:
        """Calculate overall performance score."""
        try:
            scores = []
            
            # Core merger score (based on duration)
            if "core_merger" in benchmarks and "metrics" in benchmarks["core_merger"]:
                core_duration = benchmarks["core_merger"]["metrics"]["duration"]["avg"]
                core_score = max(0, 100 - (core_duration * 10))  # Lower duration = higher score
                scores.append(core_score)
            
            # Memory usage score
            if "memory_usage" in benchmarks and "metrics" in benchmarks["memory_usage"]:
                memory_delta = benchmarks["memory_usage"]["metrics"]["memory_delta"]["avg"]
                memory_score = max(0, 100 - (memory_delta / 10))  # Lower memory usage = higher score
                scores.append(memory_score)
            
            # Stress test score (based on success rate)
            if "stress_test" in benchmarks and "metrics" in benchmarks["stress_test"]:
                success_rate = benchmarks["stress_test"]["metrics"]["success_rate"]
                stress_score = success_rate  # Success rate directly as score
                scores.append(stress_score)
            
            # Calculate overall score
            if scores:
                overall_score = sum(scores) / len(scores)
                return round(overall_score, 2)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Failed to calculate overall score: {e}")
            return 0.0
    
    @staticmethod
    def generate_performance_recommendations(results: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on benchmark results."""
        recommendations = []
        
        try:
            benchmarks = results.get("benchmarks", {})
            
            # Core merger recommendations
            if "core_merger" in benchmarks:
                core_metrics = benchmarks["core_merger"].get("metrics", {})
                duration = core_metrics.get("duration", {}).get("avg", 0)
                
                if duration > 30:
                    recommendations.append("Consider optimizing core merger performance - average duration is high")
                elif duration > 60:
                    recommendations.append("Critical: Core merger performance needs immediate attention")
            
            # Memory usage recommendations
            if "memory_usage" in benchmarks:
                memory_metrics = benchmarks["memory_usage"].get("metrics", {})
                memory_delta = memory_metrics.get("memory_delta", {}).get("avg", 0)
                
                if memory_delta > 500:  # 500MB
                    recommendations.append("High memory usage detected - consider implementing memory cleanup")
                elif memory_delta > 1000:  # 1GB
                    recommendations.append("Critical: Memory usage is excessive - implement memory optimization")
            
            # Stress test recommendations
            if "stress_test" in benchmarks:
                stress_metrics = benchmarks["stress_test"].get("metrics", {})
                success_rate = stress_metrics.get("success_rate", 100)
                
                if success_rate < 90:
                    recommendations.append("Stress test shows reliability issues - investigate error handling")
                elif success_rate < 95:
                    recommendations.append("Stress test indicates potential stability concerns")
            
            # Overall score recommendations
            overall_score = results.get("overall_score", 100)
            if overall_score < 70:
                recommendations.append("Overall performance score is low - comprehensive optimization needed")
            elif overall_score < 85:
                recommendations.append("Performance could be improved - consider targeted optimizations")
            
            if not recommendations:
                recommendations.append("Performance is excellent - continue monitoring for any changes")
                
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            recommendations.append("Error generating recommendations")
        
        return recommendations
    
    @staticmethod
    async def save_benchmark_results(results: Dict[str, Any]) -> None:
        """Save benchmark results to file."""
        try:
            # Create results directory
            results_dir = Path("benchmark_results")
            results_dir.mkdir(exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = results_dir / f"performance_benchmark_{timestamp}.json"
            
            # Save results
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Benchmark results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save benchmark results: {e}")
    
    @staticmethod
    def print_benchmark_summary(results: Dict[str, Any]) -> None:
        """Print benchmark summary to console."""
        print("\n" + "="*60)
        print("PERFORMANCE BENCHMARK RESULTS")
        print("="*60)
        
        print(f"Overall Score: {results.get('overall_score', 0):.2f}/100")
        print(f"Total Duration: {results.get('total_duration', 0):.2f} seconds")
        
        print("\nBenchmark Summary:")
        for test_name, test_results in results.get("benchmarks", {}).items():
            if "error" not in test_results:
                print(f"  {test_name}: ✅ Completed")
            else:
                print(f"  {test_name}: ❌ Failed - {test_results['error']}")
        
        print("\nRecommendations:")
        for i, recommendation in enumerate(results.get("recommendations", []), 1):
            print(f"  {i}. {recommendation}")
        
        print("\n" + "="*60)

