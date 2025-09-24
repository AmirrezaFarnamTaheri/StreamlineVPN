import unittest
from unittest.mock import MagicMock
from streamline_vpn.merger.sorter import Sorter
from streamline_vpn.merger.result_processor import ConfigResult, EnhancedConfigProcessor, CONFIG

class TestSorter(unittest.TestCase):
    def setUp(self):
        self.processor = MagicMock(spec=EnhancedConfigProcessor)
        self.proxy_history = {}
        self.sorter = Sorter(self.processor, self.proxy_history)
        self.progress = MagicMock()

    def test_sort_by_latency(self):
        CONFIG.sort_by = "latency"
        config_results = [
            ConfigResult(config="config1", protocol="VMess", ping_time=0.2, is_reachable=True),
            ConfigResult(config="config2", protocol="VLESS", ping_time=0.1, is_reachable=True),
            ConfigResult(config="config3", protocol="Trojan", is_reachable=False),
        ]
        results = self.sorter.sort_by_performance(config_results, self.progress)
        self.assertEqual(results[0].config, "config2")
        self.assertEqual(results[1].config, "config1")
        self.assertEqual(results[2].config, "config3")

    def test_sort_by_reliability(self):
        CONFIG.sort_by = "reliability"
        self.processor.create_semantic_hash.side_effect = ["hash1", "hash2", "hash3"]
        self.proxy_history = {
            "hash1": {"total_checks": 10, "successful_checks": 5},
            "hash2": {"total_checks": 10, "successful_checks": 8},
            "hash3": {"total_checks": 10, "successful_checks": 2},
        }
        self.sorter.proxy_history = self.proxy_history
        config_results = [
            ConfigResult(config="config1", protocol="VMess", is_reachable=True),
            ConfigResult(config="config2", protocol="VLESS", is_reachable=True),
            ConfigResult(config="config3", protocol="Trojan", is_reachable=True),
        ]
        results = self.sorter.sort_by_performance(config_results, self.progress)
        self.assertEqual(results[0].config, "config2")
        self.assertEqual(results[1].config, "config1")
        self.assertEqual(results[2].config, "config3")

    def test_sort_empty(self):
        results = self.sorter.sort_by_performance([], self.progress)
        self.assertEqual(len(results), 0)

    def test_sort_no_reachable(self):
        config_results = [
            ConfigResult(config="config1", protocol="VMess", is_reachable=False),
            ConfigResult(config="config2", protocol="VLESS", is_reachable=False),
        ]
        results = self.sorter.sort_by_performance(config_results, self.progress)
        self.assertEqual(len(results), 2)

if __name__ == "__main__":
    unittest.main()
