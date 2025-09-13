import pytest
from unittest.mock import patch, AsyncMock

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.models.configuration import VPNConfiguration, Protocol


def cfg(host: str) -> VPNConfiguration:
    """Helper to create a standard VPNConfiguration for tests."""
    return VPNConfiguration(protocol=Protocol.VMESS, server=host, port=443, user_id="user-id", metadata={})


@pytest.mark.asyncio
async def test_merger_process_all_orchestration(tmp_path):
    """
    Tests the orchestration logic of StreamlineVPNMerger.process_all
    by mocking out the internal components (processor, output manager, etc.).
    """
    # 1. Setup: Create a dummy config and a merger with mocked dependencies
    config_file = tmp_path / "sources.yaml"
    config_file.write_text("sources:\n  tier_1:\n    urls:\n      - https://example.com/sub1\n      - https://example.com/sub2")

    # We patch the class constructors to control the instances created by the merger
    with patch("streamline_vpn.core.merger.VPNCacheService", autospec=True), \
         patch("streamline_vpn.core.merger.FetcherService", autospec=True), \
         patch("streamline_vpn.core.merger.SourceManager", autospec=True), \
         patch("streamline_vpn.core.merger.ConfigurationProcessor", autospec=True), \
         patch("streamline_vpn.core.merger.OutputManager", autospec=True) as MockOutputManager, \
         patch("streamline_vpn.core.merger.SecurityManager", autospec=True) as MockSecurityManager, \
         patch("streamline_vpn.core.merger.MergerProcessor", autospec=True) as MockMergerProcessor:

        merger = StreamlineVPNMerger(config_path=str(config_file))
        await merger.initialize()

        # 2. Configure Mocks: Define the behavior of the mocked components

        # Configure the security manager mock
        security_mock = merger.security_manager
        security_mock.analyze_configuration.return_value = {"is_safe": True}

        # Configure the merger_processor mock to simulate the processing pipeline
        processor_mock = merger.merger_processor
        # Step 1: Process sources, return a tuple of (configs, success_count)
        processor_mock.process_sources.return_value = ([cfg("a"), cfg("b"), cfg("a")], 2)
        # Step 2: Deduplicate, return 2 unique configs
        processor_mock.deduplicate_configurations.return_value = [cfg("a"), cfg("b")]
        # Step 3: Enhance, return 2 enhanced configs
        processor_mock.apply_enhancements.return_value = [cfg("a_enhanced"), cfg("b_enhanced")]

        # Configure the output_manager mock to avoid file I/O
        output_manager_mock = merger.output_manager
        output_manager_mock.save_configurations.return_value = {"formats": ["json"], "paths": ["/tmp/out.json"]}

        # 3. Execute: Run the method under test
        result = await merger.process_all(output_dir=str(tmp_path / "out"), formats=["json"])

        # 4. Assert: Check the results and interactions
        assert result["success"] is True

        # The total_sources comes from the config file (2 sources)
        assert result["total_sources"] == 2
        # The successful_sources comes from the mocked processor
        assert result["successful_sources"] == 2
        # The total_configurations is the count after deduplication (2 unique configs)
        assert result["total_configurations"] == 2

        # Check that the final configurations stored on the merger are the enhanced ones
        final_configs = merger.get_configurations()
        assert len(final_configs) == 2
        assert final_configs[0].server == "a_enhanced"

        # Verify that the mocked methods were called in the correct sequence
        processor_mock.process_sources.assert_called_once()
        # The `_apply_security_validation` step happens before deduplication
        security_mock.analyze_configuration.assert_called()
        processor_mock.deduplicate_configurations.assert_called_once()
        processor_mock.apply_enhancements.assert_called_once()
        output_manager_mock.save_configurations.assert_called_once()
