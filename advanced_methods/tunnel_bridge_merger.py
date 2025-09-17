"""
Tunnel Bridge Merger
===================

Parser for tunnel bridge configurations.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def parse_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a tunnel bridge configuration line.
    
    Args:
        line: Configuration line
        
    Returns:
        Parsed configuration dictionary or None
    """
    if not line or not line.strip():
        return None
    
    line = line.strip()
    
    try:
        # Simple tunnel bridge format: server:port:method:password
        parts = line.split(':')
        if len(parts) >= 4:
            return {
                'protocol': 'tunnel_bridge',
                'server': parts[0],
                'port': int(parts[1]),
                'method': parts[2],
                'password': parts[3]
            }
        else:
            logger.debug(f"Invalid tunnel bridge format: {line}")
            return None
            
    except Exception as e:
        logger.debug(f"Failed to parse tunnel bridge line: {e}")
        return None
