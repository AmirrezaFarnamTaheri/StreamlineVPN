from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter


def build_graphql_router() -> Optional[APIRouter]:
    """Return a GraphQL router if strawberry is installed; otherwise None.

    Schema exposes minimal fields: stats, outputs (paths), and sources count.
    """
    try:
        import strawberry  # type: ignore
        from strawberry.fastapi import GraphQLRouter  # type: ignore
    except Exception:
        return None

    @strawberry.type
    class OutputPaths:
        raw: str
        base64: str
        csv: str
        report: str
        singbox: str

    @strawberry.type
    class Stats:
        total_configs: int
        reachable_configs: int
        total_sources: int

    @strawberry.type
    class Durations:
        total_s: Optional[float]
        discover_s: Optional[float]
        validate_s: Optional[float]
        fetch_s: Optional[float]
        output_s: Optional[float]

    @strawberry.type
    class Run:
        run_id: str
        ts: float
        total_configs: int
        reachable: int
        sources: int
        durations: Optional[Durations]

    @strawberry.type
    class PageInfo:
        nextCursor: Optional[float]
        hasMore: bool
        count: int

    @strawberry.type
    class RunsPage:
        items: List[Run]
        pageInfo: PageInfo

    @strawberry.type
    class EventData:
        run_id: Optional[str]
        accepted: Optional[int]
        count: Optional[int]
        sources: Optional[int]
        lines: Optional[int]
        unique: Optional[int]
        path: Optional[str]
        duration_s: Optional[float]

    @strawberry.type
    class EventItem:
        type: str
        ts: float
        data: Optional[EventData]

    @strawberry.type
    class EventsPage:
        items: List[EventItem]
        pageInfo: PageInfo

    @strawberry.type
    class Query:
        @strawberry.field
        def outputs(self) -> OutputPaths:
            from pathlib import Path
            base = Path('output')
            return OutputPaths(
                raw=str(base / 'vpn_subscription_raw.txt'),
                base64=str(base / 'vpn_subscription_base64.txt'),
                csv=str(base / 'vpn_detailed.csv'),
                report=str(base / 'vpn_report.json'),
                singbox=str(base / 'vpn_singbox.json'),
            )

        @strawberry.field
        def stats(self) -> Stats:
            # Lightweight reader from the JSON report
            import json
            from pathlib import Path
            report = Path('output') / 'vpn_report.json'
            try:
                data = json.loads(report.read_text(encoding='utf-8'))
                s = data.get('statistics', {})
                cats = data.get('source_categories', {})
                return Stats(
                    total_configs=int(s.get('total_configs', 0)),
                    reachable_configs=int(s.get('reachable_configs', 0)),
                    total_sources=int(cats.get('total_unique_sources', 0)),
                )
            except Exception:
                return Stats(total_configs=0, reachable_configs=0, total_sources=0)

        @strawberry.field
        def discover(self, limit: int = 50) -> List[str]:
            import asyncio
            try:
                from vpn_merger.sources.discovery import discover_all  # type: ignore
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(discover_all(limit=limit))
            except Exception:
                return []

        @strawberry.field
        def runs(self, limit: int = 50, afterTs: Optional[float] = None) -> List[Run]:
            try:
                from vpn_merger.monitoring.run_store import tail_runs, runs_after  # type: ignore
                out: List[Run] = []
                rows = runs_after(afterTs, limit) if afterTs else tail_runs(limit)
                for r in rows:
                    d = r.get('durations') or {}
                    out.append(Run(
                        run_id=str(r.get('run_id', '')),
                        ts=float(r.get('ts', 0.0)),
                        total_configs=int(r.get('total_configs', 0)),
                        reachable=int(r.get('reachable', 0)),
                        sources=int(r.get('sources', 0)),
                        durations=Durations(
                            total_s=d.get('total_s'),
                            discover_s=d.get('discover_s'),
                            validate_s=d.get('validate_s'),
                            fetch_s=d.get('fetch_s'),
                            output_s=d.get('output_s'),
                        ),
                    ))
                return out
            except Exception:
                return []

        @strawberry.field
        def events(self, limit: int = 100, type: Optional[str] = None, afterTs: Optional[float] = None) -> List[EventItem]:
            try:
                from vpn_merger.monitoring.event_store import tail_events, events_after  # type: ignore
                evs = events_after(afterTs, limit, type) if (afterTs or type) else tail_events(limit)
                out: List[EventItem] = []
                for e in evs:
                    et = str(e.get('type', ''))
                    ts = float(e.get('ts', 0.0))
                    data = e.get('data') or {}
                    out.append(EventItem(
                        type=et,
                        ts=ts,
                        data=EventData(
                            run_id=data.get('run_id'),
                            accepted=data.get('accepted'),
                            count=data.get('count'),
                            sources=data.get('sources'),
                            lines=data.get('lines'),
                            unique=data.get('unique'),
                            path=data.get('path'),
                            duration_s=data.get('duration_s'),
                        )
                    ))
                return out
            except Exception:
                return []

        @strawberry.field
        def runsPage(self, limit: int = 50, afterTs: Optional[float] = None) -> RunsPage:
            items = self.runs(limit=limit, afterTs=afterTs)
            next_cursor = items[-1].ts if items else None
            has_more = len(items) == limit
            return RunsPage(items=items, pageInfo=PageInfo(nextCursor=next_cursor, hasMore=has_more, count=len(items)))

        @strawberry.field
        def eventsPage(self, limit: int = 100, type: Optional[str] = None, afterTs: Optional[float] = None) -> EventsPage:
            items = self.events(limit=limit, type=type, afterTs=afterTs)
            next_cursor = items[-1].ts if items else None
            has_more = len(items) == limit
            return EventsPage(items=items, pageInfo=PageInfo(nextCursor=next_cursor, hasMore=has_more, count=len(items)))

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        async def run_merge(self, formats: Optional[List[str]] = None, limit: Optional[int] = None) -> str:
            try:
                from vpn_merger.core.merger import Merger  # type: ignore
                m = Merger()
                if limit:
                    try:
                        m.sources = m.sources[: int(limit)]
                    except Exception:
                        pass
                await m.run(formats=set([f.lower() for f in formats]) if formats else None)
                return "ok"
            except Exception as e:
                return f"error: {e}"

        @strawberry.mutation
        def format(self, type: str, lines: List[str]) -> str:
            t = type.lower()
            if t == "base64":
                from vpn_merger.output.formatters.base64 import to_base64
                return to_base64(lines)
            if t == "clash":
                from vpn_merger.output.formatters.clash import to_clash_yaml
                return to_clash_yaml(lines)
            if t == "singbox":
                from vpn_merger.output.formatters.singbox import to_singbox_json
                return to_singbox_json(lines)
            if t == "csv":
                from vpn_merger.output.formatters.csv import to_csv
                return to_csv(lines)
            return "\n".join(lines)

    schema = strawberry.Schema(Query, Mutation)
    return GraphQLRouter(schema, path='/graphql')


def get_router() -> APIRouter:
    r = build_graphql_router()
    if r is not None:
        return r
    router = APIRouter()

    @router.get('/graphql')
    def info() -> Dict[str, str]:
        return {"message": "Install 'strawberry-graphql' to enable GraphQL endpoint"}

    return router
