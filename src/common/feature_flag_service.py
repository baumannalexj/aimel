"""Feature flags. One file for now — interface, the flags themselves, and the service.

The gate in the code is `FeatureFlagService.is_enabled(SomeFlag.KEY)`. An unknown key raises rather
than returning False, because a typo'd flag that silently reads as off is the worst outcome: the
feature just quietly disappears.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType


class FlagState(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class IFeatureFlag(ABC):
    @property
    @abstractmethod
    def key(self) -> str:
        """How the flag is addressed. Stable; the class name is not."""

    @property
    @abstractmethod
    def state(self) -> FlagState:
        """Whether the gate is open."""


@dataclass(frozen=True)
class EmailRespondFlag(IFeatureFlag):
    """Gates replying to an agent from the browser."""

    KEY = "email_respond"

    flag_state: FlagState = FlagState.ENABLED

    @property
    def key(self) -> str:
        return self.KEY

    @property
    def state(self) -> FlagState:
        return self.flag_state


DEFAULT_FLAGS: tuple[type[IFeatureFlag], ...] = (EmailRespondFlag,)


class FeatureFlagService:
    """Read-only after construction, so concurrent reads need no lock.

    The server is threaded, so this matters: the mapping is a MappingProxyType and the flags are
    frozen, which makes the thread safety structural instead of a convention someone can break by
    adding a setter later.
    """

    def __init__(self, flags: Mapping[str, IFeatureFlag]):
        self._flags: Mapping[str, IFeatureFlag] = MappingProxyType(dict(flags))

    @classmethod
    def with_defaults(cls, environ: Mapping[str, str] | None = None) -> "FeatureFlagService":
        """Every known flag on, unless the environment says otherwise.

        `AIMEL_FLAG_EMAIL_RESPOND=disabled` turns off `email_respond`, so a flag can be flipped
        without a code change.
        """
        source = environ if environ is not None else os.environ
        flags: dict[str, IFeatureFlag] = {}
        for flag_type in DEFAULT_FLAGS:
            key = flag_type.KEY  # type: ignore[attr-defined]
            override = source.get(f"AIMEL_FLAG_{key.upper()}", FlagState.ENABLED.value)
            flags[key] = flag_type(FlagState(override.strip().lower()))  # type: ignore[call-arg]
        return cls(flags)

    def is_enabled(self, key: str) -> bool:
        if key not in self._flags:
            raise KeyError(f"unknown feature flag: {key!r} — known: {sorted(self._flags)}")
        return self._flags[key].state is FlagState.ENABLED

    @property
    def keys(self) -> list[str]:
        return sorted(self._flags)
