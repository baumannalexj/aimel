from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from adapters.resource.email_api_resource import EmailApiResource
from common.headers import HttpHeaders


class ApiServer:
    """JSON over HTTP for the web client. Local only — this serves unauthenticated mail."""

    def __init__(self, resource: EmailApiResource, host: str = "127.0.0.1", port: int = 8027):
        self._resource = resource
        self._host = host
        self._port = port

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self._port}"

    def serve_forever(self) -> None:
        server = ThreadingHTTPServer((self._host, self._port), self._handler())
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()

    def _handler(self):
        resource = self._resource

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_GET(self) -> None:  # noqa: N802 - stdlib naming
                if self.path == "/api/threads":
                    self._json([item.model_dump() for item in resource.threads()])
                    return
                self._json({"error": "not found"}, status=404)

            def _json(self, payload: object, status: int = 200) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header(HttpHeaders.CONTENT_TYPE, HttpHeaders.JSON)
                self.send_header(HttpHeaders.CONTENT_LENGTH, str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, fmt: str, *args) -> None:
                return

        return Handler
