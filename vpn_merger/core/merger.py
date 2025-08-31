"""
VPN Subscription Merger
======================

Main orchestration class for VPN subscription merging and processing.
"""

import asyncio
import base64
import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

from ..models.configuration import VPNConfiguration
from .source_manager import SourceManager
from .config_processor import ConfigurationProcessor
from .health_checker import SourceHealthChecker

logger = logging.getLogger(__name__)

# Global configuration constants
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_CONCURRENT_LIMIT = 50
DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1MB chunks for efficient processing


class VPNSubscriptionMerger:
    """Main VPN subscription merger class with comprehensive processing capabilities.
    
    This class orchestrates the entire VPN subscription merging process,
    including source management, configuration processing, and output generation.
    
    Attributes:
        source_manager: Manages VPN subscription sources
        config_processor: Processes and validates configurations
        results: List of processed VPN configurations
        stats: Processing statistics and metrics
        source_processing_times: Timing information for each source
        error_counts: Error tracking for each source
    """
    
    def __init__(self, config_path: Union[str, Path] = "config/sources.unified.yaml"):
        """Initialize the VPN subscription merger.
        
        Args:
            config_path: Path to the configuration file
        """
        self.source_manager = SourceManager(config_path)
        self.config_processor = ConfigurationProcessor()
        self.results: List[VPNConfiguration] = []
        self.stats = {
            'total_sources': 0,
            'processed_sources': 0,
            'total_configs': 0,
            'valid_configs': 0,
            'duplicate_configs': 0,
            'start_time': None,
            'end_time': None
        }
        self.source_processing_times: Dict[str, float] = {}
        self.error_counts: Dict[str, int] = {}
    
    async def run_comprehensive_merge(self, max_concurrent: int = DEFAULT_CONCURRENT_LIMIT) -> List[VPNConfiguration]:
        """Run comprehensive merge operation with concurrency control.
        
        Args:
            max_concurrent: Maximum number of concurrent source processing tasks
            
        Returns:
            List of processed VPN configurations
            
        Raises:
            ValueError: If max_concurrent is invalid
        """
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be positive")
        
        self.stats['start_time'] = datetime.now()
        self.stats['total_sources'] = len(self.source_manager.get_all_sources())
        
        logger.info(f"Starting comprehensive merge with {self.stats['total_sources']} sources")
        
        # Get prioritized sources
        sources = self.source_manager.get_prioritized_sources()
        
        # Process sources with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_source(source_url: str):
            async with semaphore:
                return await self._process_single_source(source_url)
        
        # Create tasks for all sources
        tasks = [process_source(source) for source in sources]
        
        # Process with progress bar if available
        if tqdm:
            with tqdm(total=len(tasks), desc="Processing sources") as pbar:
                for coro in asyncio.as_completed(tasks):
                    try:
                        await coro
                        pbar.update(1)
                    except Exception as e:
                        logger.error(f"Error processing source: {e}")
                        pbar.update(1)
        else:
            # Fallback without progress bar
            for coro in asyncio.as_completed(tasks):
                try:
                    await coro
                except Exception as e:
                    logger.error(f"Error processing source: {e}")
        
        # Sort results by quality score
        self.results.sort(key=lambda x: x.quality_score, reverse=True)
        
        self.stats['end_time'] = datetime.now()
        self.stats['valid_configs'] = len(self.results)
        
        logger.info(f"Merge completed: {self.stats['valid_configs']} valid configs from {self.stats['processed_sources']} sources")
        
        return self.results
    
    async def _process_single_source(self, source_url: str) -> None:
        """Process a single source URL with error handling.
        
        Args:
            source_url: Source URL to process
        """
        start_time = datetime.now()
        
        try:
            self.stats['processed_sources'] += 1
            
            # Validate source
            async with SourceHealthChecker() as validator:
                validation_result = await validator.validate_source(source_url)
                
                if not validation_result.get('accessible', False):
                    logger.debug(f"Source not accessible: {source_url}")
                    return

            # Fetch and process content
            configs = await self._fetch_source_content(source_url)
            
            for config in configs:
                result = self.config_processor.process_config(config, source_url)
                if result:
                    self.results.append(result)
                    self.stats['total_configs'] += 1
                else:
                    self.stats['duplicate_configs'] += 1
                    
        except Exception as e:
            logger.error(f"Error processing source {source_url}: {e}")
            self.error_counts[source_url] = self.error_counts.get(source_url, 0) + 1
        finally:
            # Record processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            self.source_processing_times[source_url] = processing_time
    
    async def _fetch_source_content(self, source_url: str) -> List[str]:
        """Fetch content from source URL with error handling.
        
        Args:
            source_url: Source URL to fetch from
            
        Returns:
            List of configuration strings
        """
        try:
            import aiohttp
        except ImportError:
            logger.warning("aiohttp not available, skipping fetch")
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source_url, timeout=DEFAULT_TIMEOUT) as response:
                    if response.status == 200:
                        content = await response.text()
                        return [line.strip() for line in content.split('\n') if line.strip()]
                    else:
                        logger.warning(f"Failed to fetch {source_url}: HTTP {response.status}")
                        return []
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {source_url}")
            return []
        except Exception as e:
            logger.error(f"Error fetching {source_url}: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Union[int, float, str, Dict]]:
        """Get comprehensive processing statistics.
        
        Returns:
            Dictionary containing processing statistics
        """
        return {
            **self.stats,
            'source_processing_times': self.source_processing_times,
            'error_counts': self.error_counts,
            'success_rate': (
                self.stats['processed_sources'] / self.stats['total_sources']
            ) if self.stats['total_sources'] > 0 else 0.0,
            'processing_duration': (
                (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            ) if self.stats['start_time'] and self.stats['end_time'] else None
        }
    
    def save_results(self, results: List[VPNConfiguration], output_dir: Union[str, Path] = "output") -> Dict[str, str]:
        """Save results to various output formats with enhanced error handling.
        
        Args:
            results: List of VPN configurations to save
            output_dir: Directory to save output files
            
        Returns:
            Dictionary mapping output types to file paths
            
        Raises:
            ValueError: If results list is empty
        """
        if not results:
            raise ValueError("Cannot save empty results list")
        
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Sort results by quality score for better output
            sorted_results = sorted(results, key=lambda x: x.quality_score, reverse=True)
            
            output_files = {}
            
            # Save raw configs
            raw_path = output_dir / "vpn_subscription_raw.txt"
            self._save_raw_configs(sorted_results, raw_path)
            output_files['raw'] = str(raw_path)
            
            # Save base64 encoded
            base64_path = output_dir / "vpn_subscription_base64.txt"
            self._save_base64_configs(sorted_results, base64_path)
            output_files['base64'] = str(base64_path)
            
            # Save CSV with metrics
            csv_path = output_dir / "vpn_detailed.csv"
            self._save_csv_report(sorted_results, csv_path)
            output_files['csv'] = str(csv_path)
            
            # Save JSON report with enhanced metadata
            json_path = output_dir / "vpn_report.json"
            self._save_json_report(sorted_results, json_path)
            output_files['json'] = str(json_path)
            
            # Save sing-box format
            singbox_path = output_dir / "vpn_singbox.json"
            self._save_singbox_format(sorted_results, singbox_path)
            output_files['singbox'] = str(singbox_path)
            
            logger.info(f"Results saved to {output_dir}/")
            logger.info(f"Total configurations saved: {len(sorted_results)}")
            
            return output_files
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return {}
    
    def _save_raw_configs(self, results: List[VPNConfiguration], output_path: Path) -> None:
        """Save raw configuration strings.
        
        Args:
            results: List of VPN configurations
            output_path: Path to save the raw configs
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(f"{result.config}\n")
    
    def _save_base64_configs(self, results: List[VPNConfiguration], output_path: Path) -> None:
        """Save base64 encoded configurations.
        
        Args:
            results: List of VPN configurations
            output_path: Path to save the base64 configs
        """
        configs_text = '\n'.join(result.config for result in results)
        encoded = base64.b64encode(configs_text.encode('utf-8')).decode('utf-8')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(encoded)
    
    def _save_csv_report(self, results: List[VPNConfiguration], output_path: Path) -> None:
        """Save CSV report with detailed metrics.
        
        Args:
            results: List of VPN configurations
            output_path: Path to save the CSV report
        """
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['config', 'protocol', 'host', 'port', 'quality_score', 'source_url', 'last_tested']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                row = result.to_dict()
                # Convert datetime to string for CSV
                if row.get('last_tested'):
                    row['last_tested'] = row['last_tested'].isoformat()
                writer.writerow(row)
    
    def _save_json_report(self, results: List[VPNConfiguration], output_path: Path) -> None:
        """Save JSON report with enhanced metadata.
        
        Args:
            results: List of VPN configurations
            output_path: Path to save the JSON report
        """
        report = {
            'summary': self.get_statistics(),
            'results': [result.to_dict() for result in results],
            'generated_at': datetime.now().isoformat(),
            'version': '2.0',
            'total_configs': len(results),
            'protocol_distribution': self._get_protocol_distribution(results),
            'quality_distribution': self._get_quality_distribution(results)
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    def _get_protocol_distribution(self, results: List[VPNConfiguration]) -> Dict[str, int]:
        """Get distribution of protocols in results.
        
        Args:
            results: List of VPN configurations
            
        Returns:
            Dictionary mapping protocol names to counts
        """
        return self.config_processor.get_protocol_distribution(results)
    
    def _get_quality_distribution(self, results: List[VPNConfiguration]) -> Dict[str, int]:
        """Get distribution of quality scores in results.
        
        Args:
            results: List of VPN configurations
            
        Returns:
            Dictionary mapping quality categories to counts
        """
        return self.config_processor.get_quality_distribution(results)
    
    def _save_singbox_format(self, results: List[VPNConfiguration], output_path: Path) -> None:
        """Save results in sing-box format.
        
        Args:
            results: List of VPN configurations
            output_path: Path to save the sing-box configuration
        """
        try:
            singbox_config = {
                "log": {
                    "level": "info",
                    "timestamp": True
                },
                "inbounds": [],
                "outbounds": []
            }
            
            # Convert configs to sing-box format
            for i, result in enumerate(results):
                if result.protocol in ['vmess', 'vless', 'trojan']:
                    outbound = self._convert_to_singbox_outbound(result, i)
                    if outbound:
                        singbox_config["outbounds"].append(outbound)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(singbox_config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving sing-box format: {e}")
    
    def _convert_to_singbox_outbound(self, result: VPNConfiguration, index: int) -> Optional[Dict[str, Union[str, int]]]:
        """Convert a config result to sing-box outbound format.
        
        Args:
            result: VPN configuration to convert
            index: Index for generating unique tags
            
        Returns:
            Dictionary containing sing-box outbound configuration or None if conversion fails
        """
        try:
            # Extract configuration details from the config string
            config_parts = self._parse_config_string(result.config)
            
            outbound = {
                "type": result.protocol,
                "tag": f"outbound-{index}",
                "server": config_parts.get('host') or result.host or "unknown",
                "port": config_parts.get('port') or result.port or 443
            }
            
            # Add protocol-specific settings
            if result.protocol == 'vmess':
                outbound.update({
                    "uuid": config_parts.get('uuid') or "00000000-0000-0000-0000-000000000000",
                    "security": config_parts.get('security', 'auto')
                })
            elif result.protocol == 'vless':
                outbound.update({
                    "uuid": config_parts.get('uuid') or "00000000-0000-0000-0000-000000000000",
                    "security": config_parts.get('security', 'tls')
                })
            elif result.protocol == 'trojan':
                outbound.update({
                    "password": config_parts.get('password') or "default_password"
                })
            
            return outbound
            
        except Exception as e:
            logger.debug(f"Error converting config to sing-box format: {e}")
            return None
    
    def _parse_config_string(self, config: str) -> Dict[str, Union[str, int]]:
        """Parse configuration string to extract components.
        
        Args:
            config: Configuration string to parse
            
        Returns:
            Dictionary containing parsed configuration components
        """
        try:
            parts = {}
            
            # Basic parsing for common patterns
            if '://' in config:
                protocol_part, rest = config.split('://', 1)
                
                # Extract host and port
                if '@' in rest:
                    auth_part, server_part = rest.split('@', 1)
                    if ':' in server_part:
                        host_part, port_part = server_part.split(':', 1)
                        parts['host'] = host_part
                        try:
                            parts['port'] = int(port_part.split('?')[0].split('#')[0])
                        except ValueError:
                            parts['port'] = 443
                    
                    # Extract UUID/password from auth part
                    if ':' in auth_part:
                        parts['uuid'] = auth_part.split(':')[0]
                    else:
                        parts['uuid'] = auth_part
                
                # Extract additional parameters
                if '?' in rest:
                    params_part = rest.split('?')[1].split('#')[0]
                    for param in params_part.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            parts[key] = value
            
            return parts
            
        except Exception as e:
            logger.debug(f"Error parsing config string: {e}")
            return {}
    
    def get_processing_summary(self) -> Dict[str, Union[int, float, str]]:
        """Get a human-readable processing summary.
        
        Returns:
            Dictionary containing processing summary information
        """
        stats = self.get_statistics()
        
        return {
            'total_sources': stats['total_sources'],
            'processed_sources': stats['processed_sources'],
            'valid_configs': stats['valid_configs'],
            'duplicate_configs': stats['duplicate_configs'],
            'success_rate': f"{stats['success_rate']:.1%}",
            'processing_duration': f"{stats['processing_duration']:.1f}s" if stats['processing_duration'] else 'N/A',
            'protocol_distribution': self._get_protocol_distribution(self.results),
            'quality_distribution': self._get_quality_distribution(self.results)
        }
