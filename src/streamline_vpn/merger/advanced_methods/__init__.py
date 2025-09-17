"""
Advanced Methods
===============

Advanced VPN configuration processing methods.
"""

from .http_injector_merger import parse_ehi
from .tunnel_bridge_merger import parse_line

__all__ = ["parse_ehi", "parse_line"]
