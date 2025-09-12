"""Run Unified API with WebSocket debug instrumentation.

Usage:
  python run_ws_debug.py [--host 0.0.0.0] [--port 8080] [--ws websockets|wsproto] [--disable-cors]

This starts the Unified API with:
  - log level DEBUG
  - WS backend selection (websockets or wsproto)
  - WS handshake middleware logging
  - File logging to logs/ws_debug.log
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import uvicorn
import importlib
import sys


def _patch_uvicorn_websockets():
    """Monkey-patch Uvicorn websockets protocol to log and allow all paths.

    Adds a permissive process_request and logs ws_handler path to help diagnose
    pre-route handshake rejections (HTTP 403).
    """
    try:
        wimpl = importlib.import_module('uvicorn.protocols.websockets.websockets_impl')
    except Exception:
        return
    WebSocketProtocol = getattr(wimpl, 'WebSocketProtocol', None)
    if WebSocketProtocol is None:
        return

    # Attach permissive process_request if not present
    if not hasattr(WebSocketProtocol, 'process_request'):
        def process_request(self, path, request_headers):  # type: ignore[unused-argument]
            logging.getLogger('uvicorn.error').debug('[WS-mp] process_request path=%s headers=%s', path, dict(request_headers))
            return None  # Allow handshake to proceed
        setattr(WebSocketProtocol, 'process_request', process_request)

    # Wrap ws_handler to add debug
    if hasattr(WebSocketProtocol, 'ws_handler'):
        _orig_ws_handler = WebSocketProtocol.ws_handler

        async def ws_handler(self, path):  # type: ignore[override]
            logging.getLogger('uvicorn.error').debug('[WS-mp] ws_handler path=%s', path)
            return await _orig_ws_handler(self, path)

        setattr(WebSocketProtocol, 'ws_handler', ws_handler)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--ws", choices=["auto", "websockets", "wsproto"], default="auto")
    parser.add_argument("--disable-cors", action="store_true", help="Disable CORS middleware to isolate WS issues")
    args = parser.parse_args()

    # Ensure logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging to file + console
    logfile = logs_dir / "ws_debug.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.FileHandler(logfile, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # Apply monkey patch before server start
    _patch_uvicorn_websockets()

    # Optional: disable app CORS for isolation
    if args.disable_cors:
        import os
        os.environ["DISABLE_CORS"] = "1"

    ws_impl = None if args.ws == "auto" else args.ws

    app_dir = str((Path(__file__).parent / "src").resolve())
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    config = uvicorn.Config(
        app="streamline_vpn.web.unified_api:app",
        host=args.host,
        port=args.port,
        ws=ws_impl,
        log_level="debug",
        reload=False,
    )
    server = uvicorn.Server(config)
    print(f"Starting WS debug server on {args.host}:{args.port} ws={args.ws} logs={logfile}")
    server.run()


if __name__ == "__main__":
    main()
