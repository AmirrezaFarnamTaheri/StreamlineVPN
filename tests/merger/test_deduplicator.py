import unittest
import re
from unittest.mock import MagicMock
from streamline_vpn.merger.deduplicator import Deduplicator
from streamline_vpn.merger.result_processor import ConfigResult, EnhancedConfigProcessor, CONFIG

class TestDeduplicator(unittest.TestCase):
    def setUp(self):
        self.processor = MagicMock(spec=EnhancedConfigProcessor)
        self.deduplicator = Deduplicator(self.processor, [], [])

    def test_deduplicate_basic(self):
        config_results = [
            ConfigResult(config="config1", protocol="VMess"),
            ConfigResult(config="config2", protocol="VLESS"),
            ConfigResult(config="config1", protocol="VMess"),
        ]
        self.processor.create_semantic_hash.side_effect = ["hash1", "hash2", "hash1"]
        results = self.deduplicator.deduplicate(config_results)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].config, "config1")
        self.assertEqual(results[1].config, "config2")

    def test_deduplicate_with_include_protocol(self):
        CONFIG.include_protocols = ["VMESS"]
        config_results = [
            ConfigResult(config="config1", protocol="VMess"),
            ConfigResult(config="config2", protocol="VLESS"),
        ]
        self.processor.create_semantic_hash.side_effect = ["hash1", "hash2"]
        results = self.deduplicator.deduplicate(config_results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].protocol, "VMess")
        CONFIG.include_protocols = []

    def test_deduplicate_with_exclude_protocol(self):
        CONFIG.exclude_protocols = ["VLESS"]
        config_results = [
            ConfigResult(config="config1", protocol="VMess"),
            ConfigResult(config="config2", protocol="VLESS"),
        ]
        self.processor.create_semantic_hash.side_effect = ["hash1", "hash2"]
        results = self.deduplicator.deduplicate(config_results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].protocol, "VMess")
        CONFIG.exclude_protocols = []

    def test_deduplicate_with_include_country(self):
        CONFIG.include_countries = ["US"]
        config_results = [
            ConfigResult(config="config1", protocol="VMess", country="US"),
            ConfigResult(config="config2", protocol="VLESS", country="CA"),
        ]
        self.processor.create_semantic_hash.side_effect = ["hash1", "hash2"]
        results = self.deduplicator.deduplicate(config_results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].country, "US")
        CONFIG.include_countries = []

    def test_deduplicate_with_exclude_country(self):
        CONFIG.exclude_countries = ["CA"]
        config_results = [
            ConfigResult(config="config1", protocol="VMess", country="US"),
            ConfigResult(config="config2", protocol="VLESS", country="CA"),
        ]
        self.processor.create_semantic_hash.side_effect = ["hash1", "hash2"]
        results = self.deduplicator.deduplicate(config_results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].country, "US")
        CONFIG.exclude_countries = []

    def test_deduplicate_with_include_regex(self):
        self.deduplicator.include_regexes = [re.compile("fast")]
        config_results = [
            ConfigResult(config="config-fast", protocol="VMess"),
            ConfigResult(config="config-slow", protocol="VLESS"),
        ]
        self.processor.create_semantic_hash.side_effect = ["hash1", "hash2"]
        results = self.deduplicator.deduplicate(config_results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].config, "config-fast")
        self.deduplicator.include_regexes = []

    def test_deduplicate_with_exclude_regex(self):
        self.deduplicator.exclude_regexes = [re.compile("slow")]
        config_results = [
            ConfigResult(config="config-fast", protocol="VMess"),
            ConfigResult(config="config-slow", protocol="VLESS"),
        ]
        self.processor.create_semantic_hash.side_effect = ["hash1", "hash2"]
        results = self.deduplicator.deduplicate(config_results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].config, "config-fast")
        self.deduplicator.exclude_regexes = []

if __name__ == "__main__":
    unittest.main()
