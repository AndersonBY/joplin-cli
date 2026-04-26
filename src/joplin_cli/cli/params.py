from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Iterable
from pathlib import Path

from joplin_cli.sdk.errors import JoplinValidationError

TEXT_FILE_VALUE_KEYS = frozenset({"body", "content"})


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
            values[key] = _resolve_value(key, value)
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


def _resolve_value(key: str, value: str) -> str:
    if key not in TEXT_FILE_VALUE_KEYS:
        return value
    if value.startswith("@@"):
        return value[1:]
    if not value.startswith("@"):
        return value
    return _read_text_file_value(key, value[1:])


def _read_text_file_value(key: str, raw_path: str) -> str:
    if not raw_path:
        raise JoplinValidationError(
            f"Cannot read {key} from file.",
            cause="The @file syntax was used without a file path.",
            try_this=f"Use {key}=@./draft.md, or {key}=@@literal to keep a leading @.",
            examples=[
                'joplin-cli notes create title="Draft" body=@./draft.md',
                "joplin-cli notes append id=<note-id> content=@./section.md",
            ],
        )

    path = Path(raw_path).expanduser()
    try:
        if not path.exists():
            raise JoplinValidationError(
                f"Cannot read {key} from file.",
                cause=f"File does not exist: {path}",
                try_this=f"Use {key}=@./draft.md with a readable UTF-8 text file.",
                examples=[
                    'joplin-cli notes create title="Draft" body=@./draft.md',
                    "joplin-cli notes append id=<note-id> content=@./section.md",
                ],
            )
        if path.is_dir():
            raise JoplinValidationError(
                f"Cannot read {key} from file.",
                cause=f"Path is a directory, not a file: {path}",
                try_this=f"Use {key}=@./draft.md with a readable UTF-8 text file.",
                examples=[
                    'joplin-cli notes create title="Draft" body=@./draft.md',
                    "joplin-cli notes append id=<note-id> content=@./section.md",
                ],
            )
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise JoplinValidationError(
            f"Cannot read {key} from file.",
            cause=f"File is not valid UTF-8 text: {path}",
            try_this="Save the file as UTF-8 Markdown, then retry.",
            examples=['joplin-cli notes create title="Draft" body=@./draft.md'],
        ) from exc
    except OSError as exc:
        raise JoplinValidationError(
            f"Cannot read {key} from file.",
            cause=f"{path}: {exc}",
            try_this=f"Check file permissions, then retry with {key}=@./draft.md.",
            examples=['joplin-cli notes create title="Draft" body=@./draft.md'],
        ) from exc
