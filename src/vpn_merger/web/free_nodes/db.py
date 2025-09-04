from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DB_URL

# Ensure data directory exists before creating engine (important for tests)
try:
    os.makedirs("./data", exist_ok=True)
except Exception:
    pass

Base = declarative_base()
engine = create_async_engine(DB_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class NodeModel(Base):
    __tablename__ = "nodes"
    id = Column(Integer, primary_key=True)
    key = Column(String(256), unique=True, index=True)  # proto|host|port|token
    proto = Column(String(16), index=True)
    host = Column(String(255), index=True)
    port = Column(Integer, index=True)
    name = Column(String(255))
    link = Column(Text)
    uuid = Column(String(64), nullable=True)
    password = Column(String(256), nullable=True)
    params_json = Column(Text, default="{}")
    latency_ms = Column(Integer, nullable=True)
    healthy = Column(Boolean, nullable=True)
    score = Column(Float, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SourceModel(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True)
    url = Column(String(1024), unique=True, index=True)
    added_at = Column(DateTime, default=datetime.utcnow)


class NodeMetrics(Base):
    __tablename__ = "node_metrics"
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), unique=True, index=True)
    region = Column(String(128), nullable=True)  # e.g., US-West, EU, Asia
    latency_ms = Column(Integer, nullable=True)
    throughput_mbps = Column(Float, nullable=True)
    packet_loss = Column(Float, nullable=True)  # 0.0 - 1.0
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


_SCHEMA_READY = False


async def ensure_schema() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    _SCHEMA_READY = True


