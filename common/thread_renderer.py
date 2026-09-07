from __future__ import annotations

from collections.abc import Sequence

from domain.message import Message


def render_history(messages: Sequence[Message]) -> str:
    """Prior messages newest-first, collapsible, so the latest mail carries the whole thread."""
    if not messages:
        return ""
    rows = []
    for message in messages:
        content = message.content
        body = content.body_html or f"<p>{content.body_text}</p>"
        rows.append(
            '<blockquote style="margin:0 0 1em;padding:.4em 0 .4em 1em;border-left:3px solid #ccc">'
            f'<div style="color:#666;font-size:.85em">{content.author.value}'
            f' · {content.sent_at.isoformat(timespec="seconds")}</div>{body}</blockquote>'
        )
    return (
        f"<hr><details open><summary>history · {len(messages)} earlier, newest first</summary>"
        f"{''.join(rows)}</details>"
    )
