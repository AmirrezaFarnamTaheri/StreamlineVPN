import unittest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from streamline_vpn.merger.output_writer import build_html_report, generate_comprehensive_outputs, upload_files_to_gist, write_upload_links
from streamline_vpn.merger.result_processor import ConfigResult
from streamline_vpn.merger.config import Settings

class TestOutputWriter(unittest.TestCase):
    def test_build_html_report(self):
        config_results = [
            ConfigResult(config="config1", protocol="VMess", host="server1", ping_time=0.1, country="US"),
            ConfigResult(config="config2", protocol="VLESS", host="server2", ping_time=0.2, country="CA"),
        ]
        html = build_html_report(config_results)
        self.assertIn("VMess", html)
        self.assertIn("server1", html)
        self.assertIn("100.0", html)
        self.assertIn("US", html)
        self.assertIn("VLESS", html)
        self.assertIn("server2", html)
        self.assertIn("200.0", html)
        self.assertIn("CA", html)

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.replace")
    @patch("streamline_vpn.merger.output_writer.results_to_clash_yaml")
    @patch("streamline_vpn.merger.output_writer.config_to_clash_proxy")
    def test_generate_comprehensive_outputs(self, mock_config_to_clash_proxy, mock_results_to_clash_yaml, mock_replace, mock_write_text, mock_mkdir):
        merger = MagicMock()
        merger.sources = ["source1"]
        merger._parse_extra_params.return_value = {}
        config_results = [ConfigResult(config="config1", protocol="VMess")]
        stats = {}
        start_time = 0.0
        CONFIG = Settings()
        CONFIG.write_base64 = True
        CONFIG.write_csv = True
        CONFIG.write_html = True
        CONFIG.write_clash = True
        CONFIG.write_clash_proxies = True

        async def run_test():
            await generate_comprehensive_outputs(merger, config_results, stats, start_time)

        asyncio.run(run_test())
        self.assertEqual(mock_write_text.call_count, 7)

    @patch("aiohttp.ClientSession")
    def test_upload_files_to_gist(self, mock_session):
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value.json = AsyncMock(return_value={"files": {"test.txt": {"raw_url": "http://example.com"}}})
        paths = [Path("test.txt")]
        with patch("pathlib.Path.read_text", return_value="test content"):
            async def run_test():
                links = await upload_files_to_gist(paths, "token")
                self.assertEqual(links, {"test.txt": "http://example.com"})
            asyncio.run(run_test())

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.replace")
    def test_write_upload_links(self, mock_replace, mock_write_text, mock_mkdir):
        links = {"test.txt": "http://example.com"}
        output_dir = Path("/tmp/output")
        write_upload_links(links, output_dir)
        mock_write_text.assert_called_once_with("test.txt: http://example.com", encoding="utf-8")

if __name__ == "__main__":
    unittest.main()
