import unittest
from streamline_vpn.merger.analyzer import Analyzer
from streamline_vpn.merger.result_processor import ConfigResult

class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = Analyzer()

    def test_analyze_empty(self):
        results = self.analyzer.analyze([], [], 0)
        self.assertEqual(results["total_configs"], 0)
        self.assertEqual(results["reachable_configs"], 0)
        self.assertEqual(results["available_sources"], 0)
        self.assertEqual(results["total_sources"], 0)
        self.assertEqual(results["protocol_stats"], {})
        self.assertEqual(results["performance_stats"], {})

    def test_analyze_basic(self):
        config_results = [
            ConfigResult(config="config1", protocol="VMess", ping_time=0.1, is_reachable=True),
            ConfigResult(config="config2", protocol="VLESS", ping_time=0.2, is_reachable=True),
            ConfigResult(config="config3", protocol="VMess", ping_time=0.3, is_reachable=True),
            ConfigResult(config="config4", protocol="Trojan", is_reachable=False),
        ]
        results = self.analyzer.analyze(config_results, ["source1", "source2"], 3)
        self.assertEqual(results["total_configs"], 4)
        self.assertEqual(results["reachable_configs"], 3)
        self.assertEqual(results["available_sources"], 2)
        self.assertEqual(results["total_sources"], 3)
        self.assertEqual(results["protocol_stats"], {"VMess": 2, "VLESS": 1, "Trojan": 1})
        self.assertEqual(results["performance_stats"]["VMess"]["count"], 2)
        self.assertAlmostEqual(results["performance_stats"]["VMess"]["avg_ms"], 200.0)
        self.assertAlmostEqual(results["performance_stats"]["VLESS"]["avg_ms"], 200.0)
        self.assertNotIn("Trojan", results["performance_stats"])

    def test_analyze_no_performance_data(self):
        config_results = [
            ConfigResult(config="config1", protocol="VMess", is_reachable=True),
            ConfigResult(config="config2", protocol="VLESS", is_reachable=True),
        ]
        results = self.analyzer.analyze(config_results, ["source1"], 1)
        self.assertEqual(results["total_configs"], 2)
        self.assertEqual(results["reachable_configs"], 2)
        self.assertEqual(results["protocol_stats"], {"VMess": 1, "VLESS": 1})
        self.assertEqual(results["performance_stats"], {})

    def test_analyze_no_reachable_configs(self):
        config_results = [
            ConfigResult(config="config1", protocol="VMess", is_reachable=False),
            ConfigResult(config="config2", protocol="VLESS", is_reachable=False),
        ]
        results = self.analyzer.analyze(config_results, ["source1"], 1)
        self.assertEqual(results["total_configs"], 2)
        self.assertEqual(results["reachable_configs"], 0)
        self.assertEqual(results["protocol_stats"], {"VMess": 1, "VLESS": 1})
        self.assertEqual(results["performance_stats"], {})

if __name__ == "__main__":
    unittest.main()
