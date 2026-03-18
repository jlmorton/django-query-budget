from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

_DURATION_RE = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$")


def parse_duration(value: str | int | float | timedelta) -> timedelta:
    if isinstance(value, timedelta):
        return value
    if isinstance(value, (int, float)):
        return timedelta(seconds=value)
    if not isinstance(value, str):
        raise TypeError(f"Expected str, int, float, or timedelta, got {type(value)}")
    match = _DURATION_RE.match(value.strip())
    if not match or not any(match.groups()):
        raise ValueError(f"Invalid duration string: {value!r}. Use format like '1h30m', '5m', '30s'.")
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


@dataclass(frozen=True)
class Budget:
    total_runtime: timedelta
    window: timedelta
    max_queries: int | None = None
    max_single_query: timedelta | None = None
    action: str = "LOG"
    name: str | None = None
    constraints: list[Any] = field(default_factory=list)

    def __post_init__(self):
        object.__setattr__(self, "total_runtime", parse_duration(self.total_runtime))
        object.__setattr__(self, "window", parse_duration(self.window))
        if self.max_single_query is not None:
            object.__setattr__(self, "max_single_query", parse_duration(self.max_single_query))

    @property
    def total_runtime_seconds(self) -> float:
        return self.total_runtime.total_seconds()

    @property
    def window_seconds(self) -> float:
        return self.window.total_seconds()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Budget:
        return cls(
            total_runtime=data["total_runtime"], window=data["window"],
            max_queries=data.get("max_queries"), max_single_query=data.get("max_single_query"),
            action=data.get("action", "LOG"), name=data.get("name"),
            constraints=data.get("constraints", []),
        )
