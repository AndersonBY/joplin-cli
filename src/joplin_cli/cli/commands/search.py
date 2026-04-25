from __future__ import annotations

from typing import Annotated

import typer

from joplin_cli.cli.commands import close_client, echo_output, get_client, optional_int, require_value
from joplin_cli.cli.params import parse_kv_args


def search(
    ctx: typer.Context,
    params: Annotated[list[str], typer.Argument(help="Parameters as key=value pairs.")],
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params)
    client = get_client(ctx)
    try:
        results = client.search.query(
            require_value(parsed, "query", example="query=hello"),
            limit=optional_int(parsed, "limit"),
        )
        echo_output(results, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)
