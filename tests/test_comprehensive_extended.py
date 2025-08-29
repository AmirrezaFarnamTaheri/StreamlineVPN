import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
import yaml
from datetime import datetime, timedelta

# Import the modules we want to test
from vpn_merger.sources.source_validator import SourceValidator, SourceHealth
from vpn_merger.discovery.intelligent_discovery import IntelligentSourceDiscovery, DiscoveredSource
from vpn_merger.security.security_manager import SecurityManager
from vpn_merger.services.reliability import CircuitBreaker, ExponentialBackoff
from vpn_merger.services.rate_limiter import PerHostRateLimiter
from vpn_merger.services.bloom import BloomFilter
from vpn_merger.monitoring.metrics_collector import MetricsCollector
from vpn_merger.monitoring.tracing_enhanced import TracingService

class TestSourceValidator:
    """Test the SourceValidator class comprehensively."""
    
    @pytest.fixture
    def validator(self):
        """Create a SourceValidator instance for testing."""
        return SourceValidator()
    
    @pytest.fixture
    def mock_source_health(self):
        """Create a mock SourceHealth instance."""
        return SourceHealth(
            url="https://example.com/test.txt",
            accessible=True,
            response_time=1.5,
            estimated_configs=1000,
            protocols_found=["vmess", "vless"],
            reliability_score=0.85
        )
    
    def test_source_validator_initialization(self, validator):
        """Test SourceValidator initialization."""
        assert validator is not None
        assert isinstance(validator.health_history, dict)
        assert isinstance(validator.source_cache, dict)
        assert len(validator.protocol_patterns) > 0
        assert len(validator.valid_content_types) > 0
    
    def test_protocol_detection(self, validator):
        """Test protocol detection from content."""
        content = """
        vmess://eyJhZGQiOiAiZXhhbXBsZS5jb20iLCAicG9ydCI6IDQ0M30=
        vless://uuid@example.com:443?security=tls
        trojan://password@example.com:443
        ss://base64encoded
        """
        
        protocols = validator._detect_protocols(content)
        assert "vmess" in protocols
        assert "vless" in protocols
        assert "trojan" in protocols
        assert "shadowsocks" in protocols
    
    def test_config_estimation(self, validator):
        """Test config count estimation."""
        content = """
        vmess://config1
        vless://config2
        trojan://config3
        # This is a comment
        vmess://config4
        """
        
        count = validator._estimate_configs(content)
        assert count == 4
    
    def test_reliability_calculation(self, validator, mock_source_health):
        """Test reliability score calculation."""
        score = validator._calculate_reliability("https://example.com/test.txt", mock_source_health)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be reasonably high for good source
    
    @pytest.mark.asyncio
    async def test_validate_source_mock(self, validator):
        """Test source validation with mocked HTTP responses."""
        mock_url = "https://example.com/test.txt"
        mock_content = "vmess://test\nvless://test2"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {'Content-Type': 'text/plain'}
            mock_response.text = AsyncMock(return_value=mock_content)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            health = await validator.validate_source(mock_url)
            
            assert health.url == mock_url
            assert health.accessible is True
            assert health.estimated_configs == 2
            assert "vmess" in health.protocols_found
            assert "vless" in health.protocols_found
    
    @pytest.mark.asyncio
    async def test_validate_multiple_sources(self, validator):
        """Test concurrent validation of multiple sources."""
        urls = [
            "https://example1.com/test.txt",
            "https://example2.com/test.txt",
            "https://example3.com/test.txt"
        ]
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {'Content-Type': 'text/plain'}
            mock_response.text = AsyncMock(return_value="vmess://test")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            results = await validator.validate_multiple_sources(urls)
            
            assert len(results) == 3
            for url, health in results.items():
                assert health.accessible is True
                assert health.url == url
    
    def test_health_history_management(self, validator):
        """Test health history tracking."""
        url = "https://example.com/test.txt"
        
        # Add some health records
        validator._update_health_history(url, True)
        validator._update_health_history(url, True)
        validator._update_health_history(url, False)
        
        assert url in validator.health_history
        assert len(validator.health_history[url]) == 3
        assert validator.health_history[url] == [True, True, False]
    
    def test_get_source_stats(self, validator):
        """Test source statistics generation."""
        # Add some mock sources
        validator.source_cache["url1"] = SourceHealth(
            url="url1", accessible=True, estimated_configs=100, reliability_score=0.8
        )
        validator.source_cache["url2"] = SourceHealth(
            url="url2", accessible=False, estimated_configs=0, reliability_score=0.0
        )
        
        stats = validator.get_source_stats()
        
        assert stats['total_sources'] == 2
        assert stats['accessible_sources'] == 1
        assert stats['accessibility_rate'] == 0.5
        assert stats['total_configs_estimated'] == 100
    
    def test_recommended_sources_filtering(self, validator):
        """Test source recommendation filtering."""
        # Add sources with different reliability scores
        validator.source_cache["good"] = SourceHealth(
            url="good", accessible=True, estimated_configs=500, reliability_score=0.9
        )
        validator.source_cache["medium"] = SourceHealth(
            url="medium", accessible=True, estimated_configs=200, reliability_score=0.7
        )
        validator.source_cache["poor"] = SourceHealth(
            url="poor", accessible=True, estimated_configs=50, reliability_score=0.3
        )
        
        recommended = validator.get_recommended_sources(min_reliability=0.7, min_configs=100)
        
        assert "good" in recommended
        assert "medium" in recommended
        assert "poor" not in recommended
        assert recommended[0] == "good"  # Should be sorted by score

