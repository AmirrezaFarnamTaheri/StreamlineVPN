import asyncio
import pytest

from streamline_vpn.core.merger_processor import MergerProcessor
from streamline_vpn.models.configuration import VPNConfiguration, Protocol


class FakeFetchResult:
    def __init__(self, success: bool, configs, response_time=0.01):
        self.success = success
        self.configs = configs
        self.response_time = response_time


class FakeSourceManager:
    def __init__(self):
        self.updates = []

    async def fetch_source(self, source):
        return FakeFetchResult(True, ["safe://good", "unsafe://bad", "parse://oops"])

    async def update_source_performance(self, **kwargs):
        self.updates.append(kwargs)


class FakeSecurityManager:
    def analyze_configuration(self, line: str):
        return {"is_safe": not line.startswith("unsafe://")}


class FakeParser:
    def parse_configuration(self, line: str):
        if line.startswith("parse://"):
            return None  # simulate parse failure
        return VPNConfiguration(server="s", port=1, protocol=Protocol.VMESS, metadata={})


class FakeConfigProcessor:
    def __init__(self):
        self.parser = FakeParser()

    def deduplicate_configurations(self, configs):
        # Trivial pass-through
        return configs


class FakeMerger:
    def __init__(self):
        self.max_concurrent = 5
        self.source_manager = FakeSourceManager()
        self.security_manager = FakeSecurityManager()
        self.config_processor = FakeConfigProcessor()
        self.ml_predictor = None
        self.geo_optimizer = None


@pytest.mark.asyncio
async def test_process_single_source_parses_and_updates():
    """
    Tests that the processor correctly parses configs and ignores parse failures.
    Security filtering is no longer the responsibility of the processor.
    """
    m = FakeMerger()
    proc = MergerProcessor(m)
    configs, success = await proc._process_single_source("http://test-server.example/list.txt")
    # "safe" and "unsafe" are parsed. "parse" fails. Expect 2 configs.
    assert len(configs) == 2
    assert success is True
    # update_source_performance called at least once for success
    assert any(u.get("success") is True for u in m.source_manager.updates)


@pytest.mark.asyncio
async def test_process_sources_aggregates():
    """
    Tests that the processor aggregates results from multiple sources correctly.
    """
    m = FakeMerger()
    proc = MergerProcessor(m)
    # Each source provides 2 valid configs. 2 sources * 2 configs = 4.
    configs, success_count = await proc.process_sources(["s1", "s2"])
    assert len(configs) == 4
    assert success_count == 2


@pytest.mark.asyncio
async def test_process_source_handles_fetch_failure_and_exception(monkeypatch):
    m = FakeMerger()

    # Case 1: fetch result indicates failure
    async def _fail_fetch(source):
        return FakeFetchResult(False, [], 0.0)

    m.source_manager.fetch_source = _fail_fetch
    proc = MergerProcessor(m)
    out, success = await proc._process_single_source("s")
    assert out == []
    assert success is False
    assert any(u.get("success") is False for u in m.source_manager.updates)

    # Case 2: fetch raises exception
    async def _raise_fetch(source):
        raise RuntimeError("boom")

    m2 = FakeMerger()
    m2.source_manager.fetch_source = _raise_fetch
    proc2 = MergerProcessor(m2)
    out2, success2 = await proc2._process_single_source("s")
    assert out2 == []
    assert success2 is False
    assert any(u.get("success") is False for u in m2.source_manager.updates)


@pytest.mark.asyncio
async def test_apply_enhancements_handles_optional_components():
    m = FakeMerger()

    class BadPredictor:
        async def predict_and_sort(self, cfgs):
            raise RuntimeError("ml fail")

    class Geo:
        async def optimize_configurations(self, cfgs):
            return cfgs

    m.ml_predictor = BadPredictor()
    m.geo_optimizer = Geo()
    proc = MergerProcessor(m)

    res = await proc.apply_enhancements([
        VPNConfiguration(server="x", port=1, protocol=Protocol.VMESS, metadata={})
    ])
    # returns original list even if predictor fails
    assert isinstance(res, list) and len(res) == 1


