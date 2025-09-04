from __future__ import annotations

from pydantic import BaseModel, Field


class Node(BaseModel):
    proto: str
    host: str
    port: int
    name: str
    link: str
    uuid: str | None = None
    password: str | None = None
    params: dict = Field(default_factory=dict)
    latency_ms: int | None = None
    healthy: bool | None = None
    score: float | None = None
    last_checked: float | None = None

    def key(self) -> str:
        token = self.uuid or self.password or self.name
        return f"{self.proto}|{self.host}|{self.port}|{token}"


class IngestBody(BaseModel):
    links: list[str] = Field(default_factory=list)


class SourcesBody(BaseModel):
    urls: list[str] = Field(default_factory=list)


