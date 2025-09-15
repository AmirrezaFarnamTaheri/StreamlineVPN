import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from streamline_vpn.core.config_processor import ConfigurationProcessor
from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.core.output_manager import OutputManager
from streamline_vpn.core.source_manager import SourceManager
from streamline_vpn.discovery.manager import DiscoveryManager
from streamline_vpn.jobs.manager import JobManager
from streamline_vpn.jobs.models import Job, JobStatus, JobType
from streamline_vpn.jobs.persistence import JobPersistence
from streamline_vpn.models.configuration import Protocol, VPNConfiguration
from streamline_vpn.security.manager import SecurityManager


class TestStreamlineVPNCore:
    """Complete tests for core StreamlineVPN functionality."""

    @pytest.fixture
    def sample_config(self, tmp_path):
        config = {
            "sources": {
                "premium": {
                    "urls": [
                        {
                            "url": "https://example.com/premium.txt",
                            "weight": 0.9,
                        },
                        {
                            "url": "https://example.com/premium2.txt",
                            "weight": 0.8,
                        },
                    ]
                },
                "reliable": {"urls": ["https://example.com/reliable.txt"]},
            },
            "processing": {
                "max_concurrent": 50,
                "timeout": 30,
                "retry_attempts": 3,
            },
            "output": {"formats": ["json", "clash", "singbox"]},
        }
        config_file = tmp_path / "test_config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)
        return str(config_file)

    @pytest.fixture
    def sample_vpn_config(self):
        return VPNConfiguration(
            protocol=Protocol.VMESS,
            server="test.example.com",
            port=443,
            user_id="test-uuid",
            encryption="auto",
            network="ws",
            path="/test",
            tls=True,
            quality_score=0.85,
            source_url="https://example.com/source.txt",
        )

    @pytest.mark.asyncio
    async def test_merger_full_processing(self, sample_config, tmp_path):
        """
        Tests the full processing pipeline of the merger with a mocked fetcher.
        """
        # Patch the underlying fetch service to avoid actual network calls
        with patch("streamline_vpn.core.merger.FetcherService.fetch", new_callable=AsyncMock) as mock_fetch:
            # Have the mock fetcher return a valid base64-encoded config
            # The source_manager's parser should be able to decode this.
            vmess_config_b64 = "ewogICJ2IjogIjIiLAogICJwcyI6ICJUZXN0IiwKICAiYWRkIjogImV4YW1wbGUuY29tIiwKICAicG9ydCI6IDQ0MywKICAiaWQiOiAiZmQ3YWQyMTYtZDIzMy00ZmY4LWE4M2EtZTZlMGU3ODU3ZmM2IiwKICAiYWlkIjogMCwKICAibmV0IjogIndzIiwKICAidHlwZSI6ICJub25lIiwKICAiaG9zdCI6ICJleGFtcGxlLmNvbSIsCiAgInBhdGgiOiAiLyIsCiAgInRscyI6ICJ0bHMiCn0="
            mock_fetch.return_value = f"vmess://{vmess_config_b64}"

            # Initialize the merger with the sample config
            merger = StreamlineVPNMerger(config_path=sample_config)

            # Run the entire process
            result = await merger.process_all(output_dir=str(tmp_path))

            # Assert the results based on the new API
            assert result is not None
            assert result["success"] is True

            # The sample_config fixture defines 3 source URLs
            assert result["total_sources"] == 3
            assert result["successful_sources"] == 3 # Our mock makes all sources succeed

            # Since mock_fetch returns the same config each time, deduplication should result in 1 unique config
            assert result["total_configurations"] == 1

            # The fetcher should have been called for each of the 3 sources in the config
            assert mock_fetch.call_count == 3

            # Check for presence of new statistical keys
            assert "processing_time" in result
            assert "configurations_per_second" in result

    @pytest.mark.asyncio
    async def test_source_manager_operations(self, sample_config):
        manager = SourceManager(sample_config)
        assert len(manager.sources) > 0
        test_url = "https://example.com/test.txt"
        manager.blacklist_source(test_url, "Test reason")
        if test_url in manager.sources:
            assert manager.sources[test_url].is_blacklisted
        manager.whitelist_source(test_url)
        if test_url in manager.sources:
            assert not manager.sources[test_url].is_blacklisted
        await manager.update_source_performance(
            source_url=test_url,
            success=True,
            config_count=100,
            response_time=1.5,
        )
        stats = manager.get_source_statistics()
        assert "total_sources" in stats
        assert "active_sources" in stats

    @pytest.mark.asyncio
    async def test_config_processor_complete(self, sample_vpn_config):
        processor = ConfigurationProcessor()
        config_line = (
            "vmess://eyJhZGQiOiJ0ZXN0LmV4YW1wbGUuY29tIiwicG9ydCI6NDQzfQ=="
        )
        await processor.parse_config(config_line)
        is_valid = processor.validate_config(
            {"protocol": "vmess", "server": "test.com", "port": 443}
        )
        assert isinstance(is_valid, bool)
        configs = [sample_vpn_config, sample_vpn_config]
        unique = processor.deduplicate_configurations(configs)
        assert len(unique) == 1
        stats = processor.get_statistics()
        assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_output_manager_all_formats(
        self, tmp_path, sample_vpn_config
    ):
        manager = OutputManager()
        configs = [sample_vpn_config]
        formats = ["raw", "base64", "json", "csv", "clash", "singbox"]
        for fmt in formats:
            output_path = await manager.save_configurations(
                configs, str(tmp_path), fmt
            )
            assert output_path.exists() or output_path is not None

    def test_vpn_configuration_model(self):
        config = VPNConfiguration(
            protocol=Protocol.VLESS,
            server="example.com",
            port=8080,
            user_id="test-id",
        )
        assert config.is_valid
        config_dict = config.to_dict()
        assert config_dict["protocol"] == "vless"
        assert config_dict["server"] == "example.com"
        with pytest.raises(ValueError):
            VPNConfiguration(protocol=Protocol.VMESS, server="", port=443)


