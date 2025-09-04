#!/usr/bin/env python3
"""
Strategy Pattern Implementation
===============================

Implements various strategy patterns for VPN configuration processing,
validation, and optimization.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ..models.configuration import VPNConfiguration

logger = logging.getLogger(__name__)


@runtime_checkable
class ProcessingStrategy(Protocol):
    """Protocol for processing strategies."""
    
    async def process(self, configs: List[VPNConfiguration]) -> List[VPNConfiguration]:
        """Process configurations using this strategy."""
        ...


@runtime_checkable
class ValidationStrategy(Protocol):
    """Protocol for validation strategies."""
    
    async def validate(self, config: VPNConfiguration) -> bool:
        """Validate a configuration using this strategy."""
        ...


@runtime_checkable
class OptimizationStrategy(Protocol):
    """Protocol for optimization strategies."""
    
    async def optimize(self, configs: List[VPNConfiguration], criteria: Dict[str, Any]) -> List[VPNConfiguration]:
        """Optimize configurations using this strategy."""
        ...


class BaseProcessingStrategy(ABC):
    """Base class for processing strategies."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the processing strategy.
        
        Args:
            name: Strategy name
            config: Strategy configuration
        """
        self.name = name
        self.config = config or {}
        self._metrics: Dict[str, Any] = {}
        
    @abstractmethod
    async def process(self, configs: List[VPNConfiguration]) -> List[VPNConfiguration]:
        """Process configurations using this strategy.
        
        Args:
            configs: List of configurations to process
            
        Returns:
            Processed configurations
        """
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get strategy metrics."""
        return self._metrics.copy()
    
    def update_metric(self, key: str, value: Any) -> None:
        """Update a metric.
        
        Args:
            key: Metric key
            value: Metric value
        """
        self._metrics[key] = value


class QualityBasedProcessingStrategy(BaseProcessingStrategy):
    """Processing strategy based on quality scores."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize quality-based processing strategy."""
        super().__init__("quality_based", config)
        self.min_quality = self.config.get("min_quality", 0.5)
        self.max_configs = self.config.get("max_configs", 1000)
        
    async def process(self, configs: List[VPNConfiguration]) -> List[VPNConfiguration]:
        """Process configurations based on quality scores.
        
        Args:
            configs: List of configurations to process
            
        Returns:
            Processed configurations sorted by quality
        """
        logger.debug(f"Processing {len(configs)} configs with quality-based strategy")
        
        # Filter by minimum quality
        filtered_configs = [
            config for config in configs 
            if config.quality_score >= self.min_quality
        ]
        
        # Sort by quality score (descending)
        filtered_configs.sort(key=lambda x: x.quality_score, reverse=True)
        
        # Limit number of configs
        if len(filtered_configs) > self.max_configs:
            filtered_configs = filtered_configs[:self.max_configs]
        
        # Update metrics
        self.update_metric("processed_count", len(filtered_configs))
        self.update_metric("filtered_out_count", len(configs) - len(filtered_configs))
        self.update_metric("avg_quality", 
                         sum(c.quality_score for c in filtered_configs) / len(filtered_configs) 
                         if filtered_configs else 0)
        
        logger.debug(f"Quality-based processing: {len(filtered_configs)} configs selected")
        return filtered_configs


class GeographicProcessingStrategy(BaseProcessingStrategy):
    """Processing strategy based on geographic distribution."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize geographic processing strategy."""
        super().__init__("geographic", config)
        self.target_countries = self.config.get("target_countries", [])
        self.max_per_country = self.config.get("max_per_country", 10)
        
    async def process(self, configs: List[VPNConfiguration]) -> List[VPNConfiguration]:
        """Process configurations based on geographic distribution.
        
        Args:
            configs: List of configurations to process
            
        Returns:
            Processed configurations with geographic diversity
        """
        logger.debug(f"Processing {len(configs)} configs with geographic strategy")
        
        if not self.target_countries:
            # If no target countries specified, return all configs
            return configs
        
        # Group configs by country
        country_groups: Dict[str, List[VPNConfiguration]] = {}
        for config in configs:
            country = getattr(config, 'country', 'Unknown')
            if country not in country_groups:
                country_groups[country] = []
            country_groups[country].append(config)
        
        # Select configs from target countries
        selected_configs = []
        for country in self.target_countries:
            if country in country_groups:
                country_configs = country_groups[country]
                # Sort by quality and take top configs
                country_configs.sort(key=lambda x: x.quality_score, reverse=True)
                selected_configs.extend(country_configs[:self.max_per_country])
        
        # Update metrics
        self.update_metric("processed_count", len(selected_configs))
        self.update_metric("countries_represented", len(set(getattr(c, 'country', 'Unknown') for c in selected_configs)))
        
        logger.debug(f"Geographic processing: {len(selected_configs)} configs selected from {len(self.target_countries)} countries")
        return selected_configs


