from __future__ import annotations

from typing import Any

from joplin_cli.sdk.errors import JoplinApiError


def collect_pages(
    http: Any,
    path: str,
    params: dict[str, Any] | None = None,
    total_limit: int | None = None,
) -> list[Any]:
    items: list[Any] = []
    page = 1

    while total_limit is None or len(items) < total_limit:
        request_params = dict(params or {})
        request_params["page"] = page
        response = http.get(path, params=request_params)
        page_items, has_more = _extract_page_data(response)

        remaining = None if total_limit is None else total_limit - len(items)
        items.extend(page_items if remaining is None else page_items[:remaining])

        if not has_more or (total_limit is not None and len(items) >= total_limit):
            break
        page += 1

    return items


def _extract_page_data(response: Any) -> tuple[list[Any], bool]:
    if not isinstance(response, dict):
        raise JoplinApiError(
            "Joplin API pagination response was invalid.",
            cause="Expected a response object with items and has_more fields.",
            try_this="Run `joplin-cli doctor` to confirm the local Joplin data API is healthy.",
        )

    page_items = response.get("items")
    if not isinstance(page_items, list):
        raise JoplinApiError(
            "Joplin API pagination response was invalid.",
            cause="Expected the response items field to be a list.",
            try_this="Run `joplin-cli doctor` to confirm the local Joplin data API is healthy.",
        )

    has_more = response.get("has_more")
    if not isinstance(has_more, bool):
        raise JoplinApiError(
            "Joplin API pagination response was invalid.",
            cause="Expected the response has_more field to be a boolean.",
            try_this="Run `joplin-cli doctor` to confirm the local Joplin data API is healthy.",
        )
    return page_items, has_more