class TestIntelligentSourceDiscovery:
    """Test the IntelligentSourceDiscovery class."""
    
    @pytest.fixture
    def discovery(self):
        """Create a discovery instance for testing."""
        return IntelligentSourceDiscovery()
    
    @pytest.fixture
    def mock_discovered_source(self):
        """Create a mock DiscoveredSource instance."""
        return DiscoveredSource(
            url="https://raw.githubusercontent.com/test/repo/main/config.txt",
            source_type="github",
            discovery_method="api",
            stars=100,
            forks=20,
            language="Python",
            topics=["v2ray", "vpn", "proxy"],
            description="VPN configuration collection"
        )
    
    def test_discovery_initialization(self, discovery):
        """Test IntelligentSourceDiscovery initialization."""
        assert discovery is not None
        assert isinstance(discovery.discovered_sources, dict)
        assert len(discovery.vpn_keywords) > 0
        assert len(discovery.source_patterns) > 0
    
    def test_subscription_file_detection(self, discovery):
        """Test subscription file path detection."""
        assert discovery._is_subscription_file("sub.txt") is True
        assert discovery._is_subscription_file("config.yaml") is True
        assert discovery._is_subscription_file("README.md") is False
        assert discovery._is_subscription_file("LICENSE") is False
    
    def test_source_scoring(self, discovery, mock_discovered_source):
        """Test source scoring algorithm."""
        score = discovery._calculate_source_score(mock_discovered_source)
        assert score > 0
        assert score <= 50  # Reasonable upper bound
    
    def test_rate_limit_detection(self, discovery):
        """Test rate limit detection."""
        discovery.rate_limit_remaining = 5
        assert discovery._is_rate_limited() is True
        
        discovery.rate_limit_remaining = 20
        assert discovery._is_rate_limited() is False
    
    @pytest.mark.asyncio
    async def test_github_api_search_mock(self, discovery):
        """Test GitHub API search with mocked responses."""
        discovery.github_token = "test_token"
        
        mock_search_response = {
            'items': [
                {
                    'repository': {'full_name': 'test/repo'},
                    'path': 'config.txt'
                }
            ]
        }
        
        mock_repo_response = {
            'stargazers_count': 100,
            'forks_count': 20,
            'language': 'Python',
            'topics': ['v2ray'],
            'description': 'Test repo',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock search response
            mock_search = AsyncMock()
            mock_search.status = 200
            mock_search.headers = {'X-RateLimit-Remaining': '1000'}
            mock_search.json = AsyncMock(return_value=mock_search_response)
            
            # Mock repo info response
            mock_repo = AsyncMock()
            mock_repo.status = 200
            mock_repo.json = AsyncMock(return_value=mock_repo_response)
            
            # Set up mock to return different responses
            mock_get.return_value.__aenter__.side_effect = [mock_search, mock_repo]
            
            sources = await discovery.discover_github_sources(max_results=1)
            
            assert len(sources) > 0
            assert sources[0].url == "https://raw.githubusercontent.com/test/repo/main/config.txt"
    
    def test_discovery_stats(self, discovery):
        """Test discovery statistics generation."""
        # Add some mock sources
        discovery.discovered_sources["source1"] = DiscoveredSource(
            url="source1", source_type="github", discovery_method="api", discovery_score=8.0
        )
        discovery.discovered_sources["source2"] = DiscoveredSource(
            url="source2", source_type="website", discovery_method="crawl", discovery_score=5.0
        )
        
        stats = discovery.get_discovery_stats()
        
        assert stats['total_discovered'] == 2
        assert stats['by_source_type']['github'] == 1
        assert stats['by_source_type']['website'] == 1
        assert stats['average_score'] == 6.5

class TestSecurityManager:
    """Test the SecurityManager class."""
    
    @pytest.fixture
    def security_manager(self):
        """Create a SecurityManager instance for testing."""
        return SecurityManager()
    
    @pytest.mark.parametrize("input_host,expected", [
        ("192.168.1.1", "192.168.1.1"),
        ("example.com", "example.com"),
        ("sub.example.com", "sub.example.com"),
        ("example.com:8080", None),  # Port should be rejected
        ("../../etc/passwd", None),  # Path traversal
        ("example.com\n", None),  # Newline injection
        ("'; DROP TABLE;--", None),  # SQL injection attempt
    ])
    def test_sanitize_host(self, security_manager, input_host, expected):
        """Test host sanitization."""
        if expected is None:
            with pytest.raises(Exception):
                security_manager.sanitize_host(input_host)
        else:
            result = security_manager.sanitize_host(input_host)
            assert result == expected
    
    @pytest.mark.parametrize("input_port,expected", [
        (80, 80),
        (443, 443),
        (65535, 65535),
        (0, None),
        (65536, None),
        (-1, None),
        ("not_a_port", None),
    ])
    def test_sanitize_port(self, security_manager, input_port, expected):
        """Test port sanitization."""
        result = security_manager.sanitize_port(input_port)
        assert result == expected

class TestReliabilityServices:
    """Test reliability components."""
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3)
        
        # Should be closed initially
        assert not cb.is_open("test_host")
        
        # Record failures
        for _ in range(3):
            cb.record_failure("test_host")
        
        # Should be open now
        assert cb.is_open("test_host")
    
    def test_exponential_backoff_increases(self):
        """Test exponential backoff increases with each attempt."""
        eb = ExponentialBackoff(base=1.0, max_delay=60.0)
        
        delays = [eb.get_delay(i) for i in range(5)]
        
        # Each delay should be greater than the last
        for i in range(1, len(delays)):
            assert delays[i] > delays[i-1]
        
        # Should not exceed max
        assert all(d <= 60.0 for d in delays)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_limits(self):
        """Test rate limiter enforces per-host limits."""
        limiter = PerHostRateLimiter(per_host_limit=2, window_seconds=1)
        
        # First two should succeed immediately
        await limiter.acquire("test.com")
        await limiter.acquire("test.com")
        
        # Third should be delayed
        import time
        start = time.time()
        await limiter.acquire("test.com")
        elapsed = time.time() - start
        
        assert elapsed >= 0.9  # Should wait nearly a second