class PerformanceProcessingStrategy(BaseProcessingStrategy):
    """Processing strategy based on performance metrics."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize performance processing strategy."""
        super().__init__("performance", config)
        self.min_speed = self.config.get("min_speed", 10.0)  # Mbps
        self.max_latency = self.config.get("max_latency", 200.0)  # ms
        
    async def process(self, configs: List[VPNConfiguration]) -> List[VPNConfiguration]:
        """Process configurations based on performance metrics.
        
        Args:
            configs: List of configurations to process
            
        Returns:
            Processed configurations meeting performance criteria
        """
        logger.debug(f"Processing {len(configs)} configs with performance strategy")
        
        # Filter by performance criteria
        filtered_configs = []
        for config in configs:
            speed = getattr(config, 'speed', 0.0)
            latency = getattr(config, 'latency', float('inf'))
            
            if speed >= self.min_speed and latency <= self.max_latency:
                filtered_configs.append(config)
        
        # Sort by performance score (speed/latency ratio)
        filtered_configs.sort(
            key=lambda x: getattr(x, 'speed', 0.0) / max(getattr(x, 'latency', 1.0), 1.0),
            reverse=True
        )
        
        # Update metrics
        self.update_metric("processed_count", len(filtered_configs))
        self.update_metric("filtered_out_count", len(configs) - len(filtered_configs))
        if filtered_configs:
            avg_speed = sum(getattr(c, 'speed', 0.0) for c in filtered_configs) / len(filtered_configs)
            avg_latency = sum(getattr(c, 'latency', 0.0) for c in filtered_configs) / len(filtered_configs)
            self.update_metric("avg_speed", avg_speed)
            self.update_metric("avg_latency", avg_latency)
        
        logger.debug(f"Performance processing: {len(filtered_configs)} configs selected")
        return filtered_configs


class BaseValidationStrategy(ABC):
    """Base class for validation strategies."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the validation strategy.
        
        Args:
            name: Strategy name
            config: Strategy configuration
        """
        self.name = name
        self.config = config or {}
        self._validation_count = 0
        self._validation_errors = 0
        
    @abstractmethod
    async def validate(self, config: VPNConfiguration) -> bool:
        """Validate a configuration using this strategy.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        pass
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            "total_validations": self._validation_count,
            "validation_errors": self._validation_errors,
            "success_rate": (self._validation_count - self._validation_errors) / max(self._validation_count, 1)
        }


class ProtocolValidationStrategy(BaseValidationStrategy):
    """Validation strategy based on protocol compliance."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize protocol validation strategy."""
        super().__init__("protocol", config)
        self.allowed_protocols = self.config.get("allowed_protocols", [
            "wireguard", "vless", "vmess", "shadowsocks", "trojan", "hysteria", "tuic"
        ])
        
    async def validate(self, config: VPNConfiguration) -> bool:
        """Validate configuration protocol compliance.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if protocol is valid
        """
        self._validation_count += 1
        
        try:
            protocol = getattr(config, 'protocol', '').lower()
            if protocol not in self.allowed_protocols:
                self._validation_errors += 1
                return False
            
            # Additional protocol-specific validation
            if protocol == "wireguard":
                return await self._validate_wireguard(config)
            elif protocol == "vless":
                return await self._validate_vless(config)
            elif protocol == "vmess":
                return await self._validate_vmess(config)
            # Add more protocol validations as needed
            
            return True
            
        except Exception as e:
            logger.error(f"Protocol validation error: {e}")
            self._validation_errors += 1
            return False
    
    async def _validate_wireguard(self, config: VPNConfiguration) -> bool:
        """Validate WireGuard configuration."""
        required_fields = ['public_key', 'endpoint', 'allowed_ips']
        return all(hasattr(config, field) for field in required_fields)
    
    async def _validate_vless(self, config: VPNConfiguration) -> bool:
        """Validate VLESS configuration."""
        required_fields = ['uuid', 'address', 'port']
        return all(hasattr(config, field) for field in required_fields)
    
    async def _validate_vmess(self, config: VPNConfiguration) -> bool:
        """Validate VMESS configuration."""
        required_fields = ['uuid', 'address', 'port']
        return all(hasattr(config, field) for field in required_fields)


class SecurityValidationStrategy(BaseValidationStrategy):
    """Validation strategy based on security criteria."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize security validation strategy."""
        super().__init__("security", config)
        self.check_encryption = self.config.get("check_encryption", True)
        self.check_authentication = self.config.get("check_authentication", True)
        self.min_key_length = self.config.get("min_key_length", 32)
        
    async def validate(self, config: VPNConfiguration) -> bool:
        """Validate configuration security.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is secure
        """
        self._validation_count += 1
        
        try:
            # Check encryption
            if self.check_encryption:
                if not await self._check_encryption(config):
                    self._validation_errors += 1
                    return False
            
            # Check authentication
            if self.check_authentication:
                if not await self._check_authentication(config):
                    self._validation_errors += 1
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            self._validation_errors += 1
            return False
    
    async def _check_encryption(self, config: VPNConfiguration) -> bool:
        """Check encryption strength."""
        # Implement encryption strength checks
        return True  # Placeholder
    
    async def _check_authentication(self, config: VPNConfiguration) -> bool:
        """Check authentication mechanisms."""
        # Implement authentication checks
        return True  # Placeholder


