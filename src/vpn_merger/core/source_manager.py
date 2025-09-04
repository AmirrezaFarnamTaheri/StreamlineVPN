"""
Source Manager
=============

Manages VPN subscription sources with tiered organization and fallback support.
Enhanced with additional source categories and quality validation.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)


class SourceManager:
    """Unified source management with tiered organization and reliability scoring.

    This class handles loading, organizing, and providing access to VPN subscription
    sources from configuration files with comprehensive fallback support.
    Enhanced with additional source categories and quality validation.

    Attributes:
        config_path: Path to the configuration file
        sources: Dictionary mapping tier names to lists of URLs
        enhanced_validator: Optional enhanced source validator for quality analysis
        source_categories: Set of available source categories
    """

    def __init__(self, config_path: str | Path = "config/sources.unified.yaml", use_enhanced_validation: bool = False):
        """Initialize the source manager.

        Args:
            config_path: Path to the configuration file
            use_enhanced_validation: Whether to use enhanced source validation
        """
        self.config_path = Path(config_path)
        self.use_enhanced_validation = use_enhanced_validation
        self.enhanced_validator = None
        self.source_categories = set()
        self.sources = self._load_sources()
        
        # Initialize enhanced validator if requested
        if use_enhanced_validation:
            try:
                from .enhanced_source_validator import EnhancedSourceValidator
                self.enhanced_validator = EnhancedSourceValidator()
                logger.info("Enhanced source validation enabled")
            except ImportError:
                logger.warning("Enhanced source validation requested but not available")
                self.use_enhanced_validation = False

    def _load_sources(self) -> dict[str, list[str]]:
        """Load sources from unified configuration file with fallback support.

        Returns:
            Dictionary mapping tier names to lists of source URLs
        """
        try:
            if yaml is None:
                logger.warning("PyYAML not available, using minimal fallback sources")
                return self._get_minimal_fallback_sources()

            if not self.config_path.exists():
                logger.warning(
                    f"Config file {self.config_path} not found, using minimal fallback sources"
                )
                return self._get_minimal_fallback_sources()

            with open(self.config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

                if not config or not isinstance(config, dict):
                    logger.warning("Invalid config file format, using minimal fallback sources")
                    return self._get_minimal_fallback_sources()

                # Handle the complex configuration structure
                sources = config.get("sources", {})
                processed_sources = self._process_config_sources(sources)

                # If no tiers or no URLs found, use minimal fallback
                total_urls = sum(len(urls) for urls in processed_sources.values()) if processed_sources else 0
                if not processed_sources or total_urls == 0:
                    logger.warning(
                        "No valid sources found in config, using minimal fallback sources"
                    )
                    return self._get_minimal_fallback_sources()

                logger.info(
                    f"Loaded {total_urls} sources from {len(processed_sources)} tiers"
                )
                return processed_sources

        except FileNotFoundError as e:
            logger.warning(f"Config file not found: {e}")
            return self._get_minimal_fallback_sources()
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            return self._get_minimal_fallback_sources()
        except PermissionError as e:
            logger.error(f"Permission denied accessing config file: {e}")
            return self._get_minimal_fallback_sources()
        except Exception as e:
            logger.critical(f"Unexpected error loading sources: {e}")
            raise  # Re-raise unexpected errors

    def _process_config_sources(self, sources: dict) -> dict[str, list[str]]:
        """Process configuration sources and extract URLs.

        Args:
            sources: Raw sources configuration dictionary

        Returns:
            Processed sources dictionary
        """
        processed = {}
        for tier_name, tier_data in sources.items():
            # Track source categories
            self.source_categories.add(tier_name)
            
            urls = []
            if isinstance(tier_data, list):
                urls = [url for url in tier_data if self._is_valid_url(url)]
            elif isinstance(tier_data, dict):
                urls = self._extract_urls_from_dict(tier_data)
            processed[tier_name] = urls
        return processed

    def _extract_urls_from_dict(self, data: dict, depth: int = 0) -> list[str]:
        from .source_utils import extract_urls_from_dict
        return extract_urls_from_dict(data, depth)

    def _extract_urls_from_category(self, category_data) -> list[str]:
        """Extract URLs from a category's data structure.

        Args:
            category_data: Category data to extract URLs from

        Returns:
            List of extracted URLs
        """
        from .source_utils import extract_urls_from_category
        return extract_urls_from_category(category_data)

    def _get_minimal_fallback_sources(self) -> dict[str, list[str]]:
        """Get minimal fallback sources for emergency use only.

        Returns:
            Dictionary with emergency fallback sources
        """
        from .source_utils import get_minimal_fallback_sources
        return get_minimal_fallback_sources()

    def get_all_sources(self) -> list[str]:
        """Get all sources as a flat list.

        Returns:
            List of all source URLs
        """
        all_sources = []
        for tier, sources in self.sources.items():
            all_sources.extend(sources)
        # If still empty (e.g., config had no valid URLs), fall back to minimal
        if not all_sources:
            try:
                from .source_utils import get_minimal_fallback_sources

                fb = get_minimal_fallback_sources()
                fallback_list: list[str] = []
                for arr in fb.values():
                    fallback_list.extend(arr)
                return fallback_list
            except Exception:
                return []
        return all_sources

    def get_sources_by_tier(self, tier: str) -> list[str]:
        """Get sources from a specific tier.

        Args:
            tier: Tier name to get sources from

        Returns:
            List of source URLs for the specified tier
        """
        return self.sources.get(tier, [])

    def get_prioritized_sources(self) -> list[str]:
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
            "emergency_fallback",
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

    def get_tier_info(self) -> dict[str, int]:
        """Get source count by tier.

        Returns:
            Dictionary mapping tier names to source counts
        """
        return {tier: len(sources) for tier, sources in self.sources.items()}

    def get_tier_names(self) -> list[str]:
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
        from .source_utils import is_valid_url
        return is_valid_url(url)

    def reload_sources(self) -> None:
        """Reload sources from the configuration file."""
        logger.info("Reloading sources from configuration")
        self.sources = self._load_sources()

    def get_source_summary(self) -> dict[str, int | list[str]]:
        """Get a comprehensive summary of all sources.

        Returns:
            Dictionary containing source summary information
        """
        return {
            "total_sources": self.get_source_count(),
            "tier_count": len(self.sources),
            "tier_info": self.get_tier_info(),
            "tier_names": self.get_tier_names(),
            "prioritized_count": len(self.get_prioritized_sources()),
        }

    def add_custom_sources(self, sources: list[str]) -> None:
        """Add custom sources to the manager.

        Args:
            sources: List of custom source URLs to add
        """
        if not sources:
            return

        # Add to a custom tier
        if "custom" not in self.sources:
            self.sources["custom"] = []

        for source in sources:
            if self._is_valid_url(source) and source not in self.sources["custom"]:
                self.sources["custom"].append(source)

        logger.info(f"Added {len(sources)} custom sources")

    def remove_sources(self, sources: list[str]) -> None:
        """Remove sources from the manager.

        Args:
            sources: List of source URLs to remove
        """
        if not sources:
            return

        removed_count = 0
        for tier in self.sources:
            original_count = len(self.sources[tier])
            self.sources[tier] = [s for s in self.sources[tier] if s not in sources]
            removed_count += original_count - len(self.sources[tier])

        logger.info(f"Removed {removed_count} sources")

    def get_statistics(self) -> dict[str, int | list[str]]:
        """Get source management statistics.

        Returns:
            Dictionary containing source statistics
        """
        return {
            "total_sources": self.get_source_count(),
            "tier_count": len(self.sources),
            "tier_info": self.get_tier_info(),
            "tier_names": self.get_tier_names(),
            "prioritized_count": len(self.get_prioritized_sources()),
            "sources_by_tier": self.sources,
            "source_categories": list(self.source_categories),
            "enhanced_validation_enabled": self.use_enhanced_validation,
        }
        
    def get_sources_by_category(self, category: str) -> List[str]:
        """Get sources from a specific category.
        
        Args:
            category: Category name to get sources from
            
        Returns:
            List of source URLs for the specified category
        """
        return self.sources.get(category, [])
        
    def get_community_maintained_sources(self) -> List[str]:
        """Get community-maintained sources.
        
        Returns:
            List of community-maintained source URLs
        """
        return self.get_sources_by_category("community_maintained")
        
    def get_aggregator_sources(self) -> List[str]:
        """Get aggregator service sources.
        
        Returns:
            List of aggregator service source URLs
        """
        return self.get_sources_by_category("aggregator_services")
        
    def get_regional_sources(self, region: Optional[str] = None) -> List[str]:
        """Get regional sources.
        
        Args:
            region: Specific region (asia_pacific, europe, americas) or None for all
            
        Returns:
            List of regional source URLs
        """
        if region:
            return self.get_sources_by_category(f"regional_specific.{region}")
        else:
            # Return all regional sources
            all_regional = []
            for category in self.source_categories:
                if category.startswith("regional_specific."):
                    all_regional.extend(self.sources.get(category, []))
            return all_regional
            
    def get_protocol_specific_sources(self, protocol: Optional[str] = None) -> List[str]:
        """Get protocol-specific sources.
        
        Args:
            protocol: Specific protocol (shadowsocks, vmess, vless, trojan, wireguard) or None for all
            
        Returns:
            List of protocol-specific source URLs
        """
        if protocol:
            return self.get_sources_by_category(f"protocol_specific.{protocol}")
        else:
            # Return all protocol-specific sources
            all_protocol = []
            for category in self.source_categories:
                if category.startswith("protocol_specific."):
                    all_protocol.extend(self.sources.get(category, []))
            return all_protocol
            
    def get_quality_validated_sources(self) -> List[str]:
        """Get quality-validated sources.
        
        Returns:
            List of quality-validated source URLs
        """
        return self.get_sources_by_category("quality_validated")
        
    def get_enhanced_sources(self) -> Dict[str, List[str]]:
        """Get all enhanced source categories.
        
        Returns:
            Dictionary mapping enhanced categories to source URLs
        """
        enhanced_categories = [
            "community_maintained",
            "aggregator_services", 
            "quality_validated"
        ]
        
        # Add regional categories
        for category in self.source_categories:
            if category.startswith("regional_specific."):
                enhanced_categories.append(category)
                
        # Add protocol-specific categories
        for category in self.source_categories:
            if category.startswith("protocol_specific."):
                enhanced_categories.append(category)
                
        # Add specialized categories
        for category in self.source_categories:
            if category.startswith("specialized_enhanced."):
                enhanced_categories.append(category)
        
        return {category: self.sources.get(category, []) for category in enhanced_categories}
        
    async def validate_sources_quality(self, sources: Optional[List[str]] = None) -> Dict[str, float]:
        """Validate source quality using enhanced validator.
        
        Args:
            sources: List of sources to validate, or None to validate all sources
            
        Returns:
            Dictionary mapping source URLs to quality scores
        """
        if not self.use_enhanced_validation or not self.enhanced_validator:
            logger.warning("Enhanced validation not available")
            return {}
            
        if sources is None:
            sources = self.get_all_sources()
            
        if not sources:
            return {}
            
        try:
            async with self.enhanced_validator:
                quality_metrics = await self.enhanced_validator.validate_multiple_sources_quality(sources)
                return {metrics.url: metrics.quality_score for metrics in quality_metrics}
        except Exception as e:
            logger.error(f"Error validating source quality: {e}")
            return {}
            
    def get_source_quality_statistics(self) -> Dict[str, Any]:
        """Get source quality statistics.
        
        Returns:
            Dictionary with quality statistics
        """
        if not self.use_enhanced_validation or not self.enhanced_validator:
            return {"enhanced_validation": False}
            
        try:
            return self.enhanced_validator.get_quality_statistics()
        except Exception as e:
            logger.error(f"Error getting quality statistics: {e}")
            return {"error": str(e)}
            
    def filter_sources_by_quality(self, min_quality: float = 0.5) -> List[str]:
        """Filter sources by minimum quality score.
        
        Args:
            min_quality: Minimum quality score threshold
            
        Returns:
            List of high-quality source URLs
        """
        if not self.use_enhanced_validation or not self.enhanced_validator:
            logger.warning("Enhanced validation not available")
            return self.get_all_sources()
            
        try:
            quality_sources = self.enhanced_validator.filter_by_quality(min_quality)
            return [metrics.url for metrics in quality_sources]
        except Exception as e:
            logger.error(f"Error filtering sources by quality: {e}")
            return self.get_all_sources()
            
    def get_top_quality_sources(self, limit: int = 10) -> List[str]:
        """Get top quality sources.
        
        Args:
            limit: Maximum number of sources to return
            
        Returns:
            List of top quality source URLs
        """
        if not self.use_enhanced_validation or not self.enhanced_validator:
            logger.warning("Enhanced validation not available")
            return self.get_all_sources()[:limit]
            
        try:
            top_sources = self.enhanced_validator.get_top_quality_sources(limit)
            return [metrics.url for metrics in top_sources]
        except Exception as e:
            logger.error(f"Error getting top quality sources: {e}")
            return self.get_all_sources()[:limit]