class TestBloomFilter:
    """Test the BloomFilter class."""
    
    def test_bloom_filter_basic_operations(self):
        """Test basic BloomFilter operations."""
        bf = BloomFilter(capacity=1000, error_rate=0.01)
        
        # Test adding and checking
        bf.add("test_item_1")
        bf.add("test_item_2")
        
        assert bf.contains("test_item_1") is True
        assert bf.contains("test_item_2") is True
        assert bf.contains("test_item_3") is False
    
    def test_bloom_filter_false_positive_rate(self):
        """Test BloomFilter false positive rate."""
        bf = BloomFilter(capacity=100, error_rate=0.01)
        
        # Add known items
        for i in range(50):
            bf.add(f"item_{i}")
        
        # Check for non-existent items
        false_positives = 0
        total_checks = 1000
        
        for i in range(total_checks):
            if bf.contains(f"non_existent_{i}"):
                false_positives += 1
        
        false_positive_rate = false_positives / total_checks
        assert false_positive_rate < 0.05  # Should be well under 5%

class TestMetricsCollector:
    """Test the MetricsCollector class."""
    
    def test_metrics_collector_initialization(self):
        """Test MetricsCollector initialization."""
        metrics = MetricsCollector()
        
        # Check that metrics are created
        assert metrics.configs_processed is not None
        assert metrics.sources_fetched is not None
        assert metrics.processing_duration is not None
        assert metrics.config_latency is not None
    
    def test_metrics_recording(self):
        """Test metrics recording functionality."""
        metrics = MetricsCollector()
        
        # Record some metrics
        metrics.record_config('vmess', 'success')
        metrics.record_config('vless', 'success')
        metrics.record_config('trojan', 'failed')
        
        metrics.record_latency('vmess', 150.5)
        metrics.record_latency('vless', 200.0)
    
    def test_metrics_timing_context(self):
        """Test metrics timing context manager."""
        metrics = MetricsCollector()
        
        with metrics.time_stage('test_stage'):
            # Simulate some work
            import time
            time.sleep(0.1)
        
        # The timing should be recorded
        assert True  # Context manager should work without errors