class StrategyManager:
    """Manages strategy selection and execution."""
    
    def __init__(self):
        """Initialize the strategy manager."""
        self._processing_strategies: Dict[str, BaseProcessingStrategy] = {}
        self._validation_strategies: Dict[str, BaseValidationStrategy] = {}
        self._default_processing_strategy = "quality_based"
        self._default_validation_strategy = "protocol"
        
    def register_processing_strategy(self, strategy: BaseProcessingStrategy) -> None:
        """Register a processing strategy.
        
        Args:
            strategy: Processing strategy to register
        """
        self._processing_strategies[strategy.name] = strategy
        logger.debug(f"Registered processing strategy: {strategy.name}")
    
    def register_validation_strategy(self, strategy: BaseValidationStrategy) -> None:
        """Register a validation strategy.
        
        Args:
            strategy: Validation strategy to register
        """
        self._validation_strategies[strategy.name] = strategy
        logger.debug(f"Registered validation strategy: {strategy.name}")
    
    async def process_configs(
        self, 
        configs: List[VPNConfiguration], 
        strategy_name: Optional[str] = None
    ) -> List[VPNConfiguration]:
        """Process configurations using specified strategy.
        
        Args:
            configs: Configurations to process
            strategy_name: Strategy name (uses default if None)
            
        Returns:
            Processed configurations
        """
        strategy_name = strategy_name or self._default_processing_strategy
        
        if strategy_name not in self._processing_strategies:
            raise ValueError(f"Unknown processing strategy: {strategy_name}")
        
        strategy = self._processing_strategies[strategy_name]
        return await strategy.process(configs)
    
    async def validate_config(
        self, 
        config: VPNConfiguration, 
        strategy_name: Optional[str] = None
    ) -> bool:
        """Validate configuration using specified strategy.
        
        Args:
            config: Configuration to validate
            strategy_name: Strategy name (uses default if None)
            
        Returns:
            True if configuration is valid
        """
        strategy_name = strategy_name or self._default_validation_strategy
        
        if strategy_name not in self._validation_strategies:
            raise ValueError(f"Unknown validation strategy: {strategy_name}")
        
        strategy = self._validation_strategies[strategy_name]
        return await strategy.validate(config)
    
    def set_default_processing_strategy(self, strategy_name: str) -> None:
        """Set the default processing strategy.
        
        Args:
            strategy_name: Strategy name
        """
        if strategy_name not in self._processing_strategies:
            raise ValueError(f"Unknown processing strategy: {strategy_name}")
        
        self._default_processing_strategy = strategy_name
        logger.debug(f"Set default processing strategy: {strategy_name}")
    
    def set_default_validation_strategy(self, strategy_name: str) -> None:
        """Set the default validation strategy.
        
        Args:
            strategy_name: Strategy name
        """
        if strategy_name not in self._validation_strategies:
            raise ValueError(f"Unknown validation strategy: {strategy_name}")
        
        self._default_validation_strategy = strategy_name
        logger.debug(f"Set default validation strategy: {strategy_name}")
    
    def get_available_strategies(self) -> Dict[str, List[str]]:
        """Get available strategies.
        
        Returns:
            Dictionary mapping strategy types to available strategy names
        """
        return {
            "processing": list(self._processing_strategies.keys()),
            "validation": list(self._validation_strategies.keys())
        }
    
    def get_strategy_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all strategies.
        
        Returns:
            Dictionary mapping strategy names to their metrics
        """
        metrics = {}
        
        for name, strategy in self._processing_strategies.items():
            metrics[f"processing_{name}"] = strategy.get_metrics()
        
        for name, strategy in self._validation_strategies.items():
            metrics[f"validation_{name}"] = strategy.get_validation_stats()
        
        return metrics


# Global strategy manager instance
_strategy_manager: Optional[StrategyManager] = None


def get_strategy_manager() -> StrategyManager:
    """Get the global strategy manager.
    
    Returns:
        Global StrategyManager instance
    """
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = StrategyManager()
        
        # Register default strategies
        _strategy_manager.register_processing_strategy(QualityBasedProcessingStrategy())
        _strategy_manager.register_processing_strategy(GeographicProcessingStrategy())
        _strategy_manager.register_processing_strategy(PerformanceProcessingStrategy())
        
        _strategy_manager.register_validation_strategy(ProtocolValidationStrategy())
        _strategy_manager.register_validation_strategy(SecurityValidationStrategy())
    
    return _strategy_manager


def reset_strategy_manager() -> None:
    """Reset the global strategy manager."""
    global _strategy_manager
    _strategy_manager = None
