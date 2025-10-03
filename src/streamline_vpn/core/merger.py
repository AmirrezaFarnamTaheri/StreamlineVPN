# File: src/streamline_vpn/core/merger.py

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import aiohttp

from ..models.configuration import VPNConfiguration
from .source_manager import SourceManager
from .config_processor import ConfigurationProcessor
from .output_manager import OutputManager
from .caching import VPNCacheService
from .merger_processor import MergerProcessor
from ..security.manager import SecurityManager
from ..fetcher.service import FetcherService
from ..utils.logging import get_logger
from ..utils.helpers import load_config_file

logger = get_logger(__name__)


class StreamlineVPNMerger:
    """
    Main orchestrator for VPN configuration aggregation, processing, and output generation.
    """

    def __init__(
        self,
        config_path: str = "config/sources.yaml",
        session: Optional[aiohttp.ClientSession] = None,
        **kwargs,
    ):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.initialized = False
        self.session = session

        # Core components
        self.source_manager: Optional[SourceManager] = None
        self.config_processor: Optional[ConfigurationProcessor] = None
        self.output_manager: Optional[OutputManager] = None
        self.cache_service: Optional[VPNCacheService] = None
        self.security_manager: Optional[SecurityManager] = None
        self.fetcher_service: Optional[FetcherService] = None
        self.merger_processor: Optional[MergerProcessor] = None

        # Configuration
        self.max_concurrent = kwargs.get("max_concurrent", 50)

        # State tracking
        self.last_run_time: Optional[datetime] = None
        self.last_run_results: Dict[str, Any] = {}
        self.statistics: Dict[str, Any] = {}
        self.configurations: List[VPNConfiguration] = []
        self.is_processing: bool = False

        logger.info(f"StreamlineVPN Merger initialized with config: {config_path}")

    async def initialize(self) -> None:
        """Initialize all components and load configuration."""
        if self.initialized:
            return
        logger.info("🔧 Initializing StreamlineVPN Merger components...")
        await self._load_configuration()
        await self._initialize_components()
        await self._validate_setup()
        self.initialized = True
        logger.info("✅ StreamlineVPN Merger initialization complete")

    async def _load_configuration(self) -> None:
        """Load and validate configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        self.config = await load_config_file(self.config_path)
        if "sources" not in self.config:
            self.config["sources"] = {}
        processing_config = self.config.get("processing", {})
        self.max_concurrent = processing_config.get("max_concurrent", self.max_concurrent)
        logger.info(f"Configuration loaded: {len(self.config.get('sources', {}))} source tiers")

    async def _initialize_components(self) -> None:
        """Initialize all core components."""
        from ..settings import get_settings
        if self.session is None:
            raise RuntimeError("Aiohttp session must be provided during merger creation.")
        settings = get_settings()
        self.cache_service = VPNCacheService(redis_nodes=settings.redis.nodes)
        self.security_manager = SecurityManager()
        self.fetcher_service = FetcherService(session=self.session, max_concurrent=self.max_concurrent)
        self.source_manager = SourceManager(
            config_path=self.config_path,
            security_manager=self.security_manager,
            fetcher_service=self.fetcher_service,
        )
        self.config_processor = ConfigurationProcessor()
        self.output_manager = OutputManager()
        self.merger_processor = MergerProcessor(merger=self)
        logger.info("All core components initialized successfully")

    async def _validate_setup(self) -> None:
        """Validate that all components are properly initialized."""
        for name, component in [
            ("source_manager", self.source_manager),
            ("config_processor", self.config_processor),
            ("output_manager", self.output_manager),
            ("cache_service", self.cache_service),
            ("security_manager", self.security_manager),
            ("merger_processor", self.merger_processor),
        ]:
            if component is None:
                raise ValueError(f"Required component not initialized: {name}")
        logger.debug("All required components validated")

    async def process_all(
        self,
        output_dir: str = "output",
        formats: Optional[List[str]] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Process all configured sources and generate outputs."""
        if not self.initialized:
            await self.initialize()

        start_time = datetime.now()
        logger.info("🚀 Starting complete VPN configuration processing pipeline")

        try:
            source_results, all_configs = await self._fetch_and_parse_sources(force_refresh)

            validated_configs = await self._apply_security_validation(all_configs)

            unique_configs = await self.merger_processor.deduplicate_configurations(validated_configs)

            enhanced_configs = await self.merger_processor.apply_enhancements(unique_configs)
            self.configurations = enhanced_configs

            await self._generate_outputs(enhanced_configs, output_dir, formats)

            return self._finalize_and_report_results(start_time, source_results, len(unique_configs))

        except Exception as e:
            logger.error(f"Processing pipeline failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds(),
            }

    async def _fetch_and_parse_sources(self, force_refresh: bool) -> tuple[Dict[str, Any], List[VPNConfiguration]]:
        """Fetch, parse, and perform initial validation of all sources."""
        logger.info("📡 Step 1: Processing all configured sources...")
        source_results = await self.source_manager.fetch_all_sources(force_refresh=force_refresh)
        all_configs = source_results.get("configurations", [])
        if not all_configs:
            logger.warning("No configurations retrieved from sources")
        return source_results, all_configs

    async def _apply_security_validation(self, configs: List[VPNConfiguration]) -> List[VPNConfiguration]:
        """Apply security validation to all configurations."""
        logger.info("🔒 Step 2: Applying security validation...")
        if not self.security_manager:
            logger.warning("Security manager not available, skipping security validation")
            return configs

        validated_configs = [
            config for config in configs
            if self.security_manager.analyze_configuration(str(config)).get("is_safe")
        ]
        rejections = len(configs) - len(validated_configs)
        logger.info(f"Security validation complete: {len(validated_configs)} approved, {rejections} rejected")
        return validated_configs

    async def _generate_outputs(
        self, configs: List[VPNConfiguration], output_dir: str, formats: Optional[List[str]]
    ) -> None:
        """Generate output files in specified formats."""
        logger.info("📄 Step 3: Generating output files...")
        if not self.output_manager:
            raise ValueError("Output manager not initialized")

        output_formats = formats or self.config.get("output", {}).get("formats", ["json", "clash"])
        await self.output_manager.save_configurations(configs, output_dir, output_formats)

    def _finalize_and_report_results(
        self, start_time: datetime, source_results: Dict[str, Any], final_config_count: int
    ) -> Dict[str, Any]:
        """Finalize statistics and return the results dictionary."""
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        results = {
            "success": True,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "processing_time": processing_time,
            "total_sources": source_results.get("total_sources", 0),
            "successful_sources": source_results.get("successful_sources", 0),
            "total_configurations": final_config_count,
            "configurations_per_second": final_config_count / max(processing_time, 1),
        }

        self.last_run_time = end_time
        self.last_run_results = results
        self._update_statistics(results)

        logger.info(f"✅ Processing completed in {processing_time:.2f}s: {results['total_configurations']} configs")
        return results

    def _update_statistics(self, results: Dict[str, Any]) -> None:
        """Update internal statistics based on processing results."""
        self.statistics.update({
            "last_updated": datetime.now().isoformat(),
            "total_sources": results.get("total_sources", 0),
            "total_configurations": results.get("total_configurations", 0),
            "average_processing_time": results.get("processing_time", 0.0),
        })
        if self.cache_service:
            self.statistics.update(self.cache_service.get_statistics())

    async def get_statistics(self) -> Dict[str, Any]:
        """Get current merger statistics."""
        stats = self.statistics.copy()
        if self.source_manager:
            stats.update(self.source_manager.get_source_statistics())
        return stats

    def get_configurations(self) -> List[VPNConfiguration]:
        """Get the last processed configurations."""
        return self.configurations

    async def shutdown(self) -> None:
        """Gracefully shutdown all components."""
        logger.info("🔄 Shutting down StreamlineVPN Merger...")
        for component in [
            self.output_manager, self.config_processor, self.source_manager,
            self.security_manager, self.fetcher_service, self.cache_service
        ]:
            if component and hasattr(component, "shutdown"):
                try:
                    await component.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down {component.__class__.__name__}: {e}")
        self.initialized = False
        logger.info("✅ StreamlineVPN Merger shutdown complete")