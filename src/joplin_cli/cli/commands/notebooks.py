from __future__ import annotations

from typing import Annotated

import typer

from joplin_cli.cli.commands import close_client, echo_output, get_client, optional_int, require_value
from joplin_cli.cli.params import parse_kv_args

app = typer.Typer(help="Work with notebooks.")


@app.command("list")
def list_notebooks(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    client = get_client(ctx)
    try:
        notebooks = client.notebooks.list(limit=optional_int(parsed, "limit"))
        echo_output(notebooks, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("create")
def create_notebook(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    title = require_value(parsed, "title", example="title=Projects")
    client = get_client(ctx)
    try:
        notebook = client.notebooks.create(title)
        echo_output(notebook, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("tree")
def tree_notebooks(
    ctx: typer.Context,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    client = get_client(ctx)
    try:
        tree = client.notebooks.tree()
        echo_output(tree, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("rename")
def rename_notebook(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    notebook_id = require_value(parsed, "id", example="id=folder1")
    title = require_value(parsed, "title", example="title=Projects")
    client = get_client(ctx)
    try:
        notebook = client.notebooks.rename(notebook_id, title)
        echo_output(notebook, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("delete")
def delete_notebook(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    notebook_id = require_value(parsed, "id", example="id=folder1")
    client = get_client(ctx)
    try:
        result = client.notebooks.delete(notebook_id)
        echo_output(
            result if result is not None else {"deleted": True, "id": notebook_id},
            json_output=json_output,
            output_format=output_format,
        )
    finally:
        close_client(client)
