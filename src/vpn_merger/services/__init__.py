"""
Services Module
===============

Service layer implementations for VPN merger functionality.
"""

from .base_service import (
    BaseService,
    ServiceManager,
    ServiceRegistry,
    get_service_manager,
    get_service_registry,
    reset_service_manager,
    reset_service_registry
)
from .fetcher_service import AsyncSourceFetcher
from .vpn_merger_service import VPNMergerService

__all__ = [
    # Base Service Infrastructure
    "BaseService",
    "ServiceManager",
    "ServiceRegistry",
    "get_service_manager",
    "get_service_registry",
    "reset_service_manager",
    "reset_service_registry",
    
    # Service Implementations
    "AsyncSourceFetcher",
    "VPNMergerService",
]