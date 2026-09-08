from __future__ import annotations

import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from adapters.resource.email_web_resource import EmailWebResource
from common.headers import HttpHeaders

THREAD_PATH = re.compile(r"^/email/([0-9a-fA-F-]{36})$")
REPLY_PATH = re.compile(r"^/email/([0-9a-fA-F-]{36})/reply$")


class WebServer:
    """Serves the reply-capable view. Local only — this holds unauthenticated mail."""

    def __init__(self, resource: EmailWebResource, host: str = "127.0.0.1", port: int = 8026):
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
                if self.path == "/":
                    self._html(resource.threads_page())
                    return
                match = THREAD_PATH.match(self.path)
                if match:
                    self._html(resource.thread_page(match.group(1)))
                    return
                self._html("<h1>404</h1>", status=404)

            def do_POST(self) -> None:  # noqa: N802 - stdlib naming
                match = REPLY_PATH.match(self.path)
                if not match:
                    self._html("<h1>404</h1>", status=404)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                form = parse_qs(self.rfile.read(length).decode("utf-8"))
                markup = (form.get("html") or [""])[0].strip()
                if not markup:
                    self._redirect(f"/email/{match.group(1)}")
                    return
                try:
                    sent_id = resource.reply(match.group(1), markup)
                except PermissionError as refused:
                    self._html(f"<h1>403</h1><p>{refused}</p>", status=403)
                    return
                self._redirect(f"/email/{sent_id}")

            def _html(self, body: str, status: int = 200) -> None:
                payload = body.encode("utf-8")
                self.send_response(status)
                self.send_header(HttpHeaders.CONTENT_TYPE, HttpHeaders.HTML_UTF8)
                self.send_header(HttpHeaders.CONTENT_LENGTH, str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def _redirect(self, location: str) -> None:
                self.send_response(303)
                self.send_header(HttpHeaders.LOCATION, location)
                self.send_header(HttpHeaders.CONTENT_LENGTH, "0")
                self.end_headers()

            def log_message(self, fmt: str, *args) -> None:
                return

        return Handler
