#!/usr/bin/env python3
"""
test_runner.py
==============

Comprehensive test runner for StreamlineVPN with all test types.
"""

import os
import sys
import subprocess
import time
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.utils.logging import get_logger

logger = get_logger(__name__)


class StreamlineVPNTestRunner:
    """Comprehensive test runner for StreamlineVPN."""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.coverage_data = {}
        
        # Test categories
        self.test_categories = {
            'unit': {
                'pattern': 'tests/unit/test_*.py',
                'description': 'Unit Tests',
                'timeout': 300
            },
            'integration': {
                'pattern': 'tests/test_*.py',
                'description': 'Integration Tests', 
                'timeout': 600
            },
            'api': {
                'pattern': 'tests/test_api.py',
                'description': 'API Tests',
                'timeout': 300
            },
            'e2e': {
                'pattern': 'tests/test_e2e.py',
                'description': 'End-to-End Tests',
                'timeout': 900
            },
            'performance': {
                'pattern': 'scripts/benchmark/benchmark_tests.py',
                'description': 'Performance Tests',
                'timeout': 1800
            }
        }
    
    def run_all_tests(self, categories: List[str] = None, coverage: bool = True, 
                     parallel: bool = False, verbose: bool = False) -> Dict[str, Any]:
        """Run all tests with optional coverage."""
        if categories is None:
            categories = list(self.test_categories.keys())
        
        self.start_time = time.time()
        logger.info(f"Starting test run for categories: {categories}")
        
        results = {}
        
        for category in categories:
            if category not in self.test_categories:
                logger.warning(f"Unknown test category: {category}")
                continue
            
            logger.info(f"Running {self.test_categories[category]['description']}...")
            
            try:
                result = self.run_test_category(
                    category, 
                    coverage=coverage,
                    parallel=parallel,
                    verbose=verbose
                )
                results[category] = result
                
            except Exception as e:
                logger.error(f"Failed to run {category} tests: {e}")
                results[category] = {
                    'success': False,
                    'error': str(e),
                    'tests_run': 0,
                    'tests_passed': 0,
                    'tests_failed': 0,
                    'duration': 0
                }
        
        # Generate summary
        summary = self.generate_summary(results)
        
        # Save results
        self.save_test_results(results, summary)
        
        return {
            'results': results,
            'summary': summary,
            'duration': time.time() - self.start_time
        }
    
    def run_test_category(self, category: str, coverage: bool = True, 
                         parallel: bool = False, verbose: bool = False) -> Dict[str, Any]:
        """Run tests for a specific category."""
        config = self.test_categories[category]
        pattern = config['pattern']
        timeout = config['timeout']
        
        # Find test files
        test_files = list(Path('.').glob(pattern))
        
        if not test_files:
            logger.warning(f"No test files found for pattern: {pattern}")
            return {
                'success': True,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0,
                'duration': 0,
                'message': 'No tests found'
            }
        
        # Build pytest command
        cmd = ['python', '-m', 'pytest']
        
        if verbose:
            cmd.append('-v')
        
        if parallel:
            cmd.extend(['-n', 'auto'])
        
        if coverage:
            cmd.extend([
                '--cov=src/streamline_vpn',
                '--cov-report=html:htmlcov',
                '--cov-report=json:coverage.json',
                '--cov-report=term-missing'
            ])
        
        # Add test files
        cmd.extend([str(f) for f in test_files])
        
        # Add timeout
        cmd.extend(['--timeout', str(timeout)])
        
        # Add other useful options
        cmd.extend([
            '--tb=short',
            '--strict-markers',
            '--disable-warnings'
        ])
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        start_time = time.time()
        
        try:
            # Run tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 60  # Add buffer
            )
            
            duration = time.time() - start_time
            
            # Parse results
            success = result.returncode == 0
            
            # Try to parse pytest output for detailed results
            tests_run, tests_passed, tests_failed = self.parse_pytest_output(result.stdout)
            
            return {
                'success': success,
                'tests_run': tests_run,
                'tests_passed': tests_passed,
                'tests_failed': tests_failed,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Tests timed out after {timeout} seconds")
            return {
                'success': False,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0,
                'duration': timeout,
                'error': 'Timeout',
                'stdout': '',
                'stderr': 'Test execution timed out'
            }
        
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return {
                'success': False,
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 0,
                'duration': time.time() - start_time,
                'error': str(e),
                'stdout': '',
                'stderr': str(e)
            }
    
    def parse_pytest_output(self, output: str) -> tuple:
        """Parse pytest output to extract test counts."""
        lines = output.split('\n')
        
        tests_run = 0
        tests_passed = 0
        tests_failed = 0
        
        for line in lines:
            if 'failed' in line and 'passed' in line:
                # Parse line like "5 failed, 10 passed in 2.34s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'failed':
                        try:
                            tests_failed = int(parts[i-1])
                        except:
                            pass
                    elif part == 'passed':
                        try:
                            tests_passed = int(parts[i-1])
                        except:
                            pass
                
                tests_run = tests_passed + tests_failed
                break
        
        return tests_run, tests_passed, tests_failed
    
    def run_smoke_tests(self) -> Dict[str, Any]:
        """Run quick smoke tests to verify basic functionality."""
        logger.info("Running smoke tests...")
        
        smoke_tests = [
            self.test_imports,
            self.test_basic_config,
            self.test_api_startup,
            self.test_web_interface
        ]
        
        results = []
        passed = 0
        failed = 0
        
        for test_func in smoke_tests:
            try:
                result = test_func()
                results.append({
                    'name': test_func.__name__,
                    'success': result,
                    'error': None
                })
                
                if result:
                    passed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                results.append({
                    'name': test_func.__name__,
                    'success': False,
                    'error': str(e)
                })
                failed += 1
        
        return {
            'success': failed == 0,
            'tests_run': len(smoke_tests),
            'tests_passed': passed,
            'tests_failed': failed,
            'results': results
        }
    
    def test_imports(self) -> bool:
        """Test that all modules can be imported."""
        try:
            from streamline_vpn.core.merger import StreamlineVPNMerger
            from streamline_vpn.web.unified_api import create_unified_app
            from streamline_vpn.utils.logging import get_logger
            return True
        except Exception as e:
            logger.error(f"Import test failed: {e}")
            return False
    
    def test_basic_config(self) -> bool:
        """Test basic configuration loading."""
        try:
            config_file = Path("config/sources.yaml")
            if not config_file.exists():
                logger.warning("No config file found, creating basic one")
                config_file.parent.mkdir(exist_ok=True)
                with open(config_file, 'w') as f:
                    f.write("sources:\n  free:\n    - https://example.com/config\n")
            
            import yaml
            with open(config_file) as f:
                config = yaml.safe_load(f)
            
            return 'sources' in config
        except Exception as e:
            logger.error(f"Config test failed: {e}")
            return False
    
    def test_api_startup(self) -> bool:
        """Test API can start up."""
        try:
            from streamline_vpn.web.unified_api import create_unified_app
            app = create_unified_app()
            return app is not None
        except Exception as e:
            logger.error(f"API startup test failed: {e}")
            return False
    
    def test_web_interface(self) -> bool:
        """Test web interface files exist."""
        try:
            web_files = [
                "docs/index.html",
                "docs/assets/js/main_fixed.js",
                "docs/assets/css/site.css"
            ]
            
            for file_path in web_files:
                if not Path(file_path).exists():
                    logger.error(f"Web file missing: {file_path}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Web interface test failed: {e}")
            return False
    
    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary."""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_duration = 0
        successful_categories = 0
        
        for category, result in results.items():
            total_tests += result.get('tests_run', 0)
            total_passed += result.get('tests_passed', 0)
            total_failed += result.get('tests_failed', 0)
            total_duration += result.get('duration', 0)
            
            if result.get('success', False):
                successful_categories += 1
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        overall_success = total_failed == 0 and successful_categories == len(results)
        
        return {
            'overall_success': overall_success,
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'success_rate': success_rate,
            'total_duration': total_duration,
            'successful_categories': successful_categories,
            'total_categories': len(results)
        }
    
    def save_test_results(self, results: Dict[str, Any], summary: Dict[str, Any]):
        """Save test results to file."""
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = output_dir / f"test_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'summary': summary
            }, f, indent=2)
        
        # Save summary
        summary_file = output_dir / f"test_summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"StreamlineVPN Test Results\n")
            f.write(f"========================\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Overall Success: {'✅' if summary['overall_success'] else '❌'}\n")
            f.write(f"Total Tests: {summary['total_tests']}\n")
            f.write(f"Passed: {summary['total_passed']}\n")
            f.write(f"Failed: {summary['total_failed']}\n")
            f.write(f"Success Rate: {summary['success_rate']:.1f}%\n")
            f.write(f"Duration: {summary['total_duration']:.2f}s\n\n")
            
            f.write("Category Results:\n")
            f.write("-" * 40 + "\n")
            for category, result in results.items():
                status = "✅" if result.get('success', False) else "❌"
                f.write(f"{category:<15} {status} {result.get('tests_passed', 0)}/{result.get('tests_run', 0)} tests\n")
        
        logger.info(f"Test results saved to: {results_file}")
        logger.info(f"Test summary saved to: {summary_file}")


def main():
    """Main test runner function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='StreamlineVPN Test Runner')
    parser.add_argument('--categories', '-c', nargs='+', 
                       choices=['unit', 'integration', 'api', 'e2e', 'performance'],
                       help='Test categories to run')
    parser.add_argument('--smoke', action='store_true', help='Run smoke tests only')
    parser.add_argument('--coverage', action='store_true', help='Enable coverage reporting')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    runner = StreamlineVPNTestRunner()
    
    if args.smoke:
        results = runner.run_smoke_tests()
        print(f"\nSmoke Test Results:")
        print(f"Success: {'✅' if results['success'] else '❌'}")
        print(f"Tests: {results['tests_passed']}/{results['tests_run']}")
        
        for result in results['results']:
            status = "✅" if result['success'] else "❌"
            print(f"  {result['name']}: {status}")
            if result['error']:
                print(f"    Error: {result['error']}")
    else:
        results = runner.run_all_tests(
            categories=args.categories,
            coverage=args.coverage,
            parallel=args.parallel,
            verbose=args.verbose
        )
        
        summary = results['summary']
        print(f"\nTest Results Summary:")
        print(f"Overall Success: {'✅' if summary['overall_success'] else '❌'}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['total_passed']}")
        print(f"Failed: {summary['total_failed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Duration: {summary['total_duration']:.2f}s")


if __name__ == '__main__':
    main()
