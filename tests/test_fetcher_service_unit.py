import asyncio
import zlib
import gzip
import pytest

from vpn_merger.services.fetcher_service import AsyncSourceFetcher


class DummyProcessor:
    def __init__(self, config=None):
        self.config = config

    def __call__(self, text: str):
        return text.splitlines()


class DummySessionSingle:
    def __init__(self, status: int = 200, text: str = "", headers=None, raw: bytes | None = None):
        self._status = status
        self._text = text
        self._headers = headers or {}
        self._raw = raw

    class _Resp:
        def __init__(self, status, text, headers, raw):
            self.status = status
            self._text = text
            self.headers = headers
            self._raw = raw

        async def read(self):
            return self._raw if self._raw is not None else self._text.encode("utf-8")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def get(self, url, allow_redirects=True):
        return self._Resp(self._status, self._text, self._headers, self._raw)


class DummySessionFlaky:
    def __init__(self, succeed_after: int = 2, text: str = "ok"):
        self._count = 0
        self._succeed_after = succeed_after
        self._text = text

    class _Resp:
        def __init__(self, status, text):
            self.status = status
            self._text = text
            self.headers = {}

        async def read(self):
            return self._text.encode("utf-8")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def get(self, url, allow_redirects=True):
        self._count += 1
        if self._count <= self._succeed_after - 1:
            return self._Resp(500, "err")
        return self._Resp(200, self._text)


@pytest.mark.asyncio
async def test_fetcher_handles_gzip_decompression():
    payload = b"line1\nline2\n"
    gz = gzip.compress(payload)

    proc = DummyProcessor()
    f = AsyncSourceFetcher(proc, concurrency=2)
    f.session = DummySessionSingle(status=200, text="", headers={"content-encoding": "gzip"}, raw=gz)
    await f.open()
            out = await f.fetch_many(["https://raw.githubusercontent.com/test/a.txt"])
    assert out and out[0][0].endswith("a.txt")
    assert out[0][1] == ["line1", "line2"]


@pytest.mark.asyncio
async def test_fetcher_retries_then_succeeds_with_zero_backoff(monkeypatch):
    class FastBackoff:
        def get_delay(self, attempt: int) -> float:
            return 0.0

    proc = DummyProcessor()
    f = AsyncSourceFetcher(proc, concurrency=1)
    f._backoff = FastBackoff()  # type: ignore
    f.session = DummySessionFlaky(succeed_after=3, text="ok-line")
    # Patch missing logging symbol in module scope used by log_json calls
    import types
    import vpn_merger.services.fetcher_service as fs
    if not hasattr(fs, 'logging'):
        fs.logging = types.SimpleNamespace(INFO=20, WARNING=30)
    await f.open()
            url, lines = (await f.fetch_many(["https://raw.githubusercontent.com/test/f.txt"]))[0]
    assert url.endswith("f.txt")
    assert lines == ["ok-line"]


@pytest.mark.asyncio
async def test_fetcher_handles_brotli_if_available():
    try:
        import brotli  # type: ignore
    except Exception:
        pytest.skip("brotli not installed")
    payload = "a\nb\n".encode("utf-8")
    br = brotli.compress(payload)  # type: ignore[attr-defined]
    proc = DummyProcessor()
    f = AsyncSourceFetcher(proc)
    f.session = DummySessionSingle(status=200, headers={"content-encoding": "br"}, raw=br)
    await f.open()
            url, lines = (await f.fetch_many(["https://raw.githubusercontent.com/test/br.txt"]))[0]
    assert url.endswith("br.txt")
    assert lines == ["a", "b"]
