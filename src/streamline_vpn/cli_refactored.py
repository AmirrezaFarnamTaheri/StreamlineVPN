#!/usr/bin/env python3
"""
StreamlineVPN CLI (Refactored)
==============================

Refactored CLI using modular command structure for better maintainability.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from streamline_vpn.cli.main import main

if __name__ == "__main__":
    main()

