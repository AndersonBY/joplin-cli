from __future__ import annotations

from typing import Annotated

import typer

from joplin_cli.cli.commands import close_client, echo_output, get_client, optional_int, require_value
from joplin_cli.cli.params import parse_kv_args

app = typer.Typer(help="Work with notes.")
PARAMS_HELP = "Parameters as key=value pairs."
TEXT_PARAMS_HELP = (
    "Parameters as key=value pairs. Text values support body=@./draft.md, "
    "content=@./section.md, and @@literal for a leading @."
)


@app.command("list")
def list_notes(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help=PARAMS_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    client = get_client(ctx)
    try:
        notes = client.notes.list(
            parent_id=parsed.values.get("parent_id"),
            limit=optional_int(parsed, "limit"),
        )
        echo_output(notes, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("read")
def read_note(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help=PARAMS_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    note_id = require_value(parsed, "id", example="id=n1")
    client = get_client(ctx)
    try:
        note = client.notes.get(note_id)
        echo_output(note, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("create")
def create_note(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help=TEXT_PARAMS_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    title = require_value(parsed, "title", example="title='New note'")
    client = get_client(ctx)
    try:
        note = client.notes.create(
            title=title,
            body=parsed.values.get("body", ""),
            parent_id=parsed.values.get("parent_id"),
        )
        echo_output(note, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("append")
def append_note(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help=TEXT_PARAMS_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    note_id = require_value(parsed, "id", example="id=n1")
    content = require_value(parsed, "content", example="content='More text'")
    client = get_client(ctx)
    try:
        note = client.notes.append(note_id, content)
        echo_output(note, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("prepend")
def prepend_note(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help=TEXT_PARAMS_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    note_id = require_value(parsed, "id", example="id=n1")
    content = require_value(parsed, "content", example="content='Intro text'")
    client = get_client(ctx)
    try:
        note = client.notes.prepend(note_id, content)
        echo_output(note, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("update")
def update_note(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help=TEXT_PARAMS_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    note_id = require_value(parsed, "id", example="id=n1")
    changes = {
        key: value
        for key, value in parsed.values.items()
        if key in {"title", "body"} and value is not None
    }
    client = get_client(ctx)
    try:
        note = client.notes.update(note_id, **changes)
        echo_output(note, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("move")
def move_note(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help=PARAMS_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    note_id = require_value(parsed, "id", example="id=n1")
    notebook_id = require_value(parsed, "notebook", example="notebook=folder1")
    client = get_client(ctx)
    try:
        note = client.notes.move(note_id, notebook_id)
        echo_output(note, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("copy")
def copy_note(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help=PARAMS_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    note_id = require_value(parsed, "id", example="id=n1")
    notebook_id = require_value(parsed, "notebook", example="notebook=folder1")
    client = get_client(ctx)
    try:
        note = client.notes.copy(note_id, notebook_id)
        echo_output(note, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("delete")
def delete_note(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help=PARAMS_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    note_id = require_value(parsed, "id", example="id=n1")
    client = get_client(ctx)
    try:
        result = client.notes.delete(note_id)
        echo_output(
            result if result is not None else {"deleted": True, "id": note_id},
            json_output=json_output,
            output_format=output_format,
        )
    finally:
        close_client(client)
