from typing import Tuple, List, Optional


class AsyncSourceFetcher:
    """Async HTTP fetcher placeholder to be wired with real impl.

    Maintain method signatures used by the monolith so we can swap
    imports incrementally.
    """

    def __init__(self, processor):
        self.processor = processor
        self.session = None

    async def open(self):
        return self

    async def close(self):
        pass

    async def _fetch_url(self, url: str) -> Tuple[str, List]:
        return url, []


