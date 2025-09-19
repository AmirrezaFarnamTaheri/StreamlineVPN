import pytest
import runpy
import sys
from unittest.mock import patch, MagicMock

from streamline_vpn.merger import cli

@pytest.fixture
def mock_parsers():
    # Use create=True because the modules might not have the functions if they fail to import
    with patch('streamline_vpn.merger.aggregator_tool.build_parser', create=True) as mock_agg_parser, \
         patch('streamline_vpn.merger.vpn_merger.build_parser', create=True) as mock_merge_parser, \
         patch('streamline_vpn.merger.vpn_retester.build_parser', create=True) as mock_retest_parser:
        yield {
            "aggregator": mock_agg_parser,
            "merger": mock_merge_parser,
            "retester": mock_retest_parser,
        }

@pytest.fixture
def mock_mains():
    with patch('streamline_vpn.merger.aggregator_tool.main', create=True) as mock_agg_main, \
         patch('streamline_vpn.merger.vpn_merger.main', create=True) as mock_merge_main, \
         patch('streamline_vpn.merger.vpn_retester.main', create=True) as mock_retest_main:
        yield {
            "aggregator": mock_agg_main,
            "merger": mock_merge_main,
            "retester": mock_retest_main,
        }

@patch('streamline_vpn.merger.cli.print_public_source_warning')
def test_cli_fetch_command(mock_print_warning, mock_parsers, mock_mains):
    cli.main(['fetch'])
    mock_print_warning.assert_called_once()
    mock_parsers["aggregator"].assert_called()
    mock_mains["aggregator"].assert_called_once()
    # Check that it's called with the parsed namespace
    args, _ = mock_mains["aggregator"].call_args
    assert args[0].command == 'fetch'

@patch('streamline_vpn.merger.cli.print_public_source_warning')
def test_cli_merge_command(mock_print_warning, mock_parsers, mock_mains):
    cli.main(['merge'])
    mock_print_warning.assert_called_once()
    mock_parsers["merger"].assert_called_once()
    mock_mains["merger"].assert_called_once()
    args, _ = mock_mains["merger"].call_args
    assert args[0].command == 'merge'

@patch('streamline_vpn.merger.cli.print_public_source_warning')
def test_cli_retest_command(mock_print_warning, mock_parsers, mock_mains):
    cli.main(['retest'])
    mock_print_warning.assert_called_once()
    mock_parsers["retester"].assert_called_once()
    mock_mains["retester"].assert_called_once()
    args, _ = mock_mains["retester"].call_args
    assert args[0].command == 'retest'

@patch('streamline_vpn.merger.cli.print_public_source_warning')
def test_cli_full_command(mock_print_warning, mock_parsers, mock_mains):
    cli.main(['full'])
    mock_print_warning.assert_called_once()
    # 'full' command calls aggregator_tool.build_parser
    mock_parsers["aggregator"].assert_called()
    # 'full' command calls aggregator_tool.main
    mock_mains["aggregator"].assert_called_once()
    args, _ = mock_mains["aggregator"].call_args
    assert args[0].command == 'full'
    assert args[0].with_merger is True

def test_main_entrypoint(mocker):
    """
    Test that running the script via `if __name__ == '__main__'` calls main().
    """
    # We patch the downstream main functions to prevent the full app from running.
    mock_agg_main = mocker.patch("streamline_vpn.merger.aggregator_tool.main")

    # We also need to prevent config loading from failing in the sub-commands.
    mocker.patch("streamline_vpn.merger.vpn_merger.load_config", return_value=MagicMock())
    mocker.patch("streamline_vpn.merger.vpn_retester.load_config", return_value=MagicMock())
    mocker.patch("streamline_vpn.merger.aggregator_tool.load_config", return_value=MagicMock())


    # Patch sys.argv to provide a valid command.
    with patch.object(sys, "argv", ["massconfigmerger", "fetch"]):
        runpy.run_module("streamline_vpn.merger.cli", run_name="__main__")

    # The __main__ block calls main(), which then calls aggregator_tool.main()
    mock_agg_main.assert_called_once()
