import re
from typing import List, Set

from .result_processor import ConfigResult, EnhancedConfigProcessor, CONFIG


class Deduplicator:
    """Handles deduplication of config results."""

    def __init__(
        self,
        processor: EnhancedConfigProcessor,
        include_regexes: List[re.Pattern],
        exclude_regexes: List[re.Pattern],
    ):
        self.processor = processor
        self.include_regexes = include_regexes
        self.exclude_regexes = exclude_regexes

    def deduplicate(self, results: List[ConfigResult]) -> List[ConfigResult]:
        """Efficient deduplication of config results using semantic hashing."""
        seen_hashes: Set[str] = set()
        unique_results: List[ConfigResult] = []

        for result in results:
            text = result.config.lower()
            if CONFIG.tls_fragment and CONFIG.tls_fragment.lower() not in text:
                continue
            if (
                CONFIG.include_protocols
                and result.protocol.upper() not in CONFIG.include_protocols
            ):
                continue
            if (
                CONFIG.exclude_protocols
                and result.protocol.upper() in CONFIG.exclude_protocols
            ):
                continue
            if CONFIG.include_countries and result.country:
                if result.country.upper() not in CONFIG.include_countries:
                    continue
            if CONFIG.exclude_countries and result.country:
                if result.country.upper() in CONFIG.exclude_countries:
                    continue
            if self.exclude_regexes and any(
                r.search(text) for r in self.exclude_regexes
            ):
                continue
            if self.include_regexes and not any(
                r.search(text) for r in self.include_regexes
            ):
                continue
            config_hash = self.processor.create_semantic_hash(result.config)
            if config_hash not in seen_hashes:
                seen_hashes.add(config_hash)
                unique_results.append(result)

        duplicates = len(results) - len(unique_results)
        print(f"   🗑️ Duplicates removed: {duplicates:,}")
        if len(results) > 0:
            efficiency = duplicates / len(results) * 100
        else:
            efficiency = 0
        print(f"   📊 Deduplication efficiency: {efficiency:.1f}%")
        return unique_results
