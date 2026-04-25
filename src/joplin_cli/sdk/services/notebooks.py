from __future__ import annotations

from typing import Any, List

from joplin_cli.sdk.models import Notebook
from joplin_cli.sdk.pagination import collect_pages


class NotebooksService:
    def __init__(self, http: Any) -> None:
        self._http = http

    def list(self, limit: int | None = None) -> List[Notebook]:
        params = {"limit": limit} if limit is not None else None
        return [self._to_model(item) for item in collect_pages(self._http, "folders", params, limit)]

    def tree(self) -> List[Notebook]:
        return self.list()

    def create(self, title: str, parent_id: str | None = None) -> Notebook:
        payload = _clean_payload({"title": title, "parent_id": parent_id})
        return self._to_model(self._http.post("folders", json=payload))

    def rename(self, notebook_id: str, title: str) -> Notebook:
        return self._to_model(self._http.put(f"folders/{notebook_id}", json={"title": title}))

    def delete(self, notebook_id: str) -> None:
        self._http.delete(f"folders/{notebook_id}")

    def _to_model(self, data: dict[str, Any]) -> Notebook:
        return Notebook(
            id=str(data["id"]),
            title=str(data.get("title", "")),
            parent_id=data.get("parent_id"),
            raw=data,
        )


def _clean_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}
