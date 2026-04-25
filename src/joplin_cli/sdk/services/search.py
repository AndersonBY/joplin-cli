from __future__ import annotations

from typing import Any

from joplin_cli.sdk.pagination import collect_pages
from joplin_cli.sdk.services._pagination import api_page_limit


class SearchService:
    def __init__(self, http: Any) -> None:
        self._http = http

    def query(
        self,
        query: str,
        limit: int | None = None,
        type: str = "note",
    ) -> list[dict[str, Any]]:
        params = {"query": query, "limit": api_page_limit(limit), "type": type}
        return collect_pages(self._http, "search", params=params, total_limit=limit)
