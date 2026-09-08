"""Server-side rendering. Lives in web/ beside the markup it renders.

    layout.html              the page shell
    pages/<name>.html        a page, extending the layout
    components/<name>.html   a macro per component
    style.css

Two deliberate settings:

- `StrictUndefined`, so a template referring to a variable nobody passed raises instead of rendering
  a blank. Silent blanks are how a component quietly loses half its content.
- `auto_reload` with no cache, so editing a template shows up on the next refresh without a restart.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape


class HtmlRenderer:
    def __init__(self, directory: Path | None = None):
        self._directory = Path(directory) if directory else Path(__file__).parent / "templates"
        self._environment = Environment(
            loader=FileSystemLoader(self._directory),
            autoescape=select_autoescape(default_for_string=True, default=True),
            undefined=StrictUndefined,
            auto_reload=True,
            cache_size=0,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @property
    def directory(self) -> Path:
        return self._directory

    def page(self, name: str, props: object) -> str:
        """Renders pages/<name>.html with the props dataclass as its only context."""
        return self._environment.get_template(f"pages/{name}.html").render(props=props)
