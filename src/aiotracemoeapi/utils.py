from __future__ import annotations

from collections.abc import Callable
from typing import Any


def clamp(
    value: float | None,
    format: str | Callable[[Any], str] = "{:}",
    *,
    floor: float | None = None,
    ceil: float | None = None,
    floor_token: str = "<",  # noqa: S107
    ceil_token: str = ">",  # noqa: S107
) -> str | None:
    """Format a number, clamping it to [floor, ceil] and prefixing a token if it was clamped."""
    if value is None:
        return None

    if floor is not None and value < floor:
        value = floor
        token = floor_token
    elif ceil is not None and value > ceil:
        value = ceil
        token = ceil_token
    else:
        token = ""

    if isinstance(format, str):
        return token + format.format(value)
    if callable(format):
        return token + format(value)
    raise ValueError(
        "Invalid format. Must be either a valid formatting string, or a function "
        "that accepts value and returns a string."
    )
