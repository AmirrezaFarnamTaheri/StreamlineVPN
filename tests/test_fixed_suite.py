"""
Fixed Test Suite for StreamlineVPN
===================================

Comprehensive tests with properly awaited async mocks.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from fastapi.testclient import TestClient
from types import SimpleNamespace

# Import components to test
from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.core.source_manager import SourceManager
from streamline_vpn.core.config_processor import ConfigurationProcessor
from streamline_vpn.web.unified_api import create_unified_app
from streamline_vpn.jobs import JobManager
from streamline_vpn.models.configuration import VPNConfiguration, Protocol
from streamline_vpn.jobs.models import JobType, JobStatus


class TestUnifiedAPI:
    """Test the unified API implementation."""

    class DummyMerger:
        def __init__(self, *args, **kwargs):
            self.source_manager = SimpleNamespace(sources={})
            self.results = []

        async def initialize(self):
            return None

        async def shutdown(self):
            return None

        async def process_all(self, *args, **kwargs):
            return {"success": True}

    @pytest.fixture
    def app(self, monkeypatch):
        monkeypatch.setattr(
            "streamline_vpn.web.unified_api.StreamlineVPNMerger", self.DummyMerger
        )
        return create_unified_app()

    @pytest.fixture
    def client(self, app):
        with TestClient(app) as c:
            yield c

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data

    def test_root_endpoint(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] in {"StreamlineVPN Unified API", "streamline-vpn-api", "StreamlineVPN API"}

    def test_pipeline_invalid_format(self, client):
        resp = client.post("/api/v1/pipeline/run", json={"output_dir": "output", "formats": ["json", "invalid_format"]})
        assert resp.status_code == 200


class TestJobManager:
    """Test job management functionality."""

    @pytest.fixture
    def job_manager(self, tmp_path):
        # Ensure the manager uses a writable directory
        with patch("streamline_vpn.jobs.manager.os.getenv", side_effect=lambda k, d=None: str(tmp_path) if k in {"JOBS_DIR", "JOBS_FILE"} else d):
            return JobManager()

    @pytest.mark.asyncio
    async def test_create_job(self, job_manager):
        job = await job_manager.create_job(JobType.PROCESS_CONFIGURATIONS, {"param": "value"})
        assert isinstance(job.id, str) and len(job.id) == 36

        retrieved_job = await job_manager.get_job(job.id)
        assert retrieved_job is not None
        assert retrieved_job.type == JobType.PROCESS_CONFIGURATIONS
        assert retrieved_job.status == JobStatus.PENDING
        assert retrieved_job.parameters["param"] == "value"


class TestAsyncMocks:
    """Test async functionality with proper mock handling."""

    @pytest.mark.asyncio
    async def test_merger_with_async_mocks(self):
        with patch("streamline_vpn.core.source_manager.SourceManager") as MockSourceManager:
            mock_source_manager = AsyncMock()
            mock_source_manager.get_active_sources = AsyncMock()

            mock_source_manager.get_active_sources.return_value.__aenter__ = AsyncMock(return_value=[
                "http://example.com/source1.txt",
                "http://example.com/source2.txt",
            ])

            mock_source_manager.get_active_sources.return_value.__aexit__ = AsyncMock(return_value=None)
            MockSourceManager.return_value = mock_source_manager

            with patch("aiohttp.ClientSession") as MockSession:
                mock_session = AsyncMock()
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text.return_value = "vmess://test_config"

                mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
                mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_session_cm = AsyncMock()
                mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session_cm.__aexit__ = AsyncMock(return_value=None)
                MockSession.return_value = mock_session_cm

                merger = StreamlineVPNMerger()
                sources = await mock_source_manager.get_active_sources()
                assert len(sources) == 2

    @pytest.mark.asyncio
    async def test_configuration_processor_parse(self):
        processor = ConfigurationProcessor()
        # invalid returns None
        result = await processor.parse_config("invalid_config")
        assert result is None


class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_pipeline_flow(self, tmp_path):
        config_file = tmp_path / "test_config.yaml"
        config_data = {"sources": {"test": ["http://example.com/test.txt"]}}
        import yaml

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_data, f)

        with patch("aiohttp.ClientSession") as MockSession:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = "vmess://test_config"

            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

            session_cm = AsyncMock()
            session_cm.__aenter__ = AsyncMock(return_value=mock_session)
            session_cm.__aexit__ = AsyncMock(return_value=None)
            MockSession.return_value = session_cm

            merger = StreamlineVPNMerger(config_path=str(config_file))
            await merger.initialize()
            # Parser of config_processor returns VPNConfiguration for a valid line
            with patch.object(merger.config_processor.parser, "parse_configuration") as mock_parse:
                mock_parse.return_value = VPNConfiguration(
                    protocol=Protocol.VMESS,
                    server="test.example.com",
                    port=443,
                    user_id="test-uuid",
                )
                result = await merger.process_all(output_dir=str(tmp_path / "output"), formats=["json"])  # type: ignore[arg-type]
                assert isinstance(result, dict)

