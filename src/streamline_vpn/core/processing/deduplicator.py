"""
Configuration Deduplicator
===========================

Handles deduplication of VPN configurations.
"""

import hashlib
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict

from ...models.configuration import VPNConfiguration
from ...utils.logging import get_logger

logger = get_logger(__name__)


class ConfigurationDeduplicator:
    """Deduplicates VPN configurations based on various criteria."""

    def __init__(self):
        """Initialize deduplicator."""
        self.duplicate_strategies = {
            "exact": self._deduplicate_exact,
            "server_port": self._deduplicate_server_port,
            "server_protocol": self._deduplicate_server_protocol,
            "content_hash": self._deduplicate_content_hash
        }

    def deduplicate_configurations(
        self, 
        configs: List[VPNConfiguration],
        strategy: str = "exact"
    ) -> List[VPNConfiguration]:
        """Deduplicate configurations using specified strategy.
        
        Args:
            configs: List of configurations to deduplicate
            strategy: Deduplication strategy to use
            
        Returns:
            List of unique configurations
        """
        if strategy not in self.duplicate_strategies:
            logger.warning(f"Unknown deduplication strategy: {strategy}")
            strategy = "exact"

        deduplicator_func = self.duplicate_strategies[strategy]
        unique_configs = deduplicator_func(configs)
        
        logger.info(f"Deduplicated {len(configs)} configurations to {len(unique_configs)} using {strategy} strategy")
        return unique_configs

    def _deduplicate_exact(self, configs: List[VPNConfiguration]) -> List[VPNConfiguration]:
        """Deduplicate by exact match of all fields.
        
        Args:
            configs: List of configurations
            
        Returns:
            List of unique configurations
        """
        seen = set()
        unique_configs = []
        
        for config in configs:
            config_key = self._get_exact_key(config)
            if config_key not in seen:
                seen.add(config_key)
                unique_configs.append(config)
                
        return unique_configs

    def _deduplicate_server_port(self, configs: List[VPNConfiguration]) -> List[VPNConfiguration]:
        """Deduplicate by server and port combination.
        
        Args:
            configs: List of configurations
            
        Returns:
            List of unique configurations
        """
        seen = set()
        unique_configs = []
        
        for config in configs:
            key = (config.server, config.port)
            if key not in seen:
                seen.add(key)
                unique_configs.append(config)
                
        return unique_configs

    def _deduplicate_server_protocol(self, configs: List[VPNConfiguration]) -> List[VPNConfiguration]:
        """Deduplicate by server and protocol combination.
        
        Args:
            configs: List of configurations
            
        Returns:
            List of unique configurations
        """
        seen = set()
        unique_configs = []
        
        for config in configs:
            key = (config.server, config.protocol.value)
            if key not in seen:
                seen.add(key)
                unique_configs.append(config)
                
        return unique_configs

    def _deduplicate_content_hash(self, configs: List[VPNConfiguration]) -> List[VPNConfiguration]:
        """Deduplicate by content hash.
        
        Args:
            configs: List of configurations
            
        Returns:
            List of unique configurations
        """
        seen = set()
        unique_configs = []
        
        for config in configs:
            content_hash = self._get_content_hash(config)
            if content_hash not in seen:
                seen.add(content_hash)
                unique_configs.append(config)
                
        return unique_configs

    def _get_exact_key(self, config: VPNConfiguration) -> Tuple:
        """Get exact match key for configuration.
        
        Args:
            config: Configuration to get key for
            
        Returns:
            Tuple representing the configuration
        """
        return (
            config.protocol.value,
            config.server,
            config.port,
            config.user_id,
            config.password,
            config.encryption,
            config.network,
            config.path,
            config.host,
            config.tls
        )

    def _get_content_hash(self, config: VPNConfiguration) -> str:
        """Get content hash for configuration.
        
        Args:
            config: Configuration to hash
            
        Returns:
            Hash string
        """
        content = f"{config.protocol.value}:{config.server}:{config.port}:{config.user_id}:{config.password}"
        return hashlib.md5(content.encode()).hexdigest()

    def find_duplicates(
        self, 
        configs: List[VPNConfiguration],
        strategy: str = "exact"
    ) -> Dict[str, List[VPNConfiguration]]:
        """Find duplicate configurations.
        
        Args:
            configs: List of configurations to check
            strategy: Deduplication strategy to use
            
        Returns:
            Dictionary mapping duplicate keys to lists of configurations
        """
        if strategy not in self.duplicate_strategies:
            logger.warning(f"Unknown deduplication strategy: {strategy}")
            return {}

        groups = defaultdict(list)
        
        for config in configs:
            if strategy == "exact":
                key = str(self._get_exact_key(config))
            elif strategy == "server_port":
                key = f"{config.server}:{config.port}"
            elif strategy == "server_protocol":
                key = f"{config.server}:{config.protocol.value}"
            elif strategy == "content_hash":
                key = self._get_content_hash(config)
            else:
                key = str(self._get_exact_key(config))
                
            groups[key].append(config)
            
        # Return only groups with duplicates
        return {k: v for k, v in groups.items() if len(v) > 1}

    def get_deduplication_stats(self, configs: List[VPNConfiguration]) -> Dict[str, Any]:
        """Get deduplication statistics.
        
        Args:
            configs: List of configurations to analyze
            
        Returns:
            Statistics dictionary
        """
        stats = {
            "total_configs": len(configs),
            "strategies": {}
        }
        
        for strategy in self.duplicate_strategies.keys():
            unique_configs = self.deduplicate_configurations(configs, strategy)
            duplicates = self.find_duplicates(configs, strategy)
            
            stats["strategies"][strategy] = {
                "unique_count": len(unique_configs),
                "duplicate_groups": len(duplicates),
                "duplicate_count": sum(len(group) - 1 for group in duplicates.values())
            }
            
        return stats
