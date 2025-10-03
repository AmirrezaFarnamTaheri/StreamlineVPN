#!/usr/bin/env python3
"""
StreamlineVPN CLI
=================

This script serves as the main entry point for the StreamlineVPN command-line
interface. It discovers and executes the refactored CLI application.
"""

import sys
from pathlib import Path

# Ensure the source root is on the Python path
# This allows the CLI to be run directly from the source tree
if __name__ == "__main__":
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

try:
    # Import the true main function from the modular CLI structure
    from streamline_vpn.cli.main import main
except ImportError as e:
    print(f"Error: Unable to import the StreamlineVPN CLI module. ({e})")
    print("Please ensure the application is installed correctly or run from the project root.")
    sys.exit(1)


if __name__ == "__main__":
    main()