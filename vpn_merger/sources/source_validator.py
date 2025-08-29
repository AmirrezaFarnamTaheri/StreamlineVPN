from __future__ import annotations

"""
Compatibility wrapper for SourceValidator.

This module re-exports SourceValidator from vpn_merger.sources.validator so
consumers using the documented path `vpn_merger/sources/source_validator.py`
can import it without changes.
"""

from .validator import SourceValidator  # noqa: F401

