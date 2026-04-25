from __future__ import annotations

from typing import Any, List

from joplin_cli.sdk.models import Note, Tag
from joplin_cli.sdk.pagination import collect_pages
from joplin_cli.sdk.services._pagination import api_page_limit


class TagsService:
    def __init__(self, http: Any) -> None:
        self._http = http

    def list(self, limit: int | None = None) -> List[Tag]:
        params = {"limit": api_page_limit(limit)}
        return [self._to_model(item) for item in collect_pages(self._http, "tags", params, limit)]

    def create(self, title: str) -> Tag:
        return self._to_model(self._http.post("tags", json={"title": title}))

    def notes(self, tag_id: str, limit: int | None = None) -> List[Note]:
        params = {"limit": api_page_limit(limit)}
        return [
            self._note_to_model(item)
            for item in collect_pages(self._http, f"tags/{tag_id}/notes", params, limit)
        ]

    def add_to_note(self, tag_id: str, note_id: str) -> None:
        self._http.post(f"tags/{tag_id}/notes", json={"id": note_id})

    def remove_from_note(self, tag_id: str, note_id: str) -> None:
        self._http.delete(f"tags/{tag_id}/notes/{note_id}")

    def _to_model(self, data: dict[str, Any]) -> Tag:
        return Tag(id=str(data["id"]), title=str(data.get("title", "")), raw=data)

    def _note_to_model(self, data: dict[str, Any]) -> Note:
        return Note(
            id=str(data["id"]),
            title=str(data.get("title", "")),
            body=str(data.get("body", "")),
            parent_id=data.get("parent_id"),
            is_todo=int(data.get("is_todo", 0) or 0),
            todo_completed=int(data.get("todo_completed", 0) or 0),
            raw=data,
        )
