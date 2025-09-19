import pytest
from pathlib import Path
import base64
from unittest.mock import patch, MagicMock, AsyncMock

from streamline_vpn.merger.vpn_retester import (
    load_configs,
    filter_configs,
    save_results,
    retest_configs,
    main as retester_main,
)
from streamline_vpn.merger.result_processor import CONFIG

# Tests for load_configs
def test_load_configs_raw(tmp_path):
    p = tmp_path / "sub.txt"
    p.write_text("vmess://config1\nvless://config2")
    configs = load_configs(p)
    assert configs == ["vmess://config1", "vless://config2"]

def test_load_configs_base64(tmp_path):
    p = tmp_path / "sub.txt"
    content = "vmess://config1\nvless://config2"
    encoded_content = base64.b64encode(content.encode()).decode()
    p.write_text(encoded_content)
    configs = load_configs(p)
    assert configs == ["vmess://config1", "vless://config2"]

def test_load_configs_file_not_found():
    with pytest.raises(OSError):
        load_configs(Path("non_existent_file.txt"))

def test_load_configs_invalid_base64(tmp_path):
    p = tmp_path / "sub.txt"
    p.write_text("this is not valid base64")
    with pytest.raises(ValueError, match="Failed to decode base64 input"):
        load_configs(p)

# Tests for filter_configs
@patch('streamline_vpn.merger.vpn_retester.EnhancedConfigProcessor')
def test_filter_configs_no_filters(MockProcessor):
    configs = ["vmess://config1", "trojan://config2"]
    with patch.object(CONFIG, 'include_protocols', None), \
         patch.object(CONFIG, 'exclude_protocols', None):
        filtered = filter_configs(configs)
    assert filtered == configs

@patch('streamline_vpn.merger.vpn_retester.EnhancedConfigProcessor')
def test_filter_configs_include(MockProcessor):
    mock_proc = MockProcessor.return_value
    mock_proc.categorize_protocol.side_effect = lambda c: c.split('://')[0].upper()

    configs = ["vmess://config1", "trojan://config2", "ss://config3"]
    with patch.object(CONFIG, 'include_protocols', {"VMESS", "SS"}):
        filtered = filter_configs(configs)
    assert filtered == ["vmess://config1", "ss://config3"]

@patch('streamline_vpn.merger.vpn_retester.EnhancedConfigProcessor')
def test_filter_configs_exclude(MockProcessor):
    mock_proc = MockProcessor.return_value
    mock_proc.categorize_protocol.side_effect = lambda c: c.split('://')[0].upper()

    configs = ["vmess://config1", "trojan://config2", "ss://config3"]
    with patch.object(CONFIG, 'exclude_protocols', {"VMESS", "SS"}):
        filtered = filter_configs(configs)
    assert filtered == ["trojan://config2"]

@patch('streamline_vpn.merger.vpn_retester.EnhancedConfigProcessor')
def test_filter_configs_include_and_exclude(MockProcessor):
    mock_proc = MockProcessor.return_value
    mock_proc.categorize_protocol.side_effect = lambda c: c.split('://')[0].upper()

    configs = ["vmess://config1", "trojan://config2", "ss://config3"]
    with patch.object(CONFIG, 'include_protocols', {"VMESS", "TROJAN"}), \
         patch.object(CONFIG, 'exclude_protocols', {"TROJAN"}):
        filtered = filter_configs(configs)
    assert filtered == ["vmess://config1"]

# Tests for save_results
def test_save_results_basic(tmp_path):
    results = [("vmess://config1", 0.1), ("trojan://config2", 0.2)]
    with patch.object(CONFIG, 'output_dir', str(tmp_path)):
        save_results(results, sort=False, top_n=0)

    raw_file = tmp_path / "vpn_retested_raw.txt"
    assert raw_file.exists()
    assert raw_file.read_text() == "vmess://config1\ntrojan://config2"

