from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Notebook:
    id: str
    title: str
    parent_id: str | None = None
    raw: dict[str, Any] | None = field(default=None, repr=False)


@dataclass
class Note:
    id: str
    title: str
    body: str = ""
    parent_id: str | None = None
    is_todo: int = 0
    todo_completed: int = 0
    raw: dict[str, Any] | None = field(default=None, repr=False)


@dataclass
class Tag:
    id: str
    title: str
    raw: dict[str, Any] | None = field(default=None, repr=False)


@dataclass
class Resource:
    id: str
    title: str
    mime: str | None = None
    size: int | None = None
    raw: dict[str, Any] | None = field(default=None, repr=False)
