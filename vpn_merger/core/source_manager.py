"""
Source Manager
=============

Manages VPN subscription sources with tiered organization and fallback support.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


class SourceManager:
    """Unified source management with tiered organization and reliability scoring.
    
    This class handles loading, organizing, and providing access to VPN subscription
    sources from configuration files with comprehensive fallback support.
    
    Attributes:
        config_path: Path to the configuration file
        sources: Dictionary mapping tier names to lists of URLs
    """
    
    def __init__(self, config_path: Union[str, Path] = "config/sources.unified.yaml"):
        """Initialize the source manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self.sources = self._load_sources()
    
    def _load_sources(self) -> Dict[str, List[str]]:
        """Load sources from unified configuration file with fallback support.
        
        Returns:
            Dictionary mapping tier names to lists of source URLs
        """
        try:
            if yaml is None:
                logger.warning("PyYAML not available, using minimal fallback sources")
                return self._get_minimal_fallback_sources()
            
            if not self.config_path.exists():
                logger.warning(f"Config file {self.config_path} not found, using minimal fallback sources")
                return self._get_minimal_fallback_sources()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
                if not config or not isinstance(config, dict):
                    logger.warning("Invalid config file format, using minimal fallback sources")
                    return self._get_minimal_fallback_sources()
                
                # Handle the complex configuration structure
                sources = config.get('sources', {})
                processed_sources = self._process_config_sources(sources)
                
                # If no sources found, use minimal fallback
                if not processed_sources:
                    logger.warning("No valid sources found in config, using minimal fallback sources")
                    return self._get_minimal_fallback_sources()
                
                logger.info(f"Loaded {sum(len(urls) for urls in processed_sources.values())} sources from {len(processed_sources)} tiers")
                return processed_sources
                
        except Exception as e:
            logger.error(f"Error loading sources: {e}")
            return self._get_minimal_fallback_sources()
    
    def _process_config_sources(self, sources: Dict) -> Dict[str, List[str]]:
        """Process configuration sources and extract URLs.
        
        Args:
            sources: Raw sources configuration dictionary
            
        Returns:
            Processed sources dictionary
        """
        processed_sources = {}
        
        for category, category_data in sources.items():
            if not isinstance(category, str):
                logger.warning(f"Skipping invalid category: {category}")
                continue
                
            urls = self._extract_urls_from_category(category_data)
            if urls:
                processed_sources[category] = urls
        
        return processed_sources
    
    def _extract_urls_from_category(self, category_data) -> List[str]:
        """Extract URLs from a category's data structure.
        
        Args:
            category_data: Category data to extract URLs from
            
        Returns:
            List of extracted URLs
        """
        urls = []
        
        if isinstance(category_data, dict) and 'urls' in category_data:
            # Handle structured format with urls array
            for url_data in category_data['urls']:
                if isinstance(url_data, dict) and 'url' in url_data:
                    url = url_data['url']
                    if self._is_valid_url(url):
                        urls.append(url)
        elif isinstance(category_data, list):
            # Handle simple list format
            valid_urls = [url for url in category_data if self._is_valid_url(url)]
            urls.extend(valid_urls)
        elif isinstance(category_data, dict):
            # Handle nested structure
            for key, value in category_data.items():
                if isinstance(value, dict) and 'urls' in value:
                    for url_data in value['urls']:
                        if isinstance(url_data, dict) and 'url' in url_data:
                            url = url_data['url']
                            if self._is_valid_url(url):
                                urls.append(url)
        
        return urls
    
    def _get_minimal_fallback_sources(self) -> Dict[str, List[str]]:
        """Get minimal fallback sources for emergency use only.
        
        Returns:
            Dictionary with emergency fallback sources
        """
        logger.warning("Using minimal fallback sources - please configure sources.unified.yaml")
        return {
            "emergency_fallback": [
                "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_base64.txt"
            ]
        }
    
    def get_all_sources(self) -> List[str]:
        """Get all sources as a flat list.
        
        Returns:
            List of all source URLs
        """
        all_sources = []
        for tier, sources in self.sources.items():
            all_sources.extend(sources)
        return all_sources
    
    def get_sources_by_tier(self, tier: str) -> List[str]:
        """Get sources from a specific tier.
        
        Args:
            tier: Tier name to get sources from
            
        Returns:
            List of source URLs for the specified tier
        """
        return self.sources.get(tier, [])
    
    def get_prioritized_sources(self) -> List[str]:
        """Get sources in priority order (tier 1 first).
        
        Returns:
            List of source URLs in priority order
        """
        prioritized = []
        tier_order = [
            "tier_1_premium", 
            "tier_2_reliable", 
            "tier_3_bulk", 
            "specialized", 
            "regional", 
            "experimental", 
            "emergency_fallback"
        ]
        
        for tier in tier_order:
            if tier in self.sources:
                prioritized.extend(self.sources[tier])
        
        return prioritized
    
    def get_source_count(self) -> int:
        """Get total number of sources.
        
        Returns:
            Total count of all sources
        """
        return len(self.get_all_sources())
    
    def get_tier_info(self) -> Dict[str, int]:
        """Get source count by tier.
        
        Returns:
            Dictionary mapping tier names to source counts
        """
        return {tier: len(sources) for tier, sources in self.sources.items()}
    
    def get_tier_names(self) -> List[str]:
        """Get list of available tier names.
        
        Returns:
            List of tier names
        """
        return list(self.sources.keys())
    
    def validate_source_url(self, url: str) -> bool:
        """Validate if a source URL is properly formatted.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        return self._is_valid_url(url)
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid and properly formatted.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        
        url = url.strip()
        if not url:
            return False
        
        # Basic URL validation
        valid_schemes = ['http://', 'https://']
        return any(url.startswith(scheme) for scheme in valid_schemes)
    
    def reload_sources(self) -> None:
        """Reload sources from the configuration file."""
        logger.info("Reloading sources from configuration")
        self.sources = self._load_sources()
    
    def get_source_summary(self) -> Dict[str, Union[int, List[str]]]:
        """Get a comprehensive summary of all sources.
        
        Returns:
            Dictionary containing source summary information
        """
        return {
            'total_sources': self.get_source_count(),
            'tier_count': len(self.sources),
            'tier_info': self.get_tier_info(),
            'tier_names': self.get_tier_names(),
            'prioritized_count': len(self.get_prioritized_sources())
        }
