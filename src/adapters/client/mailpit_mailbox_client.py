from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from common.config import MailboxConfig
from ports.mailbox_client import CapturedMessage, IMailboxClient


class MailpitMailboxClient(IMailboxClient):
    """Reads the Mailpit intake spool over its REST API."""

    def __init__(self, config: MailboxConfig, service_name: str = "aimel"):
        self._base = config.api_base.rstrip("/")
        self._prefix = f"X-{service_name.title()}"

    def capture(self, limit: int = 200) -> list[CapturedMessage]:
        listing = self._call("/api/v1/messages", params={"limit": limit})
        captured = []
        for summary in listing.get("messages", []):
            captured.append(self._hydrate(summary))
        return captured

    def purge(self, external_ids: list[str]) -> None:
        if external_ids:
            self._call("/api/v1/messages", method="DELETE", payload={"IDs": external_ids})

    def reachable(self) -> bool:
        try:
            self._call("/api/v1/info")
            return True
        except SystemExit:
            return False

    def _hydrate(self, summary: dict[str, Any]) -> CapturedMessage:
        external_id = summary["ID"]
        detail = self._call(f"/api/v1/message/{external_id}")
        raw_headers = self._call(f"/api/v1/message/{external_id}/headers")
        return CapturedMessage(
            external_id=external_id,
            rfc_message_id=_bracket(detail.get("MessageID", "")),
            subject=detail.get("Subject", ""),
            sender=detail["From"]["Address"],
            recipient=(detail.get("To") or [{"Address": ""}])[0]["Address"],
            body_html=detail.get("HTML") or "",
            body_text=detail.get("Text") or "",
            received_at=detail.get("Date", ""),
            headers={
                "session": _first(raw_headers, f"{self._prefix}-Session"),
                "actor": _first(raw_headers, f"{self._prefix}-Actor"),
                "thread": _first(raw_headers, f"{self._prefix}-Thread"),
                "in_reply_to": _first(raw_headers, "In-Reply-To"),
                "references": _first(raw_headers, "References"),
            },
        )

    def _call(
        self,
        path: str,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = self._base + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(
            url, data=data, method=method, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                body = response.read()
        except urllib.error.URLError as exc:
            raise SystemExit(f"cannot reach the intake spool at {self._base} ({exc})") from exc
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw": body.decode(errors="replace")}


def _first(headers: dict[str, Any], name: str) -> str:
    values = headers.get(name) or []
    return values[0] if values else ""


def _bracket(message_id: str) -> str:
    if message_id and not message_id.startswith("<"):
        return f"<{message_id}>"
    return message_id
