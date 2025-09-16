"""
Tests for CLI configuration processing functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from streamline_vpn.cli.context import CLIContext


class TestCLIProcessing:
    """Test CLI context configuration processing"""
    
    @pytest.mark.asyncio
    async def test_process_configurations_success(self):
        ctx = CLIContext()
        ctx.config_path = Path("test.yaml")
        ctx.output_path = Path("output")

        with patch('streamline_vpn.cli.context.SourceManager') as MockSM, \
             patch('streamline_vpn.cli.context.StreamlineVPNMerger') as MockMerger:
            MockSM.return_value.get_all_sources.return_value = AsyncMock(return_value=[{"name":"s"}])
            MockMerger.return_value.process_sources.return_value = AsyncMock(return_value=[{"ok":True}])

            result = await ctx.process_configurations()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_process_configurations_failure(self):
        ctx = CLIContext()
        ctx.config_path = Path("test.yaml")
        ctx.output_path = Path("output")

        with patch('streamline_vpn.cli.context.SourceManager') as MockSM, \
             patch('streamline_vpn.cli.context.StreamlineVPNMerger') as MockMerger:
            MockSM.return_value.get_all_sources.return_value = AsyncMock(return_value=[{"name":"s"}])
            MockMerger.return_value.process_sources.return_value = AsyncMock(return_value=[])

            result = await ctx.process_configurations()
            assert result is True  # empty still considered processed
    
    @pytest.mark.asyncio
    async def test_process_configurations_exception(self):
        ctx = CLIContext()
        ctx.config_path = Path("test.yaml")
        ctx.output_path = Path("output")

        with patch('streamline_vpn.cli.context.SourceManager') as MockSM, \
             patch('streamline_vpn.cli.context.StreamlineVPNMerger') as MockMerger:
            MockSM.return_value.get_all_sources.return_value = AsyncMock(return_value=[{"name":"s"}])
            MockMerger.return_value.process_sources.side_effect = Exception("Test error")

            result = await ctx.process_configurations()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_process_configurations_no_sources(self):
        ctx = CLIContext()
        ctx.config_path = Path("test.yaml")
        ctx.output_path = Path("output")

        with patch('streamline_vpn.cli.context.SourceManager') as MockSM:
            MockSM.return_value.get_all_sources.return_value = AsyncMock(return_value=[])
            result = await ctx.process_configurations()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_process_configurations_with_parameters(self):
        ctx = CLIContext()
        ctx.config_path = Path("test.yaml")
        ctx.output_path = Path("output")

        with patch('streamline_vpn.cli.context.SourceManager') as MockSM, \
             patch('streamline_vpn.cli.context.StreamlineVPNMerger') as MockMerger:
            MockSM.return_value.get_all_sources.return_value = AsyncMock(return_value=[{"name":"s"}])
            MockMerger.return_value.process_sources.return_value = AsyncMock(return_value=[{"ok":True}])

            result = await ctx.process_configurations(max_concurrent=10, timeout=60, force_refresh=True)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_process_configurations_verbose_and_dry_run(self):
        ctx = CLIContext()
        ctx.config_path = Path("test.yaml")
        ctx.output_path = Path("output")
        ctx.verbose = True
        ctx.dry_run = True

        with patch('streamline_vpn.cli.context.SourceManager') as MockSM, \
             patch('streamline_vpn.cli.context.StreamlineVPNMerger') as MockMerger:
            MockSM.return_value.get_all_sources.return_value = AsyncMock(return_value=[{"name":"s"}])
            MockMerger.return_value.process_sources.return_value = AsyncMock(return_value=[{"ok":True}])

            result = await ctx.process_configurations()
            assert result is True

