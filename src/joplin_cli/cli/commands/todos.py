from __future__ import annotations

from typing import Annotated

import typer

from joplin_cli.cli.commands import close_client, echo_output, get_client, require_value
from joplin_cli.cli.params import parse_kv_args

app = typer.Typer(help="Work with todos.")


@app.command("list")
def list_todos(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    open_filter = "open" in parsed.flags
    done_filter = "done" in parsed.flags
    client = get_client(ctx)
    try:
        todos = client.todos.list(open=open_filter, done=done_filter)
        echo_output(todos, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("create")
def create_todo(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    title = require_value(parsed, "title", example="title='Call Alice'")
    notebook_id = require_value(parsed, "notebook", example="notebook=folder1")
    client = get_client(ctx)
    try:
        todo = client.todos.create(title=title, parent_id=notebook_id)
        echo_output(todo, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("done")
def done_todo(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    todo_id = require_value(parsed, "id", example="id=todo1")
    client = get_client(ctx)
    try:
        todo = client.todos.done(todo_id)
        echo_output(todo, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("open")
def open_todo(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    todo_id = require_value(parsed, "id", example="id=todo1")
    client = get_client(ctx)
    try:
        todo = client.todos.open(todo_id)
        echo_output(todo, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("toggle")
def toggle_todo(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    todo_id = require_value(parsed, "id", example="id=todo1")
    client = get_client(ctx)
    try:
        todo = client.todos.toggle(todo_id)
        echo_output(todo, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)
