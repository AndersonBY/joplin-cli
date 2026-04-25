from __future__ import annotations

from typing import Annotated

import typer

from joplin_cli.cli.commands import close_client, echo_output, get_client, require_value
from joplin_cli.cli.params import parse_kv_args

app = typer.Typer(help="Work with tags.")


@app.command("list")
def list_tags(
    ctx: typer.Context,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    client = get_client(ctx)
    try:
        tags = client.tags.list()
        echo_output(tags, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("notes")
def list_tag_notes(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    tag_id = require_value(parsed, "tag", example="tag=t1")
    client = get_client(ctx)
    try:
        notes = client.tags.notes(tag_id)
        echo_output(notes, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("add")
def add_tag_to_note(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    note_id = require_value(parsed, "note", example="note=n1")
    tag_id = require_value(parsed, "tag", example="tag=t1")
    client = get_client(ctx)
    try:
        result = client.tags.add_to_note(tag_id, note_id)
        echo_output(
            result
            if result is not None
            else {"success": True, "action": "add", "note": note_id, "tag": tag_id},
            json_output=json_output,
            output_format=output_format,
        )
    finally:
        close_client(client)


@app.command("remove")
def remove_tag_from_note(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    note_id = require_value(parsed, "note", example="note=n1")
    tag_id = require_value(parsed, "tag", example="tag=t1")
    client = get_client(ctx)
    try:
        result = client.tags.remove_from_note(tag_id, note_id)
        echo_output(
            result
            if result is not None
            else {"success": True, "action": "remove", "note": note_id, "tag": tag_id},
            json_output=json_output,
            output_format=output_format,
        )
    finally:
        close_client(client)