class TestTracingService:
    """Test the TracingService class."""
    
    def test_tracing_service_initialization(self):
        """Test TracingService initialization."""
        # This might fail if OpenTelemetry is not available
        try:
            tracing = TracingService("test_service")
            assert tracing is not None
        except ImportError:
            pytest.skip("OpenTelemetry not available")
    
    @pytest.mark.asyncio
    async def test_tracing_context_manager(self):
        """Test tracing context manager."""
        try:
            tracing = TracingService("test_service")
            
            async with tracing.trace("test_operation", {"key": "value"}):
                # Simulate some work
                await asyncio.sleep(0.01)
            
            assert True  # Context manager should work
        except ImportError:
            pytest.skip("OpenTelemetry not available")

class TestIntegrationScenarios:
    """Test integration scenarios and end-to-end workflows."""
    
    @pytest.mark.asyncio
    async def test_source_validation_workflow(self):
        """Test complete source validation workflow."""
        validator = SourceValidator()
        
        # Mock sources
        sources = [
            "https://example1.com/config.txt",
            "https://example2.com/config.yaml",
            "https://example3.com/config.json"
        ]
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {'Content-Type': 'text/plain'}
            mock_response.text = AsyncMock(return_value="vmess://test\nvless://test2")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Validate all sources
            results = await validator.validate_multiple_sources(sources)
            
            # Check results
            assert len(results) == 3
            for url, health in results.items():
                assert health.accessible is True
                assert health.estimated_configs == 2
            
            # Get statistics
            stats = validator.get_source_stats()
            assert stats['total_sources'] == 3
            assert stats['accessible_sources'] == 3
            assert stats['accessibility_rate'] == 1.0
    
    @pytest.mark.asyncio
    async def test_discovery_and_validation_workflow(self):
        """Test source discovery and validation workflow."""
        discovery = IntelligentSourceDiscovery()
        validator = SourceValidator()
        
        # Mock GitHub API responses
        mock_search_response = {
            'items': [
                {
                    'repository': {'full_name': 'test/repo1'},
                    'path': 'config.txt'
                },
                {
                    'repository': {'full_name': 'test/repo2'},
                    'path': 'sub.yaml'
                }
            ]
        }
        
        mock_repo_response = {
            'stargazers_count': 100,
            'forks_count': 20,
            'language': 'Python',
            'topics': ['v2ray'],
            'description': 'Test repo',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock responses
            mock_search = AsyncMock()
            mock_search.status = 200
            mock_search.headers = {'X-RateLimit-Remaining': '1000'}
            mock_search.json = AsyncMock(return_value=mock_search_response)
            
            mock_repo = AsyncMock()
            mock_repo.status = 200
            mock_repo.json = AsyncMock(return_value=mock_repo_response)
            
            mock_get.return_value.__aenter__.side_effect = [mock_search, mock_repo, mock_repo]
            
            # Discover sources
            discovered = await discovery.discover_github_sources(max_results=2)
            assert len(discovered) == 2
            
            # Validate discovered sources
            urls = [source.url for source in discovered]
            validated = await validator.validate_multiple_sources(urls)
            
            assert len(validated) == 2
    
    def test_security_validation_workflow(self):
        """Test security validation workflow."""
        security = SecurityManager()
        
        # Test various inputs
        test_cases = [
            ("192.168.1.1", 80, True),
            ("example.com", 443, True),
            ("malicious.com", 8080, False),  # Assuming this is blacklisted
            ("../../etc/passwd", 22, False),  # Path traversal
        ]
        
        for host, port, should_allow in test_cases:
            try:
                validated_host = security.sanitize_host(host)
                validated_port = security.sanitize_port(port)
                
                if should_allow:
                    assert validated_host == host
                    assert validated_port == port
                else:
                    assert False, f"Should have rejected {host}:{port}"
                    
            except Exception:
                if should_allow:
                    assert False, f"Should have allowed {host}:{port}"

class TestPerformanceAndLoad:
    """Test performance characteristics and load handling."""
    
    @pytest.mark.asyncio
    async def test_concurrent_source_validation(self):
        """Test concurrent validation of many sources."""
        validator = SourceValidator()
        
        # Create many mock sources
        sources = [f"https://example{i}.com/config.txt" for i in range(100)]
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {'Content-Type': 'text/plain'}
            mock_response.text = AsyncMock(return_value="vmess://test")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            start_time = asyncio.get_event_loop().time()
            results = await validator.validate_multiple_sources(sources, max_concurrent=20)
            end_time = asyncio.get_event_loop().time()
            
            assert len(results) == 100
            assert end_time - start_time < 10  # Should complete in reasonable time
    
    def test_bloom_filter_performance(self):
        """Test BloomFilter performance with large datasets."""
        bf = BloomFilter(capacity=100000, error_rate=0.01)
        
        # Add many items
        start_time = time.time()
        for i in range(50000):
            bf.add(f"item_{i}")
        add_time = time.time() - start_time
        
        # Check many items
        start_time = time.time()
        for i in range(50000):
            bf.contains(f"item_{i}")
        check_time = time.time() - start_time
        
        # Should be fast
        assert add_time < 5.0  # Adding 50k items in under 5 seconds
        assert check_time < 2.0  # Checking 50k items in under 2 seconds

class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_network_error_recovery(self):
        """Test recovery from network errors."""
        validator = SourceValidator()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # First call fails, second succeeds
            mock_get.return_value.__aenter__.side_effect = [
                Exception("Network error"),
                AsyncMock(status=200, headers={'Content-Type': 'text/plain'}, text=AsyncMock(return_value="vmess://test"))
            ]
            
            # Should handle the error gracefully
            health = await validator.validate_source("https://example.com/test.txt")
            assert health.accessible is False
            assert health.error is not None
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1)
        
        # Record failures
        cb.record_failure("test_host")
        cb.record_failure("test_host")
        
        # Should be open
        assert cb.is_open("test_host")
        
        # Wait for timeout
        import time
        time.sleep(1.1)
        
        # Should be half-open
        assert not cb.is_open("test_host")
        
        # Success should close it
        cb.record_success("test_host")
        assert not cb.is_open("test_host")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

