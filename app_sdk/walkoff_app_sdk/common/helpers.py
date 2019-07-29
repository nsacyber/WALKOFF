import logging

logger = logging.getLogger("WALKOFF")

HEX_CHARS = 'abcdefABCDEF0123456789'
UUID_GLOB = "-".join((f"[{HEX_CHARS}]" * i for i in (8, 4, 4, 4, 12)))
UUID_REGEX = "[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"


def sint(value, default):
    if not isinstance(default, int):
        raise TypeError("Default value must be of integer type")
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def sfloat(value, default):
    if not isinstance(default, int):
        raise TypeError("Default value must be of float type")
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
