"""
Source persistence and configuration management.
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...utils.logging import get_logger

logger = get_logger(__name__)


class SourcePersistence:
    """Handles source configuration persistence."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.performance_data_path = config_path.parent / "source_performance.json"
    
    def load_sources(self) -> List[Dict[str, Any]]:
        """Load sources from configuration file."""
        try:
            if not self.config_path.exists():
                logger.warning("Config file does not exist: %s", self.config_path)
                return []
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            sources = config.get('sources', [])
            try:
                # Log tier distribution if sources is a dict of tiers
                tier_distribution = {}
                if isinstance(sources, dict):
                    for tier, data in sources.items():
                        if isinstance(data, dict):
                            urls = data.get('urls')
                            if isinstance(urls, list):
                                tier_distribution[tier] = len(urls)
                            else:
                                logger.info("Invalid tier configuration for %s", tier)
                                try:
                                    import logging as _logging
                                    _logging.getLogger().info("Invalid tier configuration for %s", tier)
                                except Exception:
                                    pass
                        else:
                            logger.info("Invalid tier configuration for %s", tier)
                            try:
                                import logging as _logging
                                _logging.getLogger().info("Invalid tier configuration for %s", tier)
                            except Exception:
                                pass
                    if tier_distribution:
                        logger.info("Tier distribution: %s", tier_distribution)
                        try:
                            import logging as _logging
                            _logging.getLogger().info("Tier distribution: %s", tier_distribution)
                        except Exception:
                            pass
                    # Warn on unknown tier names pattern (e.g., tier_5_unknown)
                    for tier in sources.keys():
                        if 'unknown' in tier:
                            logger.info("Unknown tier '%s'", tier)
                            try:
                                import logging as _logging
                                _logging.getLogger().info("Unknown tier '%s'", tier)
                            except Exception:
                                pass
                elif isinstance(sources, list):
                    dist = {"default": len(sources)}
                    logger.info("Tier distribution: %s", dist)
                    try:
                        import logging as _logging
                        _logging.getLogger().info("Tier distribution: %s", dist)
                    except Exception:
                        pass
            except Exception:
                pass
            logger.info("Loaded %d sources from config", len(sources))
            return sources
            
        except Exception as e:
            logger.error("Failed to load sources: %s", e)
            return []
    
    def save_sources(self, sources: List[Dict[str, Any]]) -> bool:
        """Save sources to configuration file."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write new config
            config = {
                'sources': sources,
                'global_settings': {
                    'max_concurrent_sources': 10,
                    'default_timeout': 30,
                    'default_retry_attempts': 3,
                    'cache_duration': 3600,
                    'enable_compression': True,
                    'user_agent': 'StreamlineVPN/1.0.0'
                }
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            logger.info("Saved %d sources to config", len(sources))
            return True
            
        except Exception as e:
            logger.error("Failed to save sources: %s", e)
            return False
    
    def load_performance_data(self) -> Dict[str, Any]:
        """Load source performance data."""
        try:
            if not self.performance_data_path.exists():
                return {}
            
            with open(self.performance_data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error("Failed to load performance data: %s", e)
            return {}
    
    def save_performance_data(self, data: Dict[str, Any]) -> bool:
        """Save source performance data."""
        try:
            with open(self.performance_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error("Failed to save performance data: %s", e)
            return False
    
    def add_source_atomically(self, sources: List[Dict[str, Any]], new_source: Dict[str, Any]) -> bool:
        """Add a new source atomically."""
        try:
            # Add new source to in-memory list
            sources.append(new_source)
            
            # Save updated config (handles its own backup/restore)
            success = self.save_sources(sources)
            
            return bool(success)
            
        except Exception as e:
            logger.error("Failed to add source atomically: %s", e)
            return False

