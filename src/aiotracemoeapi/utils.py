def clamp(value, format="{:}", floor=None, ceil=None, floor_token="<", ceil_token=">"):
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
    elif callable(format):
        return token + format(value)
    else:
        raise ValueError(
            "Invalid format. Must be either a valid formatting string, or a function "
            "that accepts value and returns a string."
        )
