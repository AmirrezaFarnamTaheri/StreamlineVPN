"""
HTTP Injector Merger
===================

Parser for HTTP Injector (.ehi) files.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def parse_ehi(content: str) -> List[Dict[str, Any]]:
    """Parse HTTP Injector (.ehi) file content.
    
    Args:
        content: EHI file content
        
    Returns:
        List of parsed configurations
    """
    configs = []
    
    try:
        lines = content.split('\n')
        current_config = {}
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('[CONFIG]'):
                if current_config:
                    configs.append(current_config)
                current_config = {}
            elif '=' in line:
                key, value = line.split('=', 1)
                current_config[key.strip()] = value.strip()
        
        # Add the last config
        if current_config:
            configs.append(current_config)
        
        logger.debug(f"Parsed {len(configs)} EHI configurations")
        return configs
        
    except Exception as e:
        logger.error(f"Failed to parse EHI content: {e}")
        return []
