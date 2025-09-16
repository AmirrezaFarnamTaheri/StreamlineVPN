"""
Tests for CLI initialization and basic functionality.
"""

import pytest
from unittest.mock import patch
import logging

from streamline_vpn.cli.context import CLIContext


class TestCLIContextInitialization:
    """Test CLI context initialization and logging setup"""

    def test_initialization(self):
        ctx = CLIContext()
        assert ctx.config_path is None
        assert ctx.output_path is None
        assert ctx.verbose is False
        assert ctx.dry_run is False

    def test_setup_logging_default(self):
        ctx = CLIContext()
        with patch('streamline_vpn.cli.context.logging.basicConfig') as mock_basic:
            ctx.setup_logging()
            mock_basic.assert_called_once()

    def test_setup_logging_verbose(self):
        ctx = CLIContext()
        with patch('streamline_vpn.cli.context.logging.basicConfig') as mock_basic:
            ctx.setup_logging(verbose=True)
            mock_basic.assert_called_once()

