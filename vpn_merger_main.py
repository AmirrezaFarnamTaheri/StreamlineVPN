#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main entry point that delegates to the vpn_merger module."""
    print("🚀 VPN Subscription Merger v2.0.0")
    print("=" * 50)
    
    try:
        # Import and run the main module
        from vpn_merger.__main__ import main as module_main
        return module_main()
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure the vpn_merger package is properly installed.")
        return 1
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
