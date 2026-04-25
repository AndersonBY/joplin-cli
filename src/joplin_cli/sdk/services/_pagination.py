from __future__ import annotations

JOPLIN_MAX_PAGE_LIMIT = 100


def api_page_limit(total_limit: int | None) -> int:
    if total_limit is None:
        return JOPLIN_MAX_PAGE_LIMIT
    return min(total_limit, JOPLIN_MAX_PAGE_LIMIT)
