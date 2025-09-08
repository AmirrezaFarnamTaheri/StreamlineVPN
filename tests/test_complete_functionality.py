"""
Complete Functionality Tests
============================

Comprehensive tests for all StreamlineVPN components.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.security.manager import SecurityManager
from streamline_vpn.jobs.manager import JobManager
from streamline_vpn.fetcher.service import FetcherService
from streamline_vpn.state.manager import StateManager
from streamline_vpn.state.fsm import SourceState, SourceEvent
from streamline_vpn.web.api import create_app
from streamline_vpn.jobs.models import Job, JobType, JobStatus
from streamline_vpn.security.threat_analyzer import ThreatAnalyzer
from streamline_vpn.security.validator import SecurityValidator
from streamline_vpn.fetcher.circuit_breaker import CircuitBreaker
from streamline_vpn.fetcher.rate_limiter import RateLimiter
from streamline_vpn.state.fsm import SourceStateMachine

# Optional GraphQL import
try:
    from streamline_vpn.web.graphql import create_graphql_app
except ImportError:
    create_graphql_app = None


class TestCompleteFunctionality:
    """Test complete functionality of all components."""

    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create temporary config file."""
        config_content = """
sources:
  - name: TestSource1
    url: http://example.com/configs1.txt
    type: http
    tier: community
    enabled: true
  - name: TestSource2
    url: http://example.com/configs2.txt
    type: http
    tier: premium
    enabled: true
"""
        file_path = tmp_path / "sources.yaml"
        file_path.write_text(config_content)
        return file_path

    @pytest.mark.asyncio
    async def test_core_merger_functionality(self, temp_config_file):
        """Test core merger functionality."""
        merger = StreamlineVPNMerger(config_path=str(temp_config_file))

        # Test initialization
        assert merger is not None
        assert merger.config_path == str(temp_config_file)

        # Test statistics
        stats = await merger.get_statistics()
        assert isinstance(stats, dict)
        assert "total_sources" in stats

    @pytest.mark.asyncio
    async def test_web_interface_creation(self):
        """Test web interface creation."""
        # Test FastAPI app creation
        app = create_app()
        assert app is not None
        assert app.get_app().title == "StreamlineVPN API"

        # Test GraphQL app creation (if available)
        if create_graphql_app is not None:
            graphql_app = create_graphql_app()
            assert graphql_app is not None

    @pytest.mark.asyncio
    async def test_job_management_system(self):
        """Test job management system."""
        job_manager = JobManager()

        # Test job creation
        job = await job_manager.create_job(
            JobType.PROCESS_CONFIGURATIONS,
            parameters={"output_dir": "test_output"},
            metadata={"test": True},
        )

        assert job is not None
        assert job.type == JobType.PROCESS_CONFIGURATIONS
        assert job.status == JobStatus.PENDING

        # Test job retrieval
        retrieved_job = await job_manager.get_job(job.id)
        assert retrieved_job is not None
        assert retrieved_job.id == job.id

        # Test job statistics
        stats = await job_manager.get_statistics()
        assert isinstance(stats, dict)
        assert "total_jobs" in stats

    @pytest.mark.asyncio
    async def test_security_components(self):
        """Test security components."""
        security_manager = SecurityManager()

        # Test configuration analysis
        test_config = "vmess://test-config"
        analysis = security_manager.analyze_configuration(test_config)

        assert isinstance(analysis, dict)
        assert "threats" in analysis
        assert "risk_score" in analysis
        assert "is_safe" in analysis

        # Test source validation
        validation = security_manager.validate_source("https://example.com")
        assert isinstance(validation, dict)
        assert "is_safe" in validation

        # Test threat analyzer
        threat_analyzer = ThreatAnalyzer()
        threats = threat_analyzer.analyze(test_config)
        assert isinstance(threats, list)

        # Test security validator
        validator = SecurityValidator()
        is_valid = validator.validate_url("https://example.com")
        assert isinstance(is_valid, bool)

    @pytest.mark.asyncio
    async def test_fetcher_service(self):
        """Test fetcher service."""
        async with FetcherService() as fetcher:
            # Test statistics
            stats = fetcher.get_statistics()
            assert isinstance(stats, dict)
            assert "total_requests" in stats

            # Test circuit breaker
            circuit_breaker = CircuitBreaker()
            assert circuit_breaker.get_state().value == "closed"

            # Test rate limiter
            rate_limiter = RateLimiter()
            is_allowed = await rate_limiter.is_allowed("test_key")
            assert isinstance(is_allowed, bool)

    @pytest.mark.asyncio
    async def test_state_management(self):
        """Test state management system."""
        state_manager = StateManager()

        # Test state machine creation
        state_machine = state_manager.get_or_create_state_machine(
            "test_source"
        )
        assert state_machine is not None
        assert state_machine.current_state == SourceState.UNKNOWN

        # Test state transition
        success = state_manager.transition_source(
            "test_source", SourceEvent.ENABLE
        )
        assert success is True

        # Test state retrieval
        current_state = state_manager.get_source_state("test_source")
        assert current_state == SourceState.ACTIVE

        # Test state statistics
        stats = state_manager.get_state_statistics()
        assert isinstance(stats, dict)
        assert "total_sources" in stats

    @pytest.mark.asyncio
    async def test_integration_workflow(self, temp_config_file):
        """Test complete integration workflow."""
        # Create merger
        merger = StreamlineVPNMerger(config_path=str(temp_config_file))

        # Create job manager
        job_manager = JobManager()

        # Create security manager
        security_manager = SecurityManager()

        # Create state manager
        state_manager = StateManager()

        # Test workflow
        job = await job_manager.create_job(JobType.PROCESS_CONFIGURATIONS)
        assert job is not None

        # Test state transition
        state_manager.transition_source("test_source", SourceEvent.ENABLE)
        state = state_manager.get_source_state("test_source")
        assert state == SourceState.ACTIVE

        # Test security analysis
        analysis = security_manager.analyze_configuration("test config")
        assert analysis["is_safe"] is not None

    def test_data_models(self):
        """Test data models."""
        # Test Job model
        job = Job(
            type=JobType.PROCESS_CONFIGURATIONS, parameters={"test": "value"}
        )

        assert job.type == JobType.PROCESS_CONFIGURATIONS
        assert job.status == JobStatus.PENDING
        assert job.parameters["test"] == "value"

        # Test job serialization
        job_dict = job.to_dict()
        assert isinstance(job_dict, dict)
        assert job_dict["type"] == "process_configurations"

        # Test job deserialization
        job_from_dict = Job.from_dict(job_dict)
        assert job_from_dict.id == job.id
        assert job_from_dict.type == job.type

    def test_state_machine_transitions(self):
        """Test state machine transitions."""
        fsm = SourceStateMachine()

        # Test initial state
        assert fsm.current_state == SourceState.UNKNOWN

        # Test valid transition
        success = fsm.transition(SourceEvent.ENABLE)
        assert success is True
        assert fsm.current_state == SourceState.ACTIVE

        # Test invalid transition
        success = fsm.transition(SourceEvent.ENABLE)  # Already enabled
        assert success is False

        # Test valid events
        valid_events = fsm.get_valid_events()
        assert SourceEvent.DISABLE in valid_events
        assert SourceEvent.FAILURE in valid_events

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling across components."""
        # Test job manager error handling
        job_manager = JobManager()

        # Test with invalid job type
        try:
            job = await job_manager.create_job("invalid_type")
            assert False, "Should have raised an error"
        except Exception:
            pass  # Expected

        # Test security manager error handling
        security_manager = SecurityManager()

        # Test with invalid input
        analysis = security_manager.analyze_configuration("")
        assert analysis["is_safe"] is False

        # Test state manager error handling
        state_manager = StateManager()

        # Test with non-existent source
        state = state_manager.get_source_state("non_existent")
        assert state is None

    def test_configuration_validation(self):
        """Test configuration validation."""
        validator = SecurityValidator()

        # Test valid configurations
        valid_configs = [
            {"protocol": "vmess", "server": "1.1.1.1", "port": 443},
            {"protocol": "vless", "server": "example.com", "port": 8080},
        ]

        for config in valid_configs:
            result = validator.validate_configuration(config)
            assert result["is_valid"] is True

        # Test invalid configurations
        invalid_configs = [
            {"protocol": "invalid", "server": "1.1.1.1", "port": 443},
            {"protocol": "vmess", "server": "1.1.1.1", "port": 99999},
        ]

        for config in invalid_configs:
            result = validator.validate_configuration(config)
            assert result["is_valid"] is False

    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test performance metrics collection."""
        # Test fetcher service metrics
        async with FetcherService() as fetcher:
            stats = fetcher.get_statistics()
            assert "total_requests" in stats
            assert "successful_requests" in stats
            assert "failed_requests" in stats

        # Test job manager metrics
        job_manager = JobManager()
        stats = await job_manager.get_statistics()
        assert "total_jobs" in stats
        assert "status_counts" in stats

        # Test state manager metrics
        state_manager = StateManager()
        stats = state_manager.get_state_statistics()
        assert "total_sources" in stats
        assert "states" in stats

    def test_utility_functions(self):
        """Test utility functions."""
        from streamline_vpn.utils.helpers import format_bytes, format_duration

        # Test formatting functions
        assert format_bytes(1024) == "1.0 KB"
        assert format_duration(65.5) == "1m 5s"

        from streamline_vpn.security.validator import SecurityValidator
        from streamline_vpn.utils.validation import is_valid_ip

        # Test validation functions
        validator = SecurityValidator()
        assert validator.validate_url("https://example.com") is True
        assert validator.validate_url("invalid-url") is False
        assert is_valid_ip("1.1.1.1") is True
        assert is_valid_ip("invalid-ip") is False