@pytest.mark.asyncio
async def test_apply_enhancements_success_paths_and_dedup():
    m = FakeMerger()

    class GoodPredictor:
        async def predict_and_sort(self, cfgs):
            return list(cfgs)

    class Geo:
        async def optimize_configurations(self, cfgs):
            return cfgs

    m.ml_predictor = GoodPredictor()
    m.geo_optimizer = Geo()
    proc = MergerProcessor(m)

    cfgs = [VPNConfiguration(server="x", port=1, protocol=Protocol.VMESS, metadata={})]
    res = await proc.apply_enhancements(cfgs)
    assert res and isinstance(res, list)

    # Dedup path
    deduped = await proc.deduplicate_configurations(cfgs)
    assert isinstance(deduped, list)


@pytest.mark.asyncio
async def test_process_single_source_parse_exception_branch():
    class RaisingParser:
        def parse_configuration(self, line: str):
            if line.startswith("boom://"):
                raise ValueError("bad line")
            return VPNConfiguration(server="s", port=2, protocol=Protocol.VMESS, metadata={})

    class CP:
        def __init__(self):
            self.parser = RaisingParser()
        def deduplicate_configurations(self, cfgs):
            return cfgs

    class SM(FakeSourceManager):
        async def fetch_source(self, source):
            return FakeFetchResult(True, ["boom://err", "safe://ok"], 0.0)

    m = FakeMerger()
    m.source_manager = SM()
    m.config_processor = CP()
    proc = MergerProcessor(m)
    configs, success = await proc._process_single_source("s")
    # One parse raises, the other succeeds
    assert len(configs) == 1
    assert success is True


@pytest.mark.asyncio
async def test_update_source_performance_failure_paths():
    # Case A: fetch failure then update performance raises -> covers lines 91-92
    class SM1(FakeSourceManager):
        async def fetch_source(self, source):
            return FakeFetchResult(False, [], 0.0)
        async def update_source_performance(self, **kwargs):
            raise RuntimeError("perf")

    m1 = FakeMerger()
    m1.source_manager = SM1()
    proc1 = MergerProcessor(m1)
    assert await proc1._process_single_source("s") == ([], False)

    # Case B: success path but performance update raises -> covers lines 125-126
    class SM2(FakeSourceManager):
        async def fetch_source(self, source):
            return FakeFetchResult(True, ["safe://ok"], 0.01)
        async def update_source_performance(self, **kwargs):
            raise RuntimeError("perf2")

    m2 = FakeMerger()
    m2.source_manager = SM2()
    proc2 = MergerProcessor(m2)
    # Parsing succeeds, then update perf raises internally but method returns configs
    configs, success = await proc2._process_single_source("s")
    assert len(configs) == 1
    assert success is True

    # Case C: outer exception then update performance raises -> covers lines 142-143
    class SM3(FakeSourceManager):
        async def fetch_source(self, source):
            raise RuntimeError("boom")
        async def update_source_performance(self, **kwargs):
            raise RuntimeError("perf3")

    m3 = FakeMerger()
    m3.source_manager = SM3()
    proc3 = MergerProcessor(m3)
    assert await proc3._process_single_source("s") == ([], False)


@pytest.mark.asyncio
async def test_geo_optimizer_exception_path():
    class BadGeo:
        async def optimize_configurations(self, cfgs):
            raise RuntimeError("geo fail")

    m = FakeMerger()
    m.geo_optimizer = BadGeo()
    proc = MergerProcessor(m)
    res = await proc.apply_enhancements([
        VPNConfiguration(server="x", port=1, protocol=Protocol.VMESS, metadata={})
    ])
    assert isinstance(res, list)
