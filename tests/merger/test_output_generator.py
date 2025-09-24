import unittest
import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from streamline_vpn.merger.output_generator import output_files, deduplicate_and_filter
from streamline_vpn.merger.config import Settings

class TestOutputGenerator(unittest.TestCase):
    def setUp(self):
        self.settings = Settings()

    @patch("streamline_vpn.merger.output_generator.is_valid_config", return_value=True)
    def test_deduplicate_and_filter_basic(self, mock_is_valid_config):
        config_set = {"vmess://config1", "vless://config2", "vmess://config1"}
        with patch("streamline_vpn.merger.output_generator.EnhancedConfigProcessor") as mock_processor:
            mock_processor.return_value.create_semantic_hash.side_effect = ["hash1", "hash2", "hash1"]
            results = deduplicate_and_filter(config_set, self.settings)
            self.assertEqual(len(results), 2)
            self.assertIn("vmess://config1", results)
            self.assertIn("vless://config2", results)

    @patch("streamline_vpn.merger.output_generator.is_valid_config", return_value=True)
    def test_deduplicate_and_filter_with_protocol_filter(self, mock_is_valid_config):
        config_set = {"vmess://config1", "vless://config2"}
        self.settings.protocols = ["vmess"]
        with patch("streamline_vpn.merger.output_generator.EnhancedConfigProcessor") as mock_processor:
            mock_processor.return_value.create_semantic_hash.side_effect = ["hash1", "hash2"]
            results = deduplicate_and_filter(config_set, self.settings)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0], "vmess://config1")
        self.settings.protocols = []

    @patch("streamline_vpn.merger.output_generator.is_valid_config", return_value=True)
    def test_deduplicate_and_filter_with_exclude_patterns(self, mock_is_valid_config):
        config_set = {"vmess://config-fast", "vless://config-slow"}
        self.settings.exclude_patterns = ["slow"]
        with patch("streamline_vpn.merger.output_generator.EnhancedConfigProcessor") as mock_processor:
            mock_processor.return_value.create_semantic_hash.side_effect = ["hash1", "hash2"]
            results = deduplicate_and_filter(config_set, self.settings)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0], "vmess://config-fast")
        self.settings.exclude_patterns = []

    @patch("streamline_vpn.merger.output_generator.is_valid_config", return_value=True)
    def test_deduplicate_and_filter_with_include_patterns(self, mock_is_valid_config):
        config_set = {"vmess://config-fast", "vless://config-slow"}
        self.settings.include_patterns = ["fast"]
        with patch("streamline_vpn.merger.output_generator.EnhancedConfigProcessor") as mock_processor:
            mock_processor.return_value.create_semantic_hash.side_effect = ["hash1", "hash2"]
            results = deduplicate_and_filter(config_set, self.settings)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0], "vmess://config-fast")
        self.settings.include_patterns = []

    @patch("pathlib.Path.replace")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.mkdir")
    def test_output_files_basic(self, mock_mkdir, mock_write_text, mock_replace):
        configs = ["vmess://config1", "vless://config2"]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            self.settings.write_base64 = True
            self.settings.write_singbox = True
            self.settings.write_clash = True
            with patch("streamline_vpn.merger.output_generator.config_to_clash_proxy") as mock_config_to_clash_proxy:
                mock_config_to_clash_proxy.return_value = {"name": "proxy"}
                output_files(configs, out_dir, self.settings)
                self.assertEqual(mock_write_text.call_count, 4)
                self.assertEqual(mock_replace.call_count, 4)

    @patch("pathlib.Path.replace")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.mkdir")
    def test_output_files_no_clash(self, mock_mkdir, mock_write_text, mock_replace):
        configs = ["vmess://config1", "vless://config2"]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            self.settings.write_base64 = True
            self.settings.write_singbox = True
            self.settings.write_clash = False
            output_files(configs, out_dir, self.settings)
            self.assertEqual(mock_write_text.call_count, 3)
            self.assertEqual(mock_replace.call_count, 3)

    @patch("pathlib.Path.replace")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.mkdir")
    def test_output_files_with_surge(self, mock_mkdir, mock_write_text, mock_replace):
        configs = ["vmess://config1"]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            self.settings.surge_file = "surge.conf"
            with patch("streamline_vpn.merger.output_generator.config_to_clash_proxy") as mock_config_to_clash_proxy, \
                 patch("streamline_vpn.merger.advanced_converters.generate_surge_conf") as mock_generate_surge_conf:
                mock_config_to_clash_proxy.return_value = {"name": "proxy"}
                output_files(configs, out_dir, self.settings)
                mock_generate_surge_conf.assert_called_once()
                self.assertEqual(mock_replace.call_args[0][0].name, "surge.conf")

    @patch("pathlib.Path.replace")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.mkdir")
    def test_output_files_with_qx(self, mock_mkdir, mock_write_text, mock_replace):
        configs = ["vmess://config1"]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            self.settings.qx_file = "qx.conf"
            with patch("streamline_vpn.merger.output_generator.config_to_clash_proxy") as mock_config_to_clash_proxy, \
                 patch("streamline_vpn.merger.advanced_converters.generate_qx_conf") as mock_generate_qx_conf:
                mock_config_to_clash_proxy.return_value = {"name": "proxy"}
                output_files(configs, out_dir, self.settings)
                mock_generate_qx_conf.assert_called_once()
                self.assertEqual(mock_replace.call_args[0][0].name, "qx.conf")

    @patch("pathlib.Path.replace")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.mkdir")
    def test_output_files_with_xyz(self, mock_mkdir, mock_write_text, mock_replace):
        configs = ["vmess://config1"]
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            self.settings.xyz_file = "xyz.txt"
            with patch("streamline_vpn.merger.output_generator.config_to_clash_proxy") as mock_config_to_clash_proxy:
                mock_config_to_clash_proxy.return_value = {"name": "proxy", "server": "server", "port": 123}
                output_files(configs, out_dir, self.settings)
                self.assertEqual(mock_replace.call_args[0][0].name, "xyz.txt")


if __name__ == "__main__":
    unittest.main()
