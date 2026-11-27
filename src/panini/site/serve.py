"""Local server: the explorer page plus one JSON endpoint that derives a root's forms on demand."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, override
from urllib.parse import unquote, urlsplit

from panini.lexicon import ROOTS
from panini.rule_catalog import build_catalog
from panini.site.build import (
    page_html,
    root_derivations,
    rule_assets,
    site_data,
    stylesheet,
)
from panini.site.rules import INDEX_PAGE, RULES_DIR, rule_links

_RULE_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}


def _handler(pages: dict[str, tuple[bytes, str]]) -> type[BaseHTTPRequestHandler]:
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
            if path in pages:
                self._send(200, *pages[path])
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
    """Serve the explorer and rule pages on `host:port` (port 0: any free port)."""
    catalog = build_catalog()
    css = stylesheet(style_dir)
    data = {
        **site_data([], embed_all_roots=True),
        "source": "server",
        "rule_pages": rule_links(catalog),
    }
    pages = {
        f"/{RULES_DIR}/{name}": (
            content.encode("utf-8"),
            _RULE_CONTENT_TYPES[Path(name).suffix],
        )
        for name, content in rule_assets(catalog, "../", set(ROOTS), css).items()
    }
    page = page_html(data, style_dir, css=css).encode("utf-8")
    pages["/"] = (page, _RULE_CONTENT_TYPES[".html"])
    pages[f"/{RULES_DIR}/"] = pages[f"/{RULES_DIR}/{INDEX_PAGE}"]
    return ThreadingHTTPServer((host, port), _handler(pages))
