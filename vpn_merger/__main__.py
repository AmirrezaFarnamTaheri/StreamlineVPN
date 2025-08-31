"""
Main entry point for VPN Subscription Merger.

This module provides the command-line interface for the VPN merger application,
including source validation mode and graceful shutdown handling.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .utils.dependencies import check_dependencies, validate_environment
from .utils.environment import detect_and_run
from .core.source_manager import SourceManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('vpn_merger.log')
    ]
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point with graceful shutdown handling.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    if not validate_environment():
        return 1
    
    # Check for validation mode
    if len(sys.argv) > 1 and sys.argv[1] == '--validate':
        return _run_validation_mode()
    
    # Check for help
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        _print_help()
        return 0
    
    # Check for version
    if len(sys.argv) > 1 and sys.argv[1] in ['--version', '-v']:
        _print_version()
        return 0
    
    # Run main merger
    return _run_main_merger()


def _run_validation_mode() -> int:
    """Run source validation mode.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print("🔍 Source validation mode")
    try:
        source_manager = SourceManager()
        urls = source_manager.get_all_sources()
        print(f"🔎 Validating {len(urls)} sources...\n")
        
        results = _validate_all_sources(urls)
        _display_validation_results(results)
        return 0
        
    except Exception as e:
        logger.error(f"Validation mode failed: {e}")
        print(f"❌ Validation failed: {e}")
        return 1


def _validate_all_sources(urls: List[str]) -> List[Dict]:
    """Validate all source URLs asynchronously.
    
    Args:
        urls: List of URLs to validate
        
    Returns:
        List of validation results
    """
    async def _validate_all():
        from .core.health_checker import SourceHealthChecker
        
        semaphore = asyncio.Semaphore(20)
        results = []
        
        async def run_one(url: str) -> Dict:
            async with semaphore:
                async with SourceHealthChecker() as validator:
                    return await validator.validate_source(url)
        
        tasks = [asyncio.create_task(run_one(url)) for url in urls]
        
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
            except Exception as e:
                logger.error(f"Validation task failed: {e}")
                results.append({
                    'url': 'unknown',
                    'accessible': False,
                    'error': str(e),
                    'reliability_score': 0.0
                })
        
        return results
    
    try:
        return asyncio.run(_validate_all())
    except RuntimeError:
        # If already in an event loop, fallback
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(_validate_all())
        except Exception as e:
            logger.error(f"Failed to run validation: {e}")
            return []


def _display_validation_results(results: List[Dict]) -> None:
    """Display validation results in a formatted way.
    
    Args:
        results: List of validation results
    """
    accessible = [r for r in results if r.get('accessible')]
    accessible.sort(key=lambda r: r.get('reliability_score', 0.0), reverse=True)
    
    print(f"✅ Accessible: {len(accessible)}/{len(results)}\n")
    
    for result in accessible[:20]:  # Show top 20
        url = result.get('url', 'unknown')
        score = result.get('reliability_score', 0.0)
        configs = result.get('estimated_configs', 0)
        protocols = ','.join(result.get('protocols_found', []))
        
        print(f" • {url} | score={score:.2f} | cfgs={configs} | protos={protocols}")


def _print_help() -> None:
    """Print help information."""
    print("VPN Subscription Merger - Command Line Interface")
    print("=" * 50)
    print()
    print("Usage:")
    print("  python -m vpn_merger              # Run main merger")
    print("  python -m vpn_merger --validate   # Validate sources only")
    print("  python -m vpn_merger --help       # Show this help")
    print("  python -m vpn_merger --version    # Show version")
    print()
    print("Options:")
    print("  --validate    Run source validation mode")
    print("  --help, -h    Show help information")
    print("  --version, -v Show version information")


def _print_version() -> None:
    """Print version information."""
    from . import __version__, __author__, __status__
    print(f"VPN Subscription Merger v{__version__}")
    print(f"Status: {__status__}")
    print(f"Author: {__author__}")


def _run_main_merger() -> int:
    """Run the main merger application.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    # Setup graceful shutdown handling
    shutdown_flag = {"set": False}
    
    def _handle_signal(signum: int, frame) -> None:
        if not shutdown_flag["set"]:
            shutdown_flag["set"] = True
            print(f"\n🛑 Received signal {signum}, finishing current tasks and shutting down...")
    
    # Register signal handlers
    for sig_name in ("SIGTERM", "SIGINT"):
        sig = getattr(signal, sig_name, None)
        if sig is not None:
            try:
                signal.signal(sig, _handle_signal)
            except Exception as e:
                logger.debug(f"Could not register signal handler for {sig_name}: {e}")
    
    try:
        return detect_and_run(config=None)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Main merger failed: {e}")
        print(f"❌ Error: {e}")
        print("\n📋 Alternative execution methods:")
        print("   • For Jupyter: await run_in_jupyter()")
        print("   • For scripts: python -m vpn_merger")
        return 1


if __name__ == "__main__":
    sys.exit(main())
