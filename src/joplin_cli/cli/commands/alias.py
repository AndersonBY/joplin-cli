from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated

import typer

from joplin_cli.cli.commands import exit_with_error
from joplin_cli.sdk.errors import JoplinConflictError

app = typer.Typer(help="Inspect shell alias setup.")


@app.command("status")
def alias_status() -> None:
    existing = shutil.which("joplin")
    if existing:
        if is_joplin_cli_alias(existing):
            typer.echo("joplin alias: already installed by joplin-cli")
            return
        typer.echo(f"joplin alias: blocked by existing command at {existing}")
        return
    typer.echo("joplin alias: available")


@app.command("install")
def alias_install(
    force: Annotated[
        bool,
        typer.Option("--force", "--overwrite", help="Allow replacing an existing joplin command."),
    ] = False,
) -> None:
    existing = shutil.which("joplin")
    if existing and not force:
        exit_with_error(
            JoplinConflictError(
                "A joplin command already exists.",
                cause=f"Found: {existing}",
                try_this="Re-run with --force only if you intend to replace it.",
            )
        )
    typer.echo("joplin alias install is opt-in and does not modify your shell automatically.")
    typer.echo("PowerShell:")
    typer.echo("  function joplin { joplin-cli @args }")
    typer.echo("POSIX shell:")
    typer.echo("  alias joplin='joplin-cli'")


@app.command("uninstall")
def alias_uninstall() -> None:
    typer.echo("Remove the joplin alias from your shell profile if you installed one.")


def is_joplin_cli_alias(path: str) -> bool:
    try:
        return "joplin-cli" in Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
