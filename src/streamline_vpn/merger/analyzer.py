from typing import List, Dict

from .result_processor import ConfigResult


class Analyzer:
    """Handles analysis of config results."""

    def analyze(
        self,
        results: List[ConfigResult],
        available_sources: List[str],
        total_sources: int,
    ) -> Dict:
        """Analyze results and generate comprehensive statistics."""
        protocol_stats: Dict[str, int] = {}
        performance_stats: Dict[str, List[float]] = {}

        for result in results:
            # Protocol count
            protocol_stats[result.protocol] = protocol_stats.get(result.protocol, 0) + 1

            # Performance stats
            if result.ping_time is not None:
                if result.protocol not in performance_stats:
                    performance_stats[result.protocol] = []
                performance_stats[result.protocol].append(result.ping_time)

        # Calculate performance metrics
        perf_summary = {}
        for protocol, times in performance_stats.items():
            if times:
                perf_summary[protocol] = {
                    "count": len(times),
                    "avg_ms": round(sum(times) / len(times) * 1000, 2),
                    "min_ms": round(min(times) * 1000, 2),
                    "max_ms": round(max(times) * 1000, 2),
                }

        # Print comprehensive breakdown
        total = len(results)
        reachable = sum(1 for r in results if r.is_reachable)

        print(f"   📊 Total configs: {total:,}")
        reach_pct = (reachable / total * 100) if total else 0
        print(f"   🌐 Reachable configs: {reachable:,} ({reach_pct:.1f}%)")
        print(f"   🔗 Available sources: {len(available_sources)}")
        print("   📋 Protocol breakdown:")

        for protocol, count in sorted(
            protocol_stats.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total) * 100 if total else 0
            perf_info = ""
            if protocol in perf_summary:
                avg_ms = perf_summary[protocol]["avg_ms"]
                perf_info = f" | Avg: {avg_ms}ms"
            print(
                f"      {protocol:12} {count:>7,} configs ({percentage:5.1f}%){perf_info}"
            )

        return {
            "protocol_stats": protocol_stats,
            "performance_stats": perf_summary,
            "total_configs": total,
            "reachable_configs": reachable,
            "available_sources": len(available_sources),
            "total_sources": total_sources,
        }
