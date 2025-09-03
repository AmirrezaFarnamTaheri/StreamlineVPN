#!/usr/bin/env python3
"""
Remove Hardcoded Sources Script
Removes hardcoded sources from vpn_merger.py after they've been moved to unified configuration
"""

import re


def remove_hardcoded_sources():
    """Remove hardcoded source lists from vpn_merger.py."""

    file_path = "vpn_merger.py"

    # Read the file
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Remove the hardcoded source lists
    # Pattern to match the source lists with proper multiline matching
    patterns = [
        r"    IRANIAN_PRIORITY = \[.*?\]",
        r"    INTERNATIONAL_MAJOR = \[.*?\]",
        r"    COMPREHENSIVE_BATCH = \[.*?\]",
    ]

    modified_content = content
    for pattern in patterns:
        modified_content = re.sub(pattern, "", modified_content, flags=re.DOTALL | re.MULTILINE)

    # Clean up extra whitespace
    modified_content = re.sub(r"\n\s*\n\s*\n", "\n\n", modified_content)

    # Write the modified content back
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(modified_content)

    print("Hardcoded sources removed from vpn_merger.py")


if __name__ == "__main__":
    remove_hardcoded_sources()
