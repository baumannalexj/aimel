from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from adapters.resource.email_api_resource import EmailApiResource
from common.headers import HttpHeaders
from domain.errors import EmailAlreadyDeleted, EmailNotFound

THREAD_PATH = re.compile(r"^/api/emails/([0-9a-fA-F-]{36})/thread$")
REPLY_PATH = re.compile(r"^/api/emails/([0-9a-fA-F-]{36})/replies$")
READ_PATH = re.compile(r"^/api/emails/([0-9a-fA-F-]{36})/read$")


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
                path, _, query = self.path.partition("?")
                if path == "/api/threads":
                    scope = parse_qs(query).get("scope", ["mine"])[0]
                    self._json([item.model_dump() for item in resource.threads(scope)])
                    return
                match = THREAD_PATH.match(self.path)
                if match:
                    detail = resource.thread(match.group(1))
                    if detail is None:
                        self._json({"error": "no such email"}, status=404)
                        return
                    self._json(detail.model_dump())
                    return
                self._json({"error": "not found"}, status=404)

            def do_POST(self) -> None:  # noqa: N802 - stdlib naming
                read_match = READ_PATH.match(self.path)
                if read_match:
                    # No body expected, but drain it so a keep-alive connection stays in sync.
                    self.rfile.read(int(self.headers.get("Content-Length", "0")))
                    try:
                        self._json(resource.mark_read(read_match.group(1)).model_dump())
                    except EmailAlreadyDeleted as deleted:
                        self._json({"error": str(deleted)}, status=409)
                    except EmailNotFound as missing:
                        self._json({"error": str(missing)}, status=404)
                    return
                match = REPLY_PATH.match(self.path)
                if not match:
                    self._json({"error": "not found"}, status=404)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                try:
                    sent = json.loads(self.rfile.read(length) or b"{}")
                except json.JSONDecodeError:
                    self._json({"error": "body must be json"}, status=400)
                    return
                markup = str(sent.get("html", "")).strip()
                if not markup:
                    self._json({"error": "html is required"}, status=422)
                    return
                try:
                    self._json(resource.reply(match.group(1), markup).model_dump(), status=201)
                except EmailNotFound as unknown:
                    self._json({"error": str(unknown)}, status=404)

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
