from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from joplin_cli.sdk.models import Resource
from joplin_cli.sdk.pagination import collect_pages
from joplin_cli.sdk.services._pagination import api_page_limit
from joplin_cli.sdk.services.notes import NotesService


class ResourcesService:
    def __init__(self, http: Any) -> None:
        self._http = http
        self._notes = NotesService(http)

    def list(self, limit: int | None = None) -> List[Resource]:
        params = {"limit": api_page_limit(limit)}
        return [
            self._to_model(item)
            for item in collect_pages(self._http, "resources", params, total_limit=limit)
        ]

    def get(self, resource_id: str) -> Resource:
        return self._to_model(self._http.get(f"resources/{resource_id}"))

    def attach_file(self, note_id: str, path: Path, title: str | None = None) -> Resource:
        resource_title = title or path.name
        with path.open("rb") as file_handle:
            data = {"props": json.dumps({"title": resource_title})}
            files = {"data": (path.name, file_handle)}
            resource = self._to_model(
                self._http.request("POST", "resources", files=files, data=data)
            )

        self._append_resource_link(note_id, resource)
        return resource

    def download(self, resource_id: str) -> bytes:
        if hasattr(self._http, "raw"):
            return self._http.raw(f"resources/{resource_id}/file")
        return self._http.get(f"resources/{resource_id}/file")

    def delete(self, resource_id: str) -> None:
        self._http.delete(f"resources/{resource_id}")

    def _append_resource_link(self, note_id: str, resource: Resource) -> None:
        note = self._notes.get(note_id)
        separator = "\n" if note.body else ""
        self._notes.update(note_id, body=f"{note.body}{separator}[](:/{resource.id})")

    def _to_model(self, data: dict[str, Any]) -> Resource:
        return Resource(
            id=str(data["id"]),
            title=str(data.get("title", "")),
            mime=data.get("mime") or data.get("mime_type"),
            size=_optional_int(data.get("size")),
            raw=data,
        )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
