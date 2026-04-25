from __future__ import annotations

from collections.abc import Iterable


class JoplinError(Exception):
    exit_code = 1

    def __init__(
        self,
        message: str,
        *,
        cause: str = "",
        try_this: str = "",
        examples: Iterable[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause
        self.try_this = try_this
        self.examples = list(examples or [])

    def __str__(self) -> str:
        parts = [self.message]
        if self.cause:
            parts.append(self.cause)
        if self.try_this:
            parts.append(self.try_this)
        return " ".join(parts)


class JoplinConnectionError(JoplinError):
    exit_code = 3


class JoplinAuthError(JoplinError):
    exit_code = 4


class JoplinNotFoundError(JoplinError):
    exit_code = 5


class JoplinConflictError(JoplinError):
    exit_code = 6


class JoplinValidationError(JoplinError):
    exit_code = 2


class JoplinApiError(JoplinError):
    exit_code = 1


class JoplinOutputError(JoplinError):
    exit_code = 1
