from __future__ import annotations

from typing import Annotated

import typer

from joplin_cli.cli.commands import echo_output, exit_with_error
from joplin_cli.cli.diagnostics import build_doctor, build_status, config_from_env
from joplin_cli.sdk.errors import JoplinError


def status(
    ctx: typer.Context,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    try:
        data = build_status((ctx.obj or {})["client_factory"], config=config_from_env())
    except JoplinError as exc:
        exit_with_error(exc)
    echo_output(data, json_output=json_output, output_format=output_format)


def doctor(ctx: typer.Context) -> None:
    try:
        data = build_status((ctx.obj or {})["client_factory"], config=config_from_env())
    except JoplinError as exc:
        exit_with_error(exc)
    typer.echo(build_doctor(data))


def auth(ctx: typer.Context) -> None:
    try:
        data = build_status((ctx.obj or {})["client_factory"], config=config_from_env())
    except JoplinError as exc:
        exit_with_error(exc)
    typer.echo(f"Token: {data['token']}")
    typer.echo(f"Token source: {data['token_source']}")
    typer.echo("Set a token with one of:")
    typer.echo("  joplin-cli config set token=...")
    typer.echo('  $env:JOPLIN_TOKEN="..."')
    typer.echo("Token values are never printed by this command.")