class TestJobManagement:
    """Complete tests for job management system."""

    @pytest.fixture
    def job_manager(self, tmp_path):
        jobs_file = tmp_path / "test_jobs.json"
        return JobManager(persistence=JobPersistence(str(jobs_file)))

    @pytest.mark.asyncio
    async def test_job_lifecycle(self, job_manager):
        job = await job_manager.create_job(
            JobType.PROCESS_CONFIGURATIONS,
            parameters={"test": "value"},
            metadata={"test_run": True},
        )
        assert job is not None
        assert job.status == JobStatus.PENDING
        success = await job_manager.start_job(job.id)
        assert success
        retrieved = await job_manager.get_job(job.id)
        assert retrieved is not None
        cancelled = await job_manager.cancel_job(job.id)
        assert cancelled
        final_job = await job_manager.get_job(job.id)
        assert final_job.status == JobStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_job_statistics(self, job_manager):
        for i in range(5):
            await job_manager.create_job(
                JobType.PROCESS_CONFIGURATIONS, parameters={"i": i}
            )
        stats = await job_manager.get_statistics()
        assert stats["total_jobs"] >= 5
        assert "status_counts" in stats
        assert "type_counts" in stats

    def test_job_model_validation(self):
        job = Job(
            type=JobType.DISCOVER_SOURCES, parameters={"source": "github"}
        )
        assert job.status == JobStatus.PENDING
        job.start()
        assert job.status == JobStatus.RUNNING
        job.complete({"result": "success"})
        assert job.status == JobStatus.COMPLETED
        job_dict = job.to_dict()
        assert job_dict["type"] == "discover_sources"
        assert job_dict["status"] == "completed"


class TestSecurityComponents:
    """Complete tests for security components."""

    @pytest.fixture
    def security_manager(self):
        return SecurityManager()

    def test_source_validation(self, security_manager):
        valid_urls = [
            "https://example.com/configs.txt",
            "http://raw.githubusercontent.com/user/repo/main/sub.txt",
        ]
        for url in valid_urls:
            assert security_manager.validate_source(url)["is_safe"] is True
        invalid_urls = [
            "javascript:alert('xss')",
            "file:///etc/passwd",
            "../../../etc/passwd",
        ]
        for url in invalid_urls:
            assert security_manager.validate_source(url)["is_safe"] is False

    def test_configuration_analysis(self, security_manager):
        safe_config = "vmess://eyJhZGQiOiJleGFtcGxlLmNvbSIsInBvcnQiOjQ0M30="
        analysis = security_manager.analyze_configuration(safe_config)
        assert "threats" in analysis
        assert "risk_score" in analysis
        assert "is_safe" in analysis
        suspicious_config = "vmess://suspicious-pattern-12345"
        analysis = security_manager.analyze_configuration(suspicious_config)
        assert isinstance(analysis["risk_score"], float)
        assert 0 <= analysis["risk_score"] <= 1


