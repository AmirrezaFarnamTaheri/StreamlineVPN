"""
Enhanced Source Validator
=========================

Advanced source validation with quality scoring, historical tracking, and
comprehensive source analysis for VPN configuration sources.

This module now uses the refactored components for better maintainability.
"""

# Import the refactored validator
from .validation.enhanced_source_validator_refactored import EnhancedSourceValidator

# Re-export for backward compatibility
__all__ = ["EnhancedSourceValidator"]
