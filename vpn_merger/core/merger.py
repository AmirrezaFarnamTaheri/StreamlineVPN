from __future__ import annotations

"""Adapter exposing a compact merger API.

This delegates to the existing UltimateVPNMerger in the legacy module to
avoid large code moves while providing a stable import path.
"""

from typing import List, Iterable, Tuple, Optional, Set, Dict

from .deduplicator import Deduplicator
from .scorer import QualityScorer  # type: ignore
from ..output.writer import atomic_write_async  # type: ignore
from ..output.formatters.base64 import to_base64  # type: ignore
from ..output.formatters.csv import to_csv  # type: ignore
from ..output.formatters.singbox import to_singbox_json  # type: ignore
from ..output.formatters.clash import to_clash_yaml  # type: ignore
from pathlib import Path
from ..testing.connection import quick_ping  # type: ignore


def _safe_list(x: Iterable[str]) -> List[str]:
    return [s for s in x if isinstance(s, str) and s.strip()]


class Merger:
    def __init__(self):
        # Try to bind to the legacy implementation for source storage; fall back to a stub
        try:
            from .. import vpn_merger as _root  # type: ignore
            self._root = _root
            self._impl = _root.UltimateVPNMerger()
        except Exception:
            self._root = None
            class _Stub:
                def __init__(self):
                    self.sources: List[str] = []
                    self.config = None
            self._impl = _Stub()
        self._dedupe = Deduplicator()

    # ----------------------- Source Validation -----------------------
    async def validate_sources(self, urls: List[str], min_score: float = 0.5, timeout: int = 12) -> List[Tuple[str, float]]:
        try:
            from vpn_merger.sources.validator import SourceValidator  # type: ignore
        except Exception:
            return [(u, 0.0) for u in urls]
        sv = SourceValidator()
        out: List[Tuple[str, float]] = []

        import asyncio

        import asyncio as _aio
        sem = _aio.Semaphore(50)

        async def _run(u: str):
            try:
                async with sem:
                    r = await sv.validate_source(u, timeout=timeout)
                s = float(r.get("reliability_score") or 0.0)
                if s >= min_score:
                    out.append((u, s))
            except Exception:
                pass

        await asyncio.gather(*[_run(u) for u in urls])
        out.sort(key=lambda t: t[1], reverse=True)
        return out

    # ----------------------- Deduplicate -----------------------------
    def deduplicate(self, lines: Iterable[str]) -> List[str]:
        return self._dedupe.unique(_safe_list(lines))

    # ----------------------- Scoring ---------------------------------
    def score_and_sort(self, lines: Iterable[str]) -> List[str]:
        items = _safe_list(lines)
        try:
            scorer = QualityScorer()  # type: ignore
        except Exception:
            return items
        scored = []
        for s in items:
            try:
                scored.append((scorer.score_line(s), s))  # type: ignore[attr-defined]
            except Exception:
                scored.append((0.0, s))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [s for _, s in scored]

    @property
    def sources(self) -> List[str]:  # pragma: no cover - trivial delegate
        return self._impl.sources

    @sources.setter
    def sources(self, v: List[str]) -> None:  # pragma: no cover
        self._impl.sources = v

    async def run(self, formats: Optional[Set[str]] = None, output_dir: Optional[Path | str] = None) -> None:
        # Run start event
        import time as _t
        run_id = f"run-{int(_t.time())}"
        # Initialize tracing and metrics (best-effort)
        self.tracing = None
        self.mc = None
        try:
            from ..monitoring.tracing_enhanced import TracingService  # type: ignore
            self.tracing = TracingService()
        except Exception:
            self.tracing = None
        try:
            from ..monitoring.metrics_collector import MetricsCollector  # type: ignore
            self.mc = MetricsCollector()
        except Exception:
            self.mc = None
        try:
            from ..core.events import Event, EventType  # type: ignore
            if self.event_bus:
                await self.event_bus.publish(Event(type=EventType.RUN_START, data={"run_id": run_id}, timestamp=_t.time()))
        except Exception:
            pass
        # Optional event bus and metrics integration
        try:
            from ..core.events import EventBus  # type: ignore
            self.event_bus = EventBus()
            import asyncio as _aio
            _aio.create_task(self.event_bus.start())
        except Exception:
            self.event_bus = None
        try:
            from ..monitoring.metrics import VPNMergerMetrics  # type: ignore
            from ..monitoring.metrics_subscribers import attach as attach_metrics  # type: ignore
            self.metrics = VPNMergerMetrics(port=8001)
            if self.event_bus is not None:
                attach_metrics(self.event_bus, self.metrics)
        except Exception:
            self.metrics = None
        # Attach persistent event logger
        try:
            from ..monitoring.event_store import append_event  # type: ignore
            from ..core.events import EventType, Event  # type: ignore
            import time as _t

            async def _persist(ev: Event):
                append_event({"type": ev.type.value, "data": ev.data, "ts": ev.timestamp})

            if self.event_bus is not None:
                for et in (
                    EventType.DISCOVER_START,
                    EventType.DISCOVER_DONE,
                    EventType.VALIDATE_START,
                    EventType.VALIDATE_DONE,
                    EventType.FETCH_START,
                    EventType.FETCH_DONE,
                    EventType.DEDUP_DONE,
                    EventType.OUTPUT_WRITTEN,
                ):
                    self.event_bus.subscribe(et, _persist)
            # Metrics + tracing subscribers
            async def _observe(ev: Event):
                try:
                    # Tracing span per event
                    if getattr(self, 'tracing', None) is not None:
                        try:
                            from ..monitoring.tracing_enhanced import TracingService  # type: ignore
                            tracer = self.tracing.tracer  # type: ignore[attr-defined]
                            with tracer.start_as_current_span(f"event.{ev.type.value}") as span:  # type: ignore
                                if isinstance(ev.data, dict):
                                    for k, v in ev.data.items():
                                        try:
                                            span.set_attribute(f"event.{k}", v)
                                        except Exception:
                                            pass
                        except Exception:
                            pass
                    # Metrics stage durations
                    if getattr(self, 'mc', None) is not None and isinstance(ev.data, dict):
                        dur = ev.data.get('duration_s')
                        if dur is not None:
                            try:
                                stage = ev.type.value
                                self.mc.processing_duration.labels(stage=stage).observe(float(dur))  # type: ignore[attr-defined]
                            except Exception:
                                pass
                except Exception:
                    pass

            if self.event_bus is not None:
                for et in (
                    EventType.DISCOVER_DONE,
                    EventType.VALIDATE_DONE,
                    EventType.FETCH_DONE,
                    EventType.OUTPUT_WRITTEN,
                    EventType.RUN_START,
                    EventType.RUN_DONE,
                ):
                    self.event_bus.subscribe(et, _observe)
        except Exception:
            pass
        # Standalone light-weight run that mirrors the legacy outputs
        import asyncio
        from ..services.fetcher_service import AsyncSourceFetcher  # type: ignore
        from ..sources.discovery import discover_all  # type: ignore

        # Read config knobs if available
        try:
            config = getattr(self._impl, 'config', None)
        except Exception:
            config = None

        # Determine sources
        try:
            from .. import vpn_merger as _root  # type: ignore
            base_sources: List[str] = list(_root.UnifiedSources.get_all_sources())
        except Exception:
            base_sources = []
        # Prefer explicitly provided sources when available
        try:
            user_sources = list(self.sources)
            if user_sources:
                base_sources = user_sources
        except Exception:
            pass

        total_start = _t.time()
        # Optional discovery
        enable_disc = True
        try:
            # Prefer new Pydantic config
            enable_disc = bool(getattr(getattr(config, 'discovery', None), 'enable', True))
        except Exception:
            pass
        # CI/test override via environment to avoid long external calls
        try:
            import os as _os
            if _os.environ.get('CI') or _os.environ.get('SKIP_DISCOVERY'):
                enable_disc = False
        except Exception:
            pass
        if enable_disc:
            disc_t0 = _t.time()
            # emit discover start
            try:
                from ..core.events import Event, EventType  # type: ignore
                import time as _t
                if self.event_bus:
                    await self.event_bus.publish(Event(type=EventType.DISCOVER_START, data={}, timestamp=_t.time()))
            except Exception:
                pass
            try:
                disc = await discover_all(limit=200)
                base_sources = list(dict.fromkeys(base_sources + disc))
            except Exception:
                pass
            # discover done
            try:
                from ..core.events import Event, EventType  # type: ignore
                import time as _t
                if self.event_bus:
                    await self.event_bus.publish(Event(type=EventType.DISCOVER_DONE, data={"count": len(base_sources), "duration_s": round(_t.time() - disc_t0, 3)}, timestamp=_t.time()))
            except Exception:
                pass

        # Optional: load URL weights/thresholds from production YAML
        def _load_url_meta() -> Dict[str, Tuple[float, Optional[float]]]:
            meta: Dict[str, Tuple[float, Optional[float]]] = {}
            try:
                import yaml  # type: ignore
                from pathlib import Path as _P
                prod = _P('config') / 'sources.production.yaml'
                if not prod.exists():
                    return meta
                data = yaml.safe_load(prod.read_text(encoding='utf-8')) or {}

                def _walk(obj, inherited_weight: float = 1.0, min_score_override: Optional[float] = None):
                    if isinstance(obj, dict):
                        w = obj.get('weight', inherited_weight)
                        try:
                            w = float(w)
                        except Exception:
                            w = inherited_weight
                        mso = obj.get('min_score', min_score_override)
                        try:
                            mso = float(mso) if mso is not None else min_score_override
                        except Exception:
                            mso = min_score_override
                        if 'url' in obj and isinstance(obj['url'], str):
                            meta[obj['url']] = (float(w), mso)
                        for v in obj.values():
                            _walk(v, float(w), mso)
                    elif isinstance(obj, list):
                        for it in obj:
                            _walk(it, inherited_weight, min_score_override)

                _walk(data)
            except Exception:
                return meta
            return meta

        url_meta = _load_url_meta()

        # Gate by reliability score
        min_score = 0.5
        timeout = 12
        try:
            min_score = float(getattr(getattr(config, 'discovery', None), 'min_score', 0.5))
            timeout = int(getattr(getattr(config, 'discovery', None), 'timeout', 12))
        except Exception:
            pass
        try:
            from ..core.events import Event, EventType  # type: ignore
            import time as _t
            if self.event_bus:
                val_t0 = _t.time()
                await self.event_bus.publish(Event(type=EventType.VALIDATE_START, data={"count": len(base_sources)}, timestamp=val_t0))
        except Exception:
            val_t0 = _t.time()
        # Metrics + tracing for validate
        _val_cm = self.mc.time_stage('validate') if self.mc else None
        try:
            if self.tracing:
                async with self.tracing.trace("validate", {"run_id": run_id, "count": len(base_sources)}):
                    valid_pairs = await self.validate_sources(base_sources, min_score=0.0, timeout=timeout)
            else:
                valid_pairs = await self.validate_sources(base_sources, min_score=0.0, timeout=timeout)
        finally:
            try:
                if _val_cm:
                    _val_cm.__exit__(None, None, None)
            except Exception:
                pass
        # Apply per-URL override thresholds and weight-based prioritization
        filtered_pairs: List[Tuple[str, float]] = []
        for u, s in valid_pairs:
            ow = url_meta.get(u, (1.0, None))
            mso = ow[1]
            th = float(mso) if mso is not None else float(min_score)
            if s >= th:
                filtered_pairs.append((u, s * float(ow[0])))
        filtered_pairs.sort(key=lambda t: t[1], reverse=True)
        sources = [u for (u, _ws) in filtered_pairs] or base_sources
        try:
            from ..core.events import Event, EventType  # type: ignore
            import time as _t
            if self.event_bus:
                await self.event_bus.publish(Event(type=EventType.VALIDATE_DONE, data={"accepted": len(sources), "duration_s": round(_t.time() - val_t0, 3)}, timestamp=_t.time()))
        except Exception:
            pass

        # Helper: filter by protocol prefixes
        def _filter_lines(lines: Iterable[str]) -> List[str]:
            prefs: Set[str] = {
                "vmess://", "vless://", "trojan://", "ss://", "ssr://",
                "hysteria://", "hysteria2://", "tuic://", "wireguard://",
            }
            out: List[str] = []
            for ln in lines:
                s = (ln or '').strip()
                if not s:
                    continue
                for p in prefs:
                    if s.startswith(p):
                        out.append(s)
                        break
            return out

        # Fetch
        fetcher = AsyncSourceFetcher(lambda text: _filter_lines(text.splitlines()), concurrency=12)
        await fetcher.open()
        try:
            from ..core.events import Event, EventType  # type: ignore
            import time as _t
            if self.event_bus:
                fetch_t0 = _t.time()
                await self.event_bus.publish(Event(type=EventType.FETCH_START, data={"sources": len(sources)}, timestamp=fetch_t0))
        except Exception:
            fetch_t0 = _t.time()
        # Throttled progress events during fetch
        try:
            from ..core.events import Event, EventType  # type: ignore
            import time as _t
            last_emit = 0.0

            async def _progress(done: int, total: int):
                nonlocal last_emit
                now = _t.time()
                if (now - last_emit) >= 1.0 or done == total:
                    last_emit = now
                    if self.event_bus:
                        await self.event_bus.publish(Event(type=EventType.FETCH_PROGRESS, data={"done": done, "total": total}, timestamp=now))

            # Metrics + tracing for fetch
            _fetch_cm = self.mc.time_stage('fetch') if self.mc else None
            try:
                if self.tracing:
                    async with self.tracing.trace("fetch", {"run_id": run_id, "sources": len(sources)}):
                        results = await fetcher.fetch_many(sources[:200], progress_cb=_progress)
                else:
                    results = await fetcher.fetch_many(sources[:200], progress_cb=_progress)
            finally:
                try:
                    if _fetch_cm:
                        _fetch_cm.__exit__(None, None, None)
                except Exception:
                    pass
        except Exception:
            # Fallback without progress
            try:
                results = await fetcher.fetch_many(sources[:200])
            except Exception:
                results = []
        finally:
            try:
                await fetcher.close()
            except Exception:
                pass
        try:
            from ..core.events import Event, EventType  # type: ignore
            import time as _t
            if self.event_bus:
                total_lines = sum(len(lines) for _u, lines in results)
                await self.event_bus.publish(Event(type=EventType.FETCH_DONE, data={"sources": len(results), "lines": total_lines, "duration_s": round(_t.time() - fetch_t0, 3)}, timestamp=_t.time()))
        except Exception:
            pass

        # Merge lines, keep source mapping
        from ..processing.parser import ProtocolParser  # type: ignore
        from .processor import ConfigResult  # type: ignore
        all_items: List[ConfigResult] = []
        for url, lines in results:
            for line in lines:
                proto = ProtocolParser.categorize(line)
                host, port = ProtocolParser.extract_endpoint(line)
                all_items.append(ConfigResult(config=line, protocol=proto, host=host, port=port, source_url=url))
        # Deduplicate, then optional score-sort
        seen: Set[str] = set()
        dedup_items: List[ConfigResult] = []
        for it in all_items:
            if it.config not in seen:
                seen.add(it.config)
                dedup_items.append(it)
        try:
            from ..core.events import Event, EventType  # type: ignore
            import time as _t
            if self.event_bus:
                dedup_t = _t.time()
                await self.event_bus.publish(Event(type=EventType.DEDUP_DONE, data={"unique": len(dedup_items)}, timestamp=dedup_t))
        except Exception:
            pass
        try:
            from .. import vpn_merger as _root  # type: ignore
            do_sort = bool(getattr(_root.CONFIG, 'enable_sorting', True))
        except Exception:
            do_sort = True
        final_lines = [it.config for it in dedup_items]
        if do_sort:
            _score_cm = self.mc.time_stage('score') if self.mc else None
            try:
                if self.tracing:
                    async with self.tracing.trace("score", {"run_id": run_id, "items": len(final_lines)}):
                        final_lines = self.score_and_sort(final_lines)
                else:
                    final_lines = self.score_and_sort(final_lines)
            finally:
                try:
                    if _score_cm:
                        _score_cm.__exit__(None, None, None)
                except Exception:
                    pass

        # Optional connection testing to enrich CSV
        try:
            from .. import vpn_merger as _root  # type: ignore
            disable_all = bool(getattr(getattr(getattr(self._impl, 'config', None), 'testing', None), 'disable_all_tests', False))
            do_test = bool(getattr(_root.CONFIG, 'enable_url_testing', True)) and not disable_all
            max_ping_ms = int(getattr(_root.CONFIG, 'max_ping_ms', 1000))
            test_timeout = float(getattr(_root.CONFIG, 'test_timeout', 5.0))
        except Exception:
            do_test, max_ping_ms, test_timeout = True, 1000, 5.0
        # Honour CI/network-skipping env flags
        try:
            import os as _os
            if _os.environ.get('CI') or _os.environ.get('SKIP_NETWORK'):
                do_test = False
        except Exception:
            pass
        if do_test:
            # Unique endpoints to probe
            endpoints: List[Tuple[str, int, str]] = []
            for it in dedup_items:
                if it.host and it.port:
                    endpoints.append((it.host, int(it.port), it.protocol))
            # Deduplicate
            seen_ep: Set[Tuple[str, int, str]] = set()
            uniq: List[Tuple[str, int, str]] = []
            for ep in endpoints:
                if ep not in seen_ep:
                    seen_ep.add(ep)
                    uniq.append(ep)
            # Per-protocol concurrency + timeout
            try:
                from .. import vpn_merger as _root  # type: ignore
                proto_cc = dict(getattr(getattr(_root.CONFIG, 'testing', None), 'protocol_concurrency', {}) or {})
                proto_to = dict(getattr(getattr(_root.CONFIG, 'testing', None), 'protocol_timeouts', {}) or {})
            except Exception:
                proto_cc, proto_to = {}, {}
            import asyncio
            semaphores: Dict[str, asyncio.Semaphore] = {}
            def _sem_for(proto: str) -> asyncio.Semaphore:
                key = proto.lower()
                if key not in semaphores:
                    semaphores[key] = asyncio.Semaphore(int(proto_cc.get(key, 50)))
                return semaphores[key]
            results_map: Dict[Tuple[str, int, str], Optional[float]] = {}

            async def probe(ep: Tuple[str, int, str]):
                h, p, proto = ep
                sem = _sem_for(proto)
                async with sem:
                    tout = float(proto_to.get(proto.lower(), test_timeout))
                    try:
                        t = await asyncio.wait_for(quick_ping(h, p, timeout=tout), timeout=tout + 0.5)
                    except Exception:
                        t = None
                    results_map[ep] = t

            await asyncio.gather(*[probe(ep) for ep in uniq])
            # Assign results back to items
            for it in dedup_items:
                if it.host and it.port:
                    t = results_map.get((it.host, int(it.port), it.protocol))
                    it.ping_time = t
                    it.is_reachable = t is not None and (t * 1000.0 <= max_ping_ms)
                    try:
                        if self.mc and t is not None:
                            self.mc.record_latency(it.protocol.lower(), t * 1000.0)
                        if self.mc:
                            self.mc.record_config(it.protocol.lower(), 'reachable' if it.is_reachable else 'unreachable')
                    except Exception:
                        pass

        # TLS handshake + app tests if requested
        do_full = False
        app_tests: Optional[List[str]] = None
        try:
            from .. import vpn_merger as _root  # type: ignore
            disable_all = bool(getattr(getattr(getattr(self._impl, 'config', None), 'testing', None), 'disable_all_tests', False))
            do_full = bool(getattr(_root.CONFIG, 'full_test', False)) and not disable_all
            app_tests = getattr(_root.CONFIG, 'app_tests', None)
            if app_tests:
                app_tests = [str(x) for x in app_tests]
                if disable_all:
                    app_tests = None
        except Exception:
            do_full = False
            app_tests = None

        if do_full or app_tests:
            from ..services.testing_service import TestingService  # type: ignore
            ts = TestingService(timeout=test_timeout, concurrency=50)
            import asyncio as _aio
            # Handshake tests for TLS-like endpoints
            if do_full:
                tls_like = {"vmess", "vless", "trojan", "reality", "xray"}
                eps = [(it.host, int(it.port), it.protocol) for it in dedup_items if it.host and it.port and it.protocol.lower() in tls_like]
                # Dedup endpoints
                eps_d: List[Tuple[str, int, str]] = []
                seen_ep2: Set[Tuple[str, int, str]] = set()
                for ep in eps:
                    if ep not in seen_ep2:
                        seen_ep2.add(ep)
                        eps_d.append(ep)
                hs_map: Dict[Tuple[str, int, str], Optional[bool]] = {}
                async def _hs(ep: Tuple[str, int, str]):
                    h, p, _pr = ep
                    hs_ok = await ts.tls_handshake(h, p)
                    hs_map[ep] = hs_ok
                await _aio.gather(*[_hs(ep) for ep in eps_d])
                for it in dedup_items:
                    if it.host and it.port and (it.host, int(it.port), it.protocol) in hs_map:
                        it.handshake_ok = bool(hs_map[(it.host, int(it.port), it.protocol)])

            # App tests
            if app_tests:
                # If tunnel tests are enabled, attempt per-config tunnel for a small sample
                enable_tunnel = False
                try:
                    from .. import vpn_merger as _root  # type: ignore
                    enable_tunnel = bool(getattr(getattr(_root.CONFIG, 'testing', None), 'enable_tunnel_tests', False))
                except Exception:
                    enable_tunnel = False
                if enable_tunnel:
                    # Test first N configs per protocol to keep runtime bounded
                    MAX_TUNNELS = 5
                    tested: int = 0
                    preferred_runner = "auto"
                    try:
                        from .. import vpn_merger as _root  # type: ignore
                        preferred_runner = str(getattr(getattr(_root.CONFIG, 'testing', None), 'tunnel_runner', 'auto'))
                    except Exception:
                        preferred_runner = "auto"
                    for it in dedup_items:
                        if tested >= MAX_TUNNELS:
                            break
                        try:
                            # Run tunnel tests using the concrete config line
                            suite = await ts.test_via_tunnel(it.config, app_tests, timeout=test_timeout, preferred=preferred_runner)
                            it.app_test_results = suite
                            tested += 1
                        except Exception:
                            continue
                else:
                    # Fallback: direct app suite
                    suite = await ts.app_suite(app_tests)
                    for it in dedup_items:
                        it.app_test_results = {k: suite.get(k, False) for k in app_tests}

        # Output directory
        outdir = Path(str(output_dir)) if output_dir is not None else Path('output')
        if output_dir is None:
            try:
                from .. import vpn_merger as _root  # type: ignore
                outdir = Path(str(_root.CONFIG.output_dir))
            except Exception:
                pass
        outdir.mkdir(parents=True, exist_ok=True)

        # Write outputs (raw, base64, csv with metrics, singbox, clash)
        selected = set(formats) if formats else {"raw", "base64", "csv", "singbox", "clash"}
        _out_cm = self.mc.time_stage('output') if self.mc else None
        if "raw" in selected:
            path = outdir / 'vpn_subscription_raw.txt'
            await atomic_write_async(path, '\n'.join(final_lines))
            try:
                from ..core.events import Event, EventType  # type: ignore
                import time as _t
                if self.event_bus:
                    await self.event_bus.publish(Event(type=EventType.OUTPUT_WRITTEN, data={"path": str(path)}, timestamp=_t.time()))
            except Exception:
                pass
        if "base64" in selected:
            path = outdir / 'vpn_subscription_base64.txt'
            await atomic_write_async(path, to_base64(final_lines))
            try:
                from ..core.events import Event, EventType  # type: ignore
                import time as _t
                if self.event_bus:
                    await self.event_bus.publish(Event(type=EventType.OUTPUT_WRITTEN, data={"path": str(path)}, timestamp=_t.time()))
            except Exception:
                pass
        if "csv" in selected:
            # Enhanced CSV with metrics-like columns
            import csv, io
            buf = io.StringIO()
            writer = csv.writer(buf)
            headers = ['Config', 'Protocol', 'Host', 'Port', 'Ping_MS', 'Reachable', 'Source']
            if do_full:
                headers.append('Handshake')
            if app_tests:
                for name in app_tests:
                    headers.append(f"{name.capitalize()}_OK")
            writer.writerow(headers)
            # Build quick map from config to first item to preserve order
            first_map: Dict[str, ConfigResult] = {}
            for it in dedup_items:
                if it.config not in first_map:
                    first_map[it.config] = it
            for cfg in final_lines:
                it = first_map.get(cfg)
                if it is None:
                    continue
                ping_ms = round(it.ping_time * 1000.0, 2) if it.ping_time else None
                # Heuristic handshake_ok if full_test requested: reachable and TLS-like proto
                handshake_ok: Optional[bool] = None
                if do_full:
                    tls_like = str(it.protocol).lower() in {"vmess", "vless", "trojan", "reality", "xray"}
                    handshake_ok = bool(it.is_reachable) if tls_like else None
                    it.handshake_ok = handshake_ok
                row = [it.config, it.protocol, it.host, it.port, ping_ms, bool(it.is_reachable), it.source_url]
                if do_full:
                    row.append('OK' if handshake_ok else ('' if handshake_ok is None else 'FAIL'))
                if app_tests:
                    for name in app_tests:
                        val = (it.app_test_results or {}).get(name)
                        row.append('' if val is None else ('OK' if val else 'FAIL'))
                writer.writerow(row)
            path = outdir / 'vpn_detailed.csv'
            await atomic_write_async(path, buf.getvalue())
            try:
                from ..core.events import Event, EventType  # type: ignore
                import time as _t
                if self.event_bus:
                    await self.event_bus.publish(Event(type=EventType.OUTPUT_WRITTEN, data={"path": str(path)}, timestamp=_t.time()))
            except Exception:
                pass
        if "singbox" in selected:
            path = outdir / 'vpn_singbox.json'
            await atomic_write_async(path, to_singbox_json(final_lines))
            try:
                from ..core.events import Event, EventType  # type: ignore
                import time as _t
                if self.event_bus:
                    await self.event_bus.publish(Event(type=EventType.OUTPUT_WRITTEN, data={"path": str(path)}, timestamp=_t.time()))
            except Exception:
                pass
        output_t0 = _t.time()
        if "clash" in selected:
            try:
                path = outdir / 'clash.yaml'
                await atomic_write_async(path, to_clash_yaml(final_lines))
                try:
                    from ..core.events import Event, EventType  # type: ignore
                    import time as _t
                    if self.event_bus:
                        await self.event_bus.publish(Event(type=EventType.OUTPUT_WRITTEN, data={"path": str(path)}, timestamp=_t.time()))
                except Exception:
                    pass
            except Exception:
                pass
        try:
            if _out_cm:
                _out_cm.__exit__(None, None, None)
        except Exception:
            pass

        # Run done: persist a compact summary
        try:
            from ..monitoring.run_store import append_run  # type: ignore
            reachable = sum(1 for it in dedup_items if it.is_reachable)
            append_run({
                "run_id": run_id,
                "ts": _t.time(),
                "total_configs": len(final_lines),
                "reachable": reachable,
                "sources": len(sources),
                "durations": {
                    "total_s": round(_t.time() - total_start, 3),
                    "discover_s": round((_t.time() - disc_t0), 3) if enable_disc else None,
                    "validate_s": round((_t.time() - val_t0), 3) if 'val_t0' in locals() else None,
                    "fetch_s": round((_t.time() - fetch_t0), 3) if 'fetch_t0' in locals() else None,
                    "output_s": round((_t.time() - output_t0), 3) if 'output_t0' in locals() else None,
                },
            })
        except Exception:
            pass
        try:
            from ..core.events import Event, EventType  # type: ignore
            if self.event_bus:
                await self.event_bus.publish(Event(type=EventType.RUN_DONE, data={"run_id": run_id, "total": len(final_lines)}, timestamp=_t.time()))
        except Exception:
            pass
        # Throttled progress events during fetch
        try:
            from ..core.events import Event, EventType  # type: ignore
            import time as _t
            last_emit = 0.0

            async def _progress(done: int, total: int):
                nonlocal last_emit
                now = _t.time()
                if (now - last_emit) >= 1.0 or done == total:
                    last_emit = now
                    if self.event_bus:
                        await self.event_bus.publish(Event(type=EventType.FETCH_PROGRESS, data={"done": done, "total": total}, timestamp=now))

            results = await fetcher.fetch_many(sources[:200], progress_cb=_progress)
        except Exception:
            # fallback already executed above if needed
            pass