class TestDiscoveryManager:
    """Complete tests for discovery manager."""

    @pytest.fixture
    def discovery_manager(self):
        return DiscoveryManager()

    @pytest.mark.asyncio
    async def test_source_discovery(self, discovery_manager):
        """Test discovery with properly mocked async session methods to avoid warnings."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"items": [{"full_name": "user/repo"}]}
        mock_response.text.return_value = "vmess://test"

        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_session.head.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.head.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session_cm):
            sources = await discovery_manager.discover_sources()
            assert isinstance(sources, list)

    @pytest.mark.asyncio
    async def test_discovery_with_error_handling(self, discovery_manager):
        """Test discovery with proper error handling."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.raise_for_status.side_effect = Exception("Not found")

        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_session_cm = AsyncMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session_cm):
            sources = await discovery_manager.discover_sources()
            assert isinstance(sources, list)

    def test_discovery_statistics(self, discovery_manager):
        stats = discovery_manager.get_statistics()
        assert "discovered_sources_count" in stats
        assert "last_discovery" in stats
        assert "discovery_interval_hours" in stats


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, tmp_path):
        config = {"sources": {"test": ["https://example.com/test.txt"]}}
        config_file = tmp_path / "e2e_config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)
        merger = StreamlineVPNMerger(config_path=str(config_file))
        await merger.initialize()
        with patch.object(merger.source_manager, "fetch_source") as mock_fetch:
            mock_fetch.return_value = AsyncMock(
                success=True, configs=["vmess://test"], response_time=0.1
            )
            with patch.object(
                merger.config_processor.parser, "parse_configuration"
            ) as mock_parse:
                mock_parse.return_value = VPNConfiguration(
                    protocol=Protocol.VMESS, server="test.com", port=443
                )
                result = await merger.process_all(
                    output_dir=str(tmp_path), formats=["json"]
                )
                assert isinstance(result["success"], bool)

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, tmp_path):
        merger = StreamlineVPNMerger()
        await merger.initialize()
        sources = [f"https://example.com/source{i}.txt" for i in range(10)]
        with patch.object(
            merger.source_manager, "get_active_sources"
        ) as mock_sources:
            mock_sources.return_value = sources
            with patch.object(
                merger.source_manager, "fetch_source"
            ) as mock_fetch:
                mock_fetch.return_value = AsyncMock(
                    success=True, configs=["vmess://test"], response_time=0.1
                )
                await merger.process_all()
                assert mock_fetch.call_count <= len(sources) + 1


class TestPerformance:
    """Performance and stress tests."""

    @pytest.mark.asyncio
    async def test_large_configuration_set(self):
        processor = ConfigurationProcessor()
        configs = []
        for i in range(1000):
            configs.append(
                VPNConfiguration(
                    protocol=Protocol.VMESS,
                    server=f"server{i}.com",
                    port=443 + i,
                )
            )
        start = asyncio.get_event_loop().time()
        unique = processor.deduplicate_configurations(configs)
        duration = asyncio.get_event_loop().time() - start
        assert len(unique) == len(configs)
        assert duration < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_source_fetching(self):
        merger = StreamlineVPNMerger()
        await merger.initialize()
        sources = [f"https://example{i}.com/configs.txt" for i in range(50)]
        with patch.object(
            merger.source_manager, "get_active_sources"
        ) as mock_sources:
            mock_sources.return_value = sources
            with patch.object(
                merger.source_manager, "fetch_source"
            ) as mock_fetch:

                async def fetch_side_effect(url):
                    await asyncio.sleep(0.01)
                    return AsyncMock(
                        success=True,
                        configs=["vmess://test"],
                        response_time=0.1,
                    )

                mock_fetch.side_effect = fetch_side_effect
                start = asyncio.get_event_loop().time()
                await merger.process_all()
                duration = asyncio.get_event_loop().time() - start
                assert duration < 5.0
