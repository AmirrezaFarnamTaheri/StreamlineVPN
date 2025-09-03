"""
Main entry point for VPN Subscription Merger.

This module provides the command-line interface for the VPN merger application,
including source validation mode and graceful shutdown handling.
"""

import argparse
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


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="VPN Subscription Merger - High-performance VPN configuration aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m vpn_merger                    # Run main merger
  python -m vpn_merger --web              # Start integrated web server
  python -m vpn_merger --web --web-port 9000  # Web server on custom port
  python -m vpn_merger --validate         # Validate sources only
  python -m vpn_merger --concurrent 20    # Run with custom concurrency
  python -m vpn_merger --output-dir ./my_output  # Custom output directory
        """
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run source validation mode only'
    )
    
    parser.add_argument(
        '--concurrent',
        type=int,
        default=50,
        help='Maximum number of concurrent processing tasks (default: 50)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Output directory for results (default: output)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (default: config/sources.unified.yaml)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-error output'
    )
    
    parser.add_argument(
        '--web',
        action='store_true',
        help='Start integrated web server with VPN merger, config generator, and analytics'
    )
    
    parser.add_argument(
        '--web-port',
        type=int,
        default=8000,
        help='Port for the integrated web server (default: 8000)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='VPN Subscription Merger v2.0.0'
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point with graceful shutdown handling.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    args = parse_arguments()
    
    # Configure logging level based on arguments
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    if not validate_environment():
        return 1
    
    # Check for web mode
    if args.web:
        return _run_web_mode(args)
    
    # Check for validation mode
    if args.validate:
        return _run_validation_mode(args)
    
    # Run main merger
    return _run_main_merger(args)


def _run_web_mode(args: argparse.Namespace) -> int:
    """
    Run integrated web server mode.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("🌐 Starting integrated web server mode")
    try:
        from .web.integrated_server import IntegratedWebServer
        
        # Create and start the integrated web server
        server = IntegratedWebServer(port=args.web_port)
        
        async def run_server():
            await server.start()
            logger.info("✅ Integrated web server started successfully")
            logger.info("Press Ctrl+C to stop the server")
            
            # Keep the server running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Shutting down web server...")
                await server.stop()
        
        # Run the server
        asyncio.run(run_server())
        return 0
        
    except ImportError as e:
        logger.error(f"Failed to import web components: {e}")
        logger.error("Please ensure all web dependencies are installed:")
        logger.error("pip install aiohttp aiofiles")
        return 1
    except Exception as e:
        logger.error(f"Web server failed: {e}")
        logger.error(f"❌ Web server error: {e}")
        return 1


def _run_validation_mode(args: argparse.Namespace) -> int:
    """
    Run source validation mode.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("🔍 Source validation mode")
    try:
        source_manager = SourceManager()
        urls = source_manager.get_all_sources()
        logger.info(f"🔎 Validating {len(urls)} sources...\n")
        
        results = _validate_all_sources(urls, args.concurrent)
        _display_validation_results(results)
        return 0
        
    except Exception as e:
        logger.error(f"Validation mode failed: {e}")
        logger.error(f"❌ Validation failed: {e}")
        return 1


def _validate_all_sources(urls: List[str], max_concurrent: int) -> List[Dict]:
    """
    Validate all source URLs asynchronously.
    
    Args:
        urls: List of URLs to validate
        max_concurrent: Maximum concurrent validation tasks
        
    Returns:
        List of validation results
    """
    async def _validate_all():
        from .core.source_validator import UnifiedSourceValidator
        
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        
        async def run_one(url: str) -> Dict:
            async with semaphore:
                async with UnifiedSourceValidator() as validator:
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
    """
    Display validation results in a formatted way.
    
    Args:
        results: List of validation results
    """
    accessible = [r for r in results if r.get('accessible')]
    accessible.sort(key=lambda r: r.get('reliability_score', 0.0), reverse=True)
    
    logger.info(f"✅ Accessible: {len(accessible)}/{len(results)}")
    
    for result in accessible[:20]:  # Show top 20
        url = result.get('url', 'unknown')
        score = result.get('reliability_score', 0.0)
        configs = result.get('estimated_configs', 0)
        protocols = ','.join(result.get('protocols_found', []))
        
        logger.info(f" • {url} | score={score:.2f} | cfgs={configs} | protos={protocols}")


def _run_main_merger(args: argparse.Namespace) -> int:
    """
    Run the main merger application.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    # Setup graceful shutdown handling
    shutdown_flag = {"set": False}
    
    def _handle_signal(signum: int, frame) -> None:
        if not shutdown_flag["set"]:
            shutdown_flag["set"] = True
            logger.info(f"\n🛑 Received signal {signum}, finishing current tasks and shutting down...")
    
    # Register signal handlers
    for sig_name in ("SIGTERM", "SIGINT"):
        sig = getattr(signal, sig_name, None)
        if sig is not None:
            try:
                signal.signal(sig, _handle_signal)
            except Exception as e:
                logger.debug(f"Could not register signal handler for {sig_name}: {e}")
    
    try:
        # Pass configuration to detect_and_run
        config = {
            'concurrent': args.concurrent,
            'output_dir': args.output_dir,
            'config_file': args.config
        }
        return detect_and_run(config=config)
    except KeyboardInterrupt:
        logger.info("\n🛑 Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Main merger failed: {e}")
        logger.error(f"❌ Error: {e}")
        logger.error("\n📋 Alternative execution methods:")
        logger.error("   • For Jupyter: await run_in_jupyter()")
        logger.error("   • For scripts: python -m vpn_merger")
        return 1


if __name__ == "__main__":
    sys.exit(main())
