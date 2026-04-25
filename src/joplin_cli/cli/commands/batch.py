from __future__ import annotations

from typing import Annotated

import typer

from joplin_cli.cli.commands import (
    close_client,
    echo_output,
    exit_with_error,
    get_client,
    require_value,
)
from joplin_cli.cli.params import parse_kv_args
from joplin_cli.sdk.errors import JoplinError, JoplinValidationError

app = typer.Typer(help="Run batch operations.")


@app.command("delete")
def delete_by_query(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    query = _require_query(parsed)
    client = get_client(ctx)
    try:
        result = client.batch.delete_by_query(
            query,
            dry_run="dry_run" in parsed.flags,
            confirm=parsed.values.get("confirm"),
            yes="yes" in parsed.flags,
        )
        echo_output(result, json_output=json_output, output_format=output_format)
    except JoplinError as error:
        exit_with_error(error)
    finally:
        close_client(client)


def _require_query(parsed) -> str:
    query = require_value(parsed, "query", example="query=tag:temporary").strip()
    if not query:
        exit_with_error(
            JoplinValidationError(
                "Missing required parameter: query.",
                try_this="Use query=tag:temporary.",
            )
        )
    return query
