"""Local server: the explorer page plus one JSON endpoint that derives a root's forms on demand."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, override
from urllib.parse import unquote, urlsplit

from panini.lexicon import ROOTS
from panini.site.build import DEFAULT_STYLE_DIR, page_html, root_derivations, site_data


def _handler(page: bytes) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, status: int, obj: dict[str, Any]) -> None:
            self._send(
                status,
                json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8",
            )

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/":
                self._send(200, page, "text/html; charset=utf-8")
            elif path.startswith("/api/root/"):
                code = unquote(path.removeprefix("/api/root/"))
                if code in ROOTS:
                    self._json(200, {"derivations": root_derivations(code)})
                else:
                    self._json(404, {"error": f"unknown root {code!r}"})
            else:
                self._json(404, {"error": "not found"})

        def do_HEAD(self) -> None:
            self.do_GET()  # same status and headers; _send leaves out the body

        @override
        def log_message(self, format: str, *args: Any) -> None:
            pass

    return Handler


def make_server(
    host: str = "127.0.0.1", port: int = 0, style_dir: Path | None = None
) -> ThreadingHTTPServer:
    """A server bound to `host:port` (port 0: any free one). The page is built once, here."""
    if style_dir is None:
        style_dir = Path(os.environ.get("PANINI_STYLE_DIR", DEFAULT_STYLE_DIR))
    data = {**site_data([], embed_all_roots=True), "source": "server"}
    return ThreadingHTTPServer(
        (host, port), _handler(page_html(data, style_dir).encode("utf-8"))
    )
