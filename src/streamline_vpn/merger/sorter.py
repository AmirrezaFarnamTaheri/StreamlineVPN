from typing import List, Dict, Tuple, cast
from tqdm import tqdm

from .result_processor import ConfigResult, EnhancedConfigProcessor, CONFIG


class Sorter:
    """Handles sorting of config results."""

    def __init__(self, processor: EnhancedConfigProcessor, proxy_history: Dict):
        self.processor = processor
        self.proxy_history = proxy_history

    def sort_by_performance(
        self, results: List[ConfigResult], progress: tqdm
    ) -> List[ConfigResult]:
        """Sort results by connection performance and protocol preference."""
        # Protocol priority ranking
        protocol_priority = {
            "VLESS": 1,
            "VMess": 2,
            "Reality": 3,
            "Hysteria2": 4,
            "Trojan": 5,
            "Shadowsocks": 6,
            "TUIC": 7,
            "Hysteria": 8,
            "Naive": 9,
            "Juicity": 10,
            "WireGuard": 11,
            "Other": 12,
        }

        def sort_key_latency(result: ConfigResult) -> Tuple:
            is_reachable = 1 if result.is_reachable else 0
            ping_time = (
                result.ping_time if result.ping_time is not None else float("inf")
            )
            protocol_rank = protocol_priority.get(result.protocol, 13)
            return (-is_reachable, ping_time, protocol_rank)

        def sort_key_reliability(result: ConfigResult) -> Tuple:
            h = self.processor.create_semantic_hash(result.config)
            hist = self.proxy_history.get(h, {})
            total = hist.get("total_checks", 0)
            success = hist.get("successful_checks", 0)
            reliability = success / total if total else 0
            ping_time = (
                result.ping_time if result.ping_time is not None else float("inf")
            )
            protocol_rank = protocol_priority.get(result.protocol, 13)
            return (-reliability, ping_time, protocol_rank)

        key_func = (
            sort_key_latency
            if CONFIG.sort_by != "reliability"
            else sort_key_reliability
        )

        keyed = []
        for r in results:
            keyed.append((key_func(r), r))
            progress.update(1)
            progress.set_postfix(
                processed=progress.n,
                remaining=progress.total - progress.n,
                refresh=False,
            )

        sorted_results = [r for _, r in sorted(keyed, key=lambda x: x[0])]

        if CONFIG.sort_by == "reliability":
            print("   🚀 Sorted by reliability")
        reachable_count = sum(1 for r in results if r.is_reachable)
        print(f"   🚀 Sorted: {reachable_count:,} reachable configs first")

        if reachable_count > 0:
            fastest = min(
                (r for r in results if r.ping_time is not None),
                key=lambda x: cast(float, x.ping_time),
                default=None,
            )
            if fastest and fastest.ping_time is not None:
                print(
                    f"   ⚡ Fastest server: {fastest.ping_time * 1000:.1f}ms ({fastest.protocol})"
                )
        return sorted_results
