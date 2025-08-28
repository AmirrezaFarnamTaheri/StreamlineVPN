from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, List, Dict, Optional


class ConfigFetcher(Protocol):
    async def fetch(self, url: str) -> List[str]: ...


class ConfigParser(Protocol):
    def parse(self, raw: str) -> Optional[Dict]: ...


class ConfigTester(Protocol):
    async def test(self, host: str, port: int) -> float: ...


class ConfigScorer(Protocol):
    def score(self, config: Dict, test_result: float) -> float: ...


class ServiceContainer:
    """Lightweight dependency registry for modular composition."""

    def __init__(self):
        self._services: Dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get(self, name: str) -> Any:
        if name not in self._services:
            raise KeyError(f"Service {name} not registered")
        return self._services[name]

