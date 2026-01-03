from collections.abc import Callable
from typing import Any, Union


def clamp(
    value: Union[int, float, None],
    format: Union[str, Callable[[Any], str]] = "{:}",
    floor: Union[int, float, None] = None,
    ceil: Union[int, float, None] = None,
    floor_token: str = "<",  # noqa: S107
    ceil_token: str = ">",  # noqa: S107
) -> Union[str, None]:
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
