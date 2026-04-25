from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from typing import Any

from joplin_cli.sdk.errors import JoplinOutputError


def render_output(data: Any, output_format: str = "text") -> str:
    normalized = normalize(data)
    output_format = output_format.lower()

    if output_format == "json":
        return json.dumps(normalized, indent=2, ensure_ascii=False)
    if output_format == "tsv":
        return _render_delimited(normalized, delimiter="\t")
    if output_format == "csv":
        return _render_delimited(normalized, delimiter=",")
    if output_format == "text":
        return _render_text(normalized)

    raise JoplinOutputError(
        f"Unsupported output format: {output_format}",
        try_this="Use one of: text, json, tsv, csv.",
    )


def normalize(data: Any) -> Any:
    if is_dataclass(data) and not isinstance(data, type):
        return normalize(asdict(data))
    if isinstance(data, Mapping):
        return {str(key): normalize(value) for key, value in data.items() if key != "raw"}
    if isinstance(data, list | tuple):
        return [normalize(item) for item in data]
    return data


def _render_delimited(data: Any, *, delimiter: str) -> str:
    rows = _as_rows(data)
    if not rows:
        return ""

    headers = _collect_headers(rows)
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=headers,
        delimiter=delimiter,
        lineterminator="\n",
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().rstrip("\n")


def _collect_headers(rows: list[dict[str, Any]]) -> list[str]:
    headers: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                headers.append(key)
    return headers


def _render_text(data: Any) -> str:
    if isinstance(data, list):
        return "\n".join(_render_text_row(row) for row in data)
    if isinstance(data, Mapping):
        return _render_text_row(data)
    if data is None:
        return ""
    return str(data)


def _render_text_row(row: Any) -> str:
    if isinstance(row, Mapping):
        return "\t".join(f"{key}: {_stringify(value)}" for key, value in row.items())
    return _stringify(row)


def _as_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [_as_row(item) for item in data]
    if isinstance(data, Mapping):
        return [_as_row(data)]
    if data is None:
        return []
    return [{"value": data}]


def _as_row(item: Any) -> dict[str, Any]:
    if isinstance(item, Mapping):
        return {str(key): _stringify(value) for key, value in item.items()}
    return {"value": _stringify(item)}


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Iterable) and not isinstance(value, bytes | bytearray | Mapping):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, Mapping):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
