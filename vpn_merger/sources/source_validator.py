import aiohttp
import asyncio
import hashlib
import re
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

@dataclass
class SourceHealth:
    """Source health status and metrics."""
    url: str
    accessible: bool = False
    response_time: Optional[float] = None
    content_type: Optional[str] = None
    size_bytes: int = 0
    estimated_configs: int = 0
    protocols_found: List[str] = field(default_factory=list)
    last_modified: Optional[datetime] = None
    reliability_score: float = 0.0
    error: Optional[str] = None
    last_check: datetime = field(default_factory=datetime.now)
    check_count: int = 0
    success_count: int = 0
    failure_count: int = 0

class SourceValidator:
    """Validates and monitors source health with comprehensive metrics."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.health_history: Dict[str, List[bool]] = {}
        self.last_check: Dict[str, datetime] = {}
        self.source_cache: Dict[str, SourceHealth] = {}
        self.blacklist: Set[str] = set()
        self.whitelist: Set[str] = set()
        self.config = self._load_config(config_path)
        
        # Protocol detection patterns
        self.protocol_patterns = {
            'vmess': r'vmess://[A-Za-z0-9+/=]+',
            'vless': r'vless://[A-Za-z0-9-]+@[^:]+:\d+',
            'trojan': r'trojan://[^@]+@[^:]+:\d+',
            'shadowsocks': r'ss://[A-Za-z0-9+/=]+',
            'shadowsocksr': r'ssr://[A-Za-z0-9+/=]+',
            'hysteria': r'hysteria://[^:]+:\d+',
            'hysteria2': r'hysteria2://[^:]+:\d+',
            'tuic': r'tuic://[^:]+:\d+'
        }
        
        # Content type validation
        self.valid_content_types = {
            'text/plain',
            'text/yaml',
            'application/yaml',
            'application/json',
            'text/html',  # Some sources serve as HTML
            'application/octet-stream'
        }
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load validation configuration."""
        if not config_path:
            config_path = "config/sources.production.yaml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config {config_path}: {e}")
            return {}
    
    async def validate_source(self, url: str, timeout: int = 30) -> SourceHealth:
        """Comprehensive source validation with detailed metrics."""
        health = SourceHealth(url=url)
        
        try:
            async with aiohttp.ClientSession() as session:
                start = datetime.now()
                
                # Set headers to mimic real browser
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/plain,text/yaml,application/yaml,application/json,*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    health.accessible = response.status == 200
                    health.response_time = (datetime.now() - start).total_seconds()
                    health.content_type = response.headers.get('Content-Type', '')
                    health.last_modified = self._parse_last_modified(response.headers.get('Last-Modified'))
                    
                    if health.accessible:
                        content = await response.text()
                        health.size_bytes = len(content.encode('utf-8'))
                        
                        # Analyze content quality
                        health.estimated_configs = self._estimate_configs(content)
                        health.protocols_found = self._detect_protocols(content)
                        
                        # Calculate reliability score
                        health.reliability_score = self._calculate_reliability(url, health)
                        
                        # Update history
                        self._update_health_history(url, True)
                        health.success_count += 1
                    else:
                        health.error = f"HTTP {response.status}"
                        self._update_health_history(url, False)
                        health.failure_count += 1
                        
        except asyncio.TimeoutError:
            health.error = "Timeout"
            health.response_time = timeout
            self._update_health_history(url, False)
            health.failure_count += 1
        except Exception as e:
            health.error = str(e)
            self._update_health_history(url, False)
            health.failure_count += 1
        
        health.check_count += 1
        health.last_check = datetime.now()
        
        # Cache the result
        self.source_cache[url] = health
        
        return health
    
    def _parse_last_modified(self, last_modified: Optional[str]) -> Optional[datetime]:
        """Parse Last-Modified header."""
        if not last_modified:
            return None
        
        try:
            # Common date formats
            formats = [
                '%a, %d %b %Y %H:%M:%S %Z',
                '%a, %d %b %Y %H:%M:%S %z',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S%z'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(last_modified, fmt)
                except ValueError:
                    continue
            
            # Try parsing with dateutil if available
            try:
                from dateutil import parser
                return parser.parse(last_modified)
            except ImportError:
                pass
                
        except Exception:
            pass
        
        return None
    
    def _estimate_configs(self, content: str) -> int:
        """Estimate number of configs in content."""
        lines = content.strip().split('\n')
        valid_prefixes = ('vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://', 'hysteria://', 'hysteria2://', 'tuic://')
        
        config_count = 0
        for line in lines:
            line = line.strip()
            if any(line.startswith(prefix) for prefix in valid_prefixes):
                config_count += 1
            elif line.startswith('-') and any(proto in line for proto in ['vmess', 'vless', 'trojan', 'shadowsocks']):
                config_count += 1
        
        return config_count
    
    def _detect_protocols(self, content: str) -> List[str]:
        """Detect which protocols are present in content."""
        protocols = set()
        
        for protocol, pattern in self.protocol_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                protocols.add(protocol)
        
        # Also check for YAML/JSON format indicators
        if 'proxies:' in content or 'proxy-groups:' in content:
            protocols.add('clash')
        
        return list(protocols)
    
    def _calculate_reliability(self, url: str, health: SourceHealth) -> float:
        """Calculate comprehensive source reliability score."""
        score = 0.0
        
        # Base accessibility score
        if health.accessible:
            score += 0.3
        
        # Response time factor (faster = better)
        if health.response_time:
            if health.response_time < 2:
                score += 0.2
            elif health.response_time < 5:
                score += 0.15
            elif health.response_time < 10:
                score += 0.1
            elif health.response_time < 30:
                score += 0.05
        
        # Content quality factors
        if health.estimated_configs > 100:
            score += 0.15
        if health.estimated_configs > 500:
            score += 0.1
        if health.estimated_configs > 1000:
            score += 0.05
        
        # Protocol diversity
        if len(health.protocols_found) >= 3:
            score += 0.1
        elif len(health.protocols_found) >= 2:
            score += 0.05
        
        # Content type validation
        if health.content_type and any(valid in health.content_type for valid in self.valid_content_types):
            score += 0.05
        
        # Historical reliability
        if url in self.health_history:
            recent = self.health_history[url][-10:]  # Last 10 checks
            if recent:
                success_rate = sum(recent) / len(recent)
                score += success_rate * 0.1
        
        # URL quality indicators
        if any(keyword in url.lower() for keyword in ['official', 'verified', 'trusted', 'main']):
            score += 0.05
        
        # Penalize suspicious patterns
        if any(pattern in url for pattern in ['temp', 'test', 'backup', 'old', 'dev']):
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _update_health_history(self, url: str, success: bool):
        """Update health check history."""
        if url not in self.health_history:
            self.health_history[url] = []
        
        self.health_history[url].append(success)
        
        # Keep only last 100 checks
        if len(self.health_history[url]) > 100:
            self.health_history[url] = self.health_history[url][-100:]
    
    async def validate_multiple_sources(self, urls: List[str], max_concurrent: int = 10) -> Dict[str, SourceHealth]:
        """Validate multiple sources concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def validate_with_semaphore(url: str) -> Tuple[str, SourceHealth]:
            async with semaphore:
                health = await self.validate_source(url)
                return url, health
        
        tasks = [validate_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        validated_sources = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Validation error: {result}")
                continue
            
            url, health = result
            validated_sources[url] = health
        
        return validated_sources
    
    def get_source_stats(self) -> Dict:
        """Get comprehensive source statistics."""
        total_sources = len(self.source_cache)
        if total_sources == 0:
            return {}
        
        accessible_sources = sum(1 for h in self.source_cache.values() if h.accessible)
        avg_response_time = sum(h.response_time or 0 for h in self.source_cache.values() if h.response_time) / total_sources
        avg_configs = sum(h.estimated_configs for h in self.source_cache.values()) / total_sources
        avg_reliability = sum(h.reliability_score for h in self.source_cache.values()) / total_sources
        
        protocol_distribution = {}
        for health in self.source_cache.values():
            for protocol in health.protocols_found:
                protocol_distribution[protocol] = protocol_distribution.get(protocol, 0) + 1
        
        return {
            'total_sources': total_sources,
            'accessible_sources': accessible_sources,
            'accessibility_rate': accessible_sources / total_sources,
            'average_response_time': avg_response_time,
            'average_configs_per_source': avg_configs,
            'average_reliability_score': avg_reliability,
            'protocol_distribution': protocol_distribution,
            'total_configs_estimated': sum(h.estimated_configs for h in self.source_cache.values()),
            'last_updated': datetime.now().isoformat()
        }
    
    def export_health_report(self, output_path: str = "source_health_report.yaml"):
        """Export comprehensive health report."""
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.get_source_stats(),
            'sources': {}
        }
        
        for url, health in self.source_cache.items():
            report['sources'][url] = {
                'accessible': health.accessible,
                'response_time': health.response_time,
                'estimated_configs': health.estimated_configs,
                'protocols_found': health.protocols_found,
                'reliability_score': health.reliability_score,
                'last_check': health.last_check.isoformat(),
                'check_count': health.check_count,
                'success_count': health.success_count,
                'failure_count': health.failure_count,
                'error': health.error
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(report, f, default_flow_style=False, indent=2)
        
        logger.info(f"Health report exported to {output_path}")
        return output_path
    
    def get_recommended_sources(self, min_reliability: float = 0.7, min_configs: int = 100) -> List[str]:
        """Get list of recommended sources based on criteria."""
        recommended = []
        
        for url, health in self.source_cache.items():
            if (health.reliability_score >= min_reliability and 
                health.estimated_configs >= min_configs and 
                health.accessible):
                recommended.append(url)
        
        # Sort by reliability score (descending)
        recommended.sort(key=lambda url: self.source_cache[url].reliability_score, reverse=True)
        return recommended
    
    def cleanup_old_records(self, max_age_days: int = 30):
        """Clean up old health records."""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        
        # Clean up old cache entries
        old_urls = [
            url for url, health in self.source_cache.items()
            if health.last_check < cutoff
        ]
        
        for url in old_urls:
            del self.source_cache[url]
        
        # Clean up old history
        for url in list(self.health_history.keys()):
            if url not in self.source_cache:
                del self.health_history[url]
        
        logger.info(f"Cleaned up {len(old_urls)} old source records")

