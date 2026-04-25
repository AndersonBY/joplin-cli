from __future__ import annotations

from typing import Any, NoReturn

import typer

from joplin_cli.cli.errors import render_error
from joplin_cli.cli.output import render_output
from joplin_cli.cli.params import ParsedArgs
from joplin_cli.sdk.errors import JoplinError, JoplinValidationError


def get_client(ctx: typer.Context) -> Any:
    client_factory = (ctx.obj or {}).get("client_factory")
    if client_factory is None:
        raise JoplinValidationError("CLI client factory is not configured.")
    return client_factory()


def close_client(client: Any) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        close()


def echo_output(data: Any, *, json_output: bool, output_format: str) -> None:
    typer.echo(render_output(data, output_format="json" if json_output else output_format))


def exit_with_error(error: JoplinError) -> NoReturn:
    typer.echo(render_error(error))
    raise typer.Exit(error.exit_code)


def require_value(parsed: ParsedArgs, key: str, *, example: str) -> str:
    value = parsed.values.get(key)
    if value is None:
        exit_with_error(
            JoplinValidationError(
                f"Missing required parameter: {key}.",
                try_this=f"Use {example}.",
            )
        )
    return value


def optional_int(parsed: ParsedArgs, key: str) -> int | None:
    value = parsed.values.get(key)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise JoplinValidationError(
            f"Parameter {key} must be an integer.",
            try_this=f"Use {key}=5.",
        ) from exc
