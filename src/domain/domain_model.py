from __future__ import annotations

from abc import ABC


class DomainModel(ABC):
    """Marker for domain objects. Frozen dataclasses, non-null fields, no infrastructure."""
