#!/usr/bin/env python3

"""
VPN Subscription Merger - Main Entry Point
==========================================

A high-performance, production-ready VPN subscription merger that aggregates and processes
VPN configurations from multiple sources with advanced filtering, validation, and output formatting.

This is the main entry point for the refactored, modular VPN merger package.

Features:
• Complete source collection (500+ VPN sources with tiered reliability)
• Real-time URL availability testing and dead link removal
• Server reachability testing with response time measurement
• Smart sorting by connection speed and protocol preference
• Event loop compatibility (Jupyter, IPython, regular Python)
• Advanced deduplication with semantic analysis
• Multiple output formats (raw, base64, CSV, JSON, sing-box, clash)
• Comprehensive error handling and retry logic
• Best practices implemented throughout

Requirements: pip install aiohttp aiodns nest-asyncio
Author: VPN Merger Team
Expected Output: 1M+ tested and sorted configs
"""

import logging
import sys
from pathlib import Path

# Ensure local imports work whether using src/ layout or flat layout
_root = Path(__file__).parent
_src = _root / "src"
if _src.exists():
    sys.path.insert(0, str(_src))
else:
    sys.path.insert(0, str(_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("vpn_merger.log")],
)
logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main entry point that delegates to the vpn_merger module.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("🚀 VPN Subscription Merger v2.0.0")
    logger.info("=" * 50)

    try:
        # Import and run the main module
        from vpn_merger.__main__ import main as module_main

        return module_main()
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error(f"❌ Import error: {e}")
        logger.error("Please ensure the vpn_merger package is properly installed.")
        logger.error("Run: pip install -r requirements.txt")
        return 1
    except KeyboardInterrupt:
        logger.info("\n🛑 Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during execution: {e}")
        logger.error(f"❌ Error during execution: {e}")
        logger.error("\n📋 For help, run: python vpn_merger_main.py --help")
        return 1


if __name__ == "__main__":
    sys.exit(main())
