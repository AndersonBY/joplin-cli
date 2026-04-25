from __future__ import annotations

from pathlib import Path
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
from joplin_cli.sdk.errors import JoplinValidationError

app = typer.Typer(help="Work with resources.")


@app.command("list")
def list_resources(
    ctx: typer.Context,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    client = get_client(ctx)
    try:
        resources = client.resources.list()
        echo_output(resources, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("info")
def resource_info(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    resource_id = require_value(parsed, "id", example="id=r1")
    client = get_client(ctx)
    try:
        resource = client.resources.get(resource_id)
        echo_output(resource, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("attach")
def attach_resource(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    note_id = require_value(parsed, "note", example="note=n1")
    path = Path(require_value(parsed, "path", example="path=./file.pdf"))
    client = get_client(ctx)
    try:
        resource = client.resources.attach_file(note_id, path)
        echo_output(resource, json_output=json_output, output_format=output_format)
    finally:
        close_client(client)


@app.command("download")
def download_resource(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    resource_id = require_value(parsed, "id", example="id=r1")
    output = Path(require_value(parsed, "output", example="output=./resource.bin"))
    if output.exists() and "overwrite" not in parsed.flags:
        exit_with_error(
            JoplinValidationError(
                f"Output path already exists: {output}",
                try_this="Use overwrite to replace the existing file.",
            )
        )
    client = get_client(ctx)
    try:
        data = client.resources.download(resource_id)
        output.write_bytes(data)
        echo_output(
            {"id": resource_id, "output": str(output), "bytes": len(data)},
            json_output=json_output,
            output_format=output_format,
        )
    finally:
        close_client(client)


@app.command("delete")
def delete_resource(
    ctx: typer.Context,
    params: Annotated[list[str] | None, typer.Argument(help="Parameters as key=value pairs.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Render JSON output.")] = False,
    output_format: Annotated[str, typer.Option("--format", help="Output format.")] = "text",
) -> None:
    parsed = parse_kv_args(params or [])
    resource_id = require_value(parsed, "id", example="id=r1")
    client = get_client(ctx)
    try:
        result = client.resources.delete(resource_id)
        echo_output(
            result if result is not None else {"deleted": True, "id": resource_id},
            json_output=json_output,
            output_format=output_format,
        )
    finally:
        close_client(client)
