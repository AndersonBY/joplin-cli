from __future__ import annotations

from typing import Any, List

from joplin_cli.sdk.models import Note
from joplin_cli.sdk.pagination import collect_pages

NOTE_DETAIL_FIELDS = "id,title,body,parent_id,is_todo,todo_completed"
NOTE_LIST_FIELDS = "id,title,parent_id,is_todo,todo_completed"


class NotesService:
    def __init__(self, http: Any) -> None:
        self._http = http

    def list(self, parent_id: str | None = None, limit: int | None = None) -> List[Note]:
        path = "notes" if parent_id is None else f"folders/{parent_id}/notes"
        params: dict[str, object] = {"fields": NOTE_LIST_FIELDS}
        if limit is not None:
            params["limit"] = limit
        return [self._to_model(item) for item in collect_pages(self._http, path, params, limit)]

    def get(self, note_id: str) -> Note:
        return self._to_model(
            self._http.get(f"notes/{note_id}", params={"fields": NOTE_DETAIL_FIELDS})
        )

    def create(
        self,
        title: str,
        body: str = "",
        parent_id: str | None = None,
        is_todo: int = 0,
    ) -> Note:
        payload = _clean_payload(
            {
                "title": title,
                "body": body,
                "parent_id": parent_id,
                "is_todo": is_todo if is_todo else None,
            }
        )
        return self._to_model(self._http.post("notes", json=payload))

    def update(self, note_id: str, **changes: Any) -> Note:
        return self._to_model(self._http.put(f"notes/{note_id}", json=_clean_payload(changes)))

    def append(self, note_id: str, content: str) -> Note:
        note = self.get(note_id)
        return self.update(note_id, body=f"{note.body}{content}")

    def prepend(self, note_id: str, content: str) -> Note:
        note = self.get(note_id)
        return self.update(note_id, body=f"{content}{note.body}")

    def move(self, note_id: str, parent_id: str) -> Note:
        return self.update(note_id, parent_id=parent_id)

    def copy(self, note_id: str, parent_id: str | None = None) -> Note:
        note = self.get(note_id)
        return self.create(
            title=note.title,
            body=note.body,
            parent_id=parent_id if parent_id is not None else note.parent_id,
            is_todo=note.is_todo,
        )

    def delete(self, note_id: str) -> None:
        self._http.delete(f"notes/{note_id}")

    def _to_model(self, data: dict[str, Any]) -> Note:
        return Note(
            id=str(data["id"]),
            title=str(data.get("title", "")),
            body=str(data.get("body", "")),
            parent_id=data.get("parent_id"),
            is_todo=int(data.get("is_todo", 0) or 0),
            todo_completed=int(data.get("todo_completed", 0) or 0),
            raw=data,
        )


def _clean_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}
