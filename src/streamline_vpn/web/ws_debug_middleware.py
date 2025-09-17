from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from ..utils.logging import get_logger


logger = get_logger(__name__)


class WSLogMiddleware:
    """ASGI middleware that logs WebSocket handshake and lifecycle events.

    This middleware logs incoming WebSocket scopes (path, headers, client), and
    intercepts send() messages to record when the application accepts or closes
    the connection during the handshake. It helps diagnose 403 rejections that
    happen before route handlers run.
    """

    def __init__(self, app: Callable[..., Awaitable[None]]):
        self.app = app

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:  # type: ignore[override]
        if scope.get("type") != "websocket":
            await self.app(scope, receive, send)
            return

        path = scope.get("path")
        client = scope.get("client")
        scheme = scope.get("scheme")
        headers = {}
        try:
            headers = {
                k.decode("latin-1"): v.decode("latin-1")
                for k, v in scope.get("headers", [])
            }
        except Exception:
            pass

        line = (
            f"[WS] Incoming handshake path={path} scheme={scheme} client={client} "
            f"headers={json.dumps(headers, ensure_ascii=False)}"
        )
        logger.debug(
            "[WS] Incoming handshake path=%s scheme=%s client=%s headers=%s",
            path,
            scheme,
            client,
            json.dumps(headers, ensure_ascii=False),
        )
        try:
            root = Path(__file__).resolve().parents[3]
            (root / "logs").mkdir(parents=True, exist_ok=True)
            with open(root / "logs" / "ws_scopes.log", "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

        async def send_wrapper(message: Dict[str, Any]) -> None:
            mtype = message.get("type")
            line2 = None
            if mtype == "websocket.accept":
                line2 = f"[WS] Accepted path={path} subprotocol={message.get('subprotocol')}"
                logger.debug(
                    "[WS] Accepted path=%s subprotocol=%s",
                    path,
                    message.get("subprotocol"),
                )
            elif mtype == "websocket.close":
                line2 = f"[WS] Closed path={path} code={message.get('code')}"
                logger.debug(
                    "[WS] Closed (pre-accept or app-close) path=%s code=%s",
                    path,
                    message.get("code"),
                )
            elif mtype == "websocket.http.response.start":
                line2 = f"[WS] HTTP response start path={path} status={message.get('status')}"
                logger.debug(
                    "[WS] HTTP response start during handshake path=%s status=%s",
                    path,
                    message.get("status"),
                )
            if line2:
                try:
                    root = Path(__file__).resolve().parents[3]
                    (root / "logs").mkdir(parents=True, exist_ok=True)
                    with open(
                        root / "logs" / "ws_scopes.log", "a", encoding="utf-8"
                    ) as f:
                        f.write(line2 + "\n")
                except Exception:
                    pass
            await send(message)

        await self.app(scope, receive, send_wrapper)
