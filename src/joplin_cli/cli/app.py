from collections.abc import Callable
from typing import Any

import click
import typer
from typer.core import TyperGroup

from joplin_cli.cli.commands.alias import app as alias_app
from joplin_cli.cli.commands.batch import app as batch_app
from joplin_cli.cli.commands.config import app as config_app
from joplin_cli.cli.commands.diagnostics import auth, doctor, status
from joplin_cli.cli.commands.notes import app as notes_app
from joplin_cli.cli.commands.notebooks import app as notebooks_app
from joplin_cli.cli.commands.resources import app as resources_app
from joplin_cli.cli.commands.search import search
from joplin_cli.cli.commands.tags import app as tags_app
from joplin_cli.cli.commands.todos import app as todos_app
from joplin_cli.cli.errors import render_error
from joplin_cli.sdk.client import JoplinClient
from joplin_cli.sdk.errors import JoplinError


class JoplinCliGroup(TyperGroup):
    def invoke(self, ctx: click.Context) -> Any:
        try:
            return super().invoke(ctx)
        except JoplinError as exc:
            typer.echo(render_error(exc))
            raise typer.Exit(exc.exit_code) from None


def build_app(client_factory: Callable[..., Any] = JoplinClient.auto) -> typer.Typer:
    cli_app = typer.Typer(
        cls=JoplinCliGroup,
        help="Agent-friendly CLI for local Joplin desktop.",
        invoke_without_command=True,
    )

    @cli_app.callback()
    def cli(ctx: typer.Context) -> None:
        """Agent-friendly CLI for local Joplin desktop."""
        ctx.obj = {"client_factory": client_factory}
        if ctx.invoked_subcommand is None:
            typer.echo("Run `joplin-cli help` or `joplin-cli doctor` to get started.")

    @cli_app.command("help")
    def help_command(ctx: typer.Context) -> None:
        """Show root command help."""
        root_ctx = ctx.parent or ctx
        typer.echo(root_ctx.get_help())

    cli_app.add_typer(notes_app, name="notes")
    cli_app.add_typer(notebooks_app, name="notebooks")
    cli_app.add_typer(tags_app, name="tags")
    cli_app.add_typer(todos_app, name="todos")
    cli_app.add_typer(resources_app, name="resources")
    cli_app.add_typer(batch_app, name="batch")
    cli_app.add_typer(config_app, name="config")
    cli_app.add_typer(alias_app, name="alias")
    cli_app.command("search")(search)
    cli_app.command("status")(status)
    cli_app.command("doctor")(doctor)
    cli_app.command("auth")(auth)
    return cli_app


app = build_app()


def main() -> None:
    build_app()()
