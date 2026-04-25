from __future__ import annotations

import hashlib
import json
from typing import Any

from joplin_cli.sdk.errors import JoplinConflictError, JoplinValidationError


class BatchService:
    def __init__(self, *, notes: Any, search: Any, tags: Any) -> None:
        self._notes = notes
        self._search = search
        self._tags = tags

    def delete_by_query(
        self,
        query: str,
        *,
        dry_run: bool = False,
        confirm: str | None = None,
        yes: bool = False,
    ) -> dict[str, Any]:
        query = _validate_query(query)
        matches = self._search.query(query)
        count = len(matches)
        preview = [_preview_note(note) for note in matches]
        token = _confirmation_token(query, preview)
        result = {
            "query": query,
            "count": count,
            "confirm": token,
            "deleted": False,
            "preview": preview,
        }

        if dry_run:
            return result

        if not yes and confirm != token:
            raise JoplinConflictError(
                "Batch delete requires confirmation.",
                try_this=f"Run a dry run first, then pass confirm={token} or yes.",
                examples=[
                    f"joplin-cli batch delete query={query} dry-run",
                    f"joplin-cli batch delete query={query} confirm={token}",
                ],
            )

        for note in matches:
            self._notes.delete(_note_id(note))

        return {**result, "deleted": True}


def _note_id(note: Any) -> str:
    if isinstance(note, dict):
        return str(note["id"])
    return str(note.id)


def _preview_note(note: Any) -> dict[str, str]:
    if isinstance(note, dict):
        return {"id": str(note["id"]), "title": str(note.get("title", ""))}
    return {"id": str(note.id), "title": str(getattr(note, "title", ""))}


def _confirmation_token(query: str, preview: list[dict[str, str]]) -> str:
    payload = {
        "query": query,
        "ids": [note["id"] for note in preview],
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:12]
    return f"delete-{len(preview)}-notes-{digest}"


def _validate_query(query: str) -> str:
    normalized = query.strip()
    if not normalized:
        raise JoplinValidationError(
            "Missing required parameter: query.",
            try_this="Use query=tag:temporary.",
        )
    return normalized
