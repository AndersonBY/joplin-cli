from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Iterable

from joplin_cli.sdk.errors import JoplinValidationError


@dataclass(frozen=True)
class ParsedArgs:
    values: dict[str, str] = field(default_factory=dict)
    flags: set[str] = field(default_factory=set)


def parse_kv_args(args: Iterable[str]) -> ParsedArgs:
    values: dict[str, str] = {}
    flags: set[str] = set()

    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            key = _normalize_key(key)
            values[key] = value
        else:
            flags.add(_normalize_key(arg))

    return ParsedArgs(values=values, flags=flags)


def _normalize_key(key: str) -> str:
    normalized = key.strip().replace("-", "_")
    if not normalized:
        raise JoplinValidationError(
            "CLI parameter key cannot be empty.",
            try_this="Use key=value pairs such as title=Note.",
        )
    return normalized
