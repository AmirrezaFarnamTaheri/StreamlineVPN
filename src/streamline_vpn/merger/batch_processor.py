from .config import CONFIG


class BatchProcessor:
    """Handles processing and saving of results in batches."""

    def __init__(self, merger):
        self.merger = merger
        self.include_regexes = merger.deduplicator.include_regexes
        self.exclude_regexes = merger.deduplicator.exclude_regexes

    async def maybe_save_batch(self):
        """Save intermediate output based on batch settings."""
        merger = self.merger
        if CONFIG.save_every <= 0:
            return

        # Process new results since last call
        new_slice = merger.all_results[merger.last_processed_index :]
        merger.last_processed_index = len(merger.all_results)
        for r in new_slice:
            text = r.config.lower()
            if CONFIG.tls_fragment and CONFIG.tls_fragment.lower() not in text:
                continue
            if (
                CONFIG.include_protocols
                and r.protocol.upper() not in CONFIG.include_protocols
            ):
                continue
            if (
                CONFIG.exclude_protocols
                and r.protocol.upper() in CONFIG.exclude_protocols
            ):
                continue
            if self.exclude_regexes and any(
                rx.search(text) for rx in self.exclude_regexes
            ):
                continue
            if self.include_regexes and not any(
                rx.search(text) for rx in self.include_regexes
            ):
                continue
            if CONFIG.enable_url_testing and r.ping_time is None:
                continue
            h = merger.processor.create_semantic_hash(r.config)
            if h not in merger.saved_hashes:
                merger.saved_hashes.add(h)
                merger.cumulative_unique.append(r)

        if CONFIG.strict_batch:
            while (
                len(merger.cumulative_unique) - merger.last_saved_count
                >= CONFIG.save_every
            ):
                merger.batch_counter += 1
                if CONFIG.cumulative_batches:
                    batch_results = merger.cumulative_unique[:]
                else:
                    start = merger.last_saved_count
                    end = start + CONFIG.save_every
                    batch_results = merger.cumulative_unique[start:end]
                    merger.last_saved_count = end

                if CONFIG.enable_sorting:
                    batch_results = merger._sort_by_performance(batch_results)
                if CONFIG.top_n > 0:
                    batch_results = batch_results[: CONFIG.top_n]

                stats = merger.analyzer.analyze(
                    batch_results, merger.available_sources, len(merger.sources)
                )
                await merger._generate_comprehensive_outputs(
                    batch_results,
                    stats,
                    merger.start_time,
                    prefix=f"batch_{merger.batch_counter}_",
                )

                cumulative_stats = merger.analyzer.analyze(
                    merger.cumulative_unique,
                    merger.available_sources,
                    len(merger.sources),
                )
                await merger._generate_comprehensive_outputs(
                    merger.cumulative_unique,
                    cumulative_stats,
                    merger.start_time,
                    prefix="cumulative_",
                )
                if CONFIG.cumulative_batches:
                    merger.last_saved_count = len(merger.cumulative_unique)

                if (
                    CONFIG.stop_after_found > 0
                    and len(merger.cumulative_unique) >= CONFIG.stop_after_found
                ):
                    print(
                        f"\n⏹️  Threshold of {CONFIG.stop_after_found} configs reached. Stopping early."
                    )
                    merger.stop_fetching = True
                    break
        else:
            if len(merger.cumulative_unique) >= merger.next_batch_threshold:
                merger.batch_counter += 1
                if CONFIG.cumulative_batches:
                    batch_results = merger.cumulative_unique[:]
                else:
                    batch_results = merger.cumulative_unique[merger.last_saved_count :]
                    merger.last_saved_count = len(merger.cumulative_unique)

                if CONFIG.enable_sorting:
                    batch_results = merger._sort_by_performance(batch_results)
                if CONFIG.top_n > 0:
                    batch_results = batch_results[: CONFIG.top_n]

                stats = merger.analyzer.analyze(
                    batch_results, merger.available_sources, len(merger.sources)
                )
                await merger._generate_comprehensive_outputs(
                    batch_results,
                    stats,
                    merger.start_time,
                    prefix=f"batch_{merger.batch_counter}_",
                )

                cumulative_stats = merger.analyzer.analyze(
                    merger.cumulative_unique,
                    merger.available_sources,
                    len(merger.sources),
                )
                await merger._generate_comprehensive_outputs(
                    merger.cumulative_unique,
                    cumulative_stats,
                    merger.start_time,
                    prefix="cumulative_",
                )
                if CONFIG.cumulative_batches:
                    merger.last_saved_count = len(merger.cumulative_unique)

                merger.next_batch_threshold += CONFIG.save_every

                if (
                    CONFIG.stop_after_found > 0
                    and len(merger.cumulative_unique) >= CONFIG.stop_after_found
                ):
                    print(
                        f"\n⏹️  Threshold of {CONFIG.stop_after_found} configs reached. Stopping early."
                    )
                    merger.stop_fetching = True
