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

    schema = strawberry.Schema(Query)
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