def test_save_results_sorted(tmp_path):
    results = [("vmess://config1", 0.2), ("trojan://config2", 0.1)]
    with patch.object(CONFIG, 'output_dir', str(tmp_path)):
        save_results(results, sort=True, top_n=0)

    raw_file = tmp_path / "vpn_retested_raw.txt"
    assert raw_file.read_text() == "trojan://config2\nvmess://config1"

def test_save_results_top_n(tmp_path):
    results = [("vmess://config1", 0.2), ("trojan://config2", 0.1), ("ss://config3", 0.3)]
    with patch.object(CONFIG, 'output_dir', str(tmp_path)):
        save_results(results, sort=True, top_n=2)

    raw_file = tmp_path / "vpn_retested_raw.txt"
    assert raw_file.read_text() == "trojan://config2\nvmess://config1"

def test_save_results_with_base64_and_csv(tmp_path):
    results = [("vmess://config1", 0.1)]
    with patch.object(CONFIG, 'output_dir', str(tmp_path)), \
         patch.object(CONFIG, 'write_base64', True), \
         patch.object(CONFIG, 'write_csv', True):
        save_results(results, sort=False, top_n=0)

    base64_file = tmp_path / "vpn_retested_base64.txt"
    assert base64_file.exists()
    expected_b64 = base64.b64encode(b"vmess://config1").decode()
    assert base64_file.read_text() == expected_b64

    csv_file = tmp_path / "vpn_retested_detailed.csv"
    assert csv_file.exists()
    assert "vmess://config1,100.0" in csv_file.read_text()

# Tests for retest_configs
@pytest.mark.asyncio
async def test_retest_configs():
    configs = ["vmess://config1", "invalid-config"]

    mock_proc = MagicMock()
    mock_proc.extract_host_port.side_effect = [("host1", 123), (None, None)]

    async def fake_test_connection(host, port):
        if host == "host1":
            return 0.123
        return None

    mock_proc.test_connection = fake_test_connection
    mock_proc.tester.close = AsyncMock()

    with patch('streamline_vpn.merger.vpn_retester.EnhancedConfigProcessor', return_value=mock_proc):
        results = await retest_configs(configs)

    assert len(results) == 2
    assert results[0] == ("vmess://config1", 0.123)
    assert results[1] == ("invalid-config", None)
    mock_proc.tester.close.assert_awaited_once()

# Tests for main function
@patch('streamline_vpn.merger.vpn_retester.load_configs')
@patch('streamline_vpn.merger.vpn_retester.filter_configs')
@patch('streamline_vpn.merger.vpn_retester.retest_configs', new_callable=AsyncMock)
@patch('streamline_vpn.merger.vpn_retester.save_results')
@patch('streamline_vpn.merger.vpn_retester.load_config')
@patch('streamline_vpn.merger.vpn_retester.asyncio.run')
def test_retester_main(mock_async_run, mock_load_conf, mock_save, mock_retest, mock_filter, mock_load):
    # Mock the return values of the functions called by main
    mock_load.return_value = ["vmess://config1"]
    mock_filter.return_value = ["vmess://config1"]
    mock_async_run.return_value = [("vmess://config1", 0.1)] # retest_configs is async

    # Create a mock args namespace
    args = MagicMock()
    args.input = "dummy_path"
    args.no_sort = False
    args.top_n = 0
    args.concurrent_limit = 100
    args.connect_timeout = 5.0
    args.max_ping = 2000
    args.include_protocols = None
    args.exclude_protocols = "OTHER"
    args.output_dir = "/tmp/output"
    args.history_file = None
    args.no_base64 = False
    args.no_csv = False

    # Call the main function with the mock args
    retester_main(args)

    # Assert that the functions were called
    mock_load_conf.assert_called_once()
    mock_load.assert_called_once_with(Path("dummy_path"))
    mock_filter.assert_called_once_with(["vmess://config1"])
    mock_async_run.assert_called_once()
    mock_save.assert_called_once()
    # Check args for save_results more specifically
    save_args, _ = mock_save.call_args
    assert save_args[0] == [("vmess://config1", 0.1)]
    assert save_args[1] is True  # sort is not args.no_sort
    assert save_args[2] == 0     # top_n
