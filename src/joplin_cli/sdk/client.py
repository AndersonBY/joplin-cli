from __future__ import annotations

from typing import Any

import httpx

from joplin_cli.sdk.auth import AuthResolver
from joplin_cli.sdk.http import JoplinHttpClient
from joplin_cli.sdk.services.batch import BatchService
from joplin_cli.sdk.services.notebooks import NotebooksService
from joplin_cli.sdk.services.notes import NotesService
from joplin_cli.sdk.services.resources import ResourcesService
from joplin_cli.sdk.services.search import SearchService
from joplin_cli.sdk.services.tags import TagsService
from joplin_cli.sdk.services.todos import TodosService


class JoplinClient:
    """SDK entry point. Services are added in later tasks."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 41184,
        token: str = "",
        timeout: float = 10,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.http = JoplinHttpClient(
            host,
            port,
            token,
            timeout,
            transport=transport,
        )
        self.notebooks = NotebooksService(self.http)
        self.notes = NotesService(self.http)
        self.search = SearchService(self.http)
        self.tags = TagsService(self.http)
        self.todos = TodosService(self.http)
        self.resources = ResourcesService(self.http)
        self.batch = BatchService(notes=self.notes, search=self.search, tags=self.tags)

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> JoplinClient:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    @classmethod
    def auto(
        cls,
        *,
        transport: httpx.BaseTransport | None = None,
        **kwargs: Any,
    ) -> JoplinClient:
        resolved = AuthResolver().resolve(**kwargs)
        return cls(
            host=resolved.host,
            port=resolved.port,
            token=resolved.token,
            timeout=resolved.timeout,
            transport=transport,
        )
