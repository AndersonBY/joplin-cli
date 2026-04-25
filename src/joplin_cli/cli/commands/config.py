from __future__ import annotations

from typing import Annotated

import typer

from joplin_cli.cli.commands import exit_with_error
from joplin_cli.cli.diagnostics import config_from_env
from joplin_cli.sdk.errors import JoplinError, JoplinValidationError

app = typer.Typer(help="Inspect and update joplin-cli configuration.")


@app.command("path")
def config_path() -> None:
    typer.echo(str(config_from_env().resolved_path))


@app.command("get")
def get_config(
    params: Annotated[list[str] | None, typer.Argument(help="Use key=token or token.")] = None,
) -> None:
    try:
        key = _key_from_params(params or [])
        value = config_from_env().read().get(key)
    except JoplinError as exc:
        exit_with_error(exc)
    typer.echo(f"{key}={_display_value(key, value)}")


@app.command("set")
def set_config(
    params: Annotated[list[str], typer.Argument(help="Use key=value, for example token=...")],
) -> None:
    try:
        key, value = _pair_from_params(params)
        config_from_env().set_value(key, value)
    except JoplinError as exc:
        exit_with_error(exc)
    typer.echo(f"{key}={_display_value(key, value)}")


@app.command("unset")
def unset_config(
    params: Annotated[list[str] | None, typer.Argument(help="Use key=token or token.")] = None,
) -> None:
    try:
        key = _key_from_params(params or [])
        config_from_env().unset_value(key)
    except JoplinError as exc:
        exit_with_error(exc)
    typer.echo(f"unset {key}")


def _key_from_params(params: list[str]) -> str:
    if len(params) != 1:
        raise JoplinValidationError(
            "Expected exactly one config key.",
            try_this="Use `joplin-cli config get key=token`.",
        )
    arg = params[0]
    if "=" in arg:
        key, value = arg.split("=", 1)
        if key != "key":
            raise JoplinValidationError(
                "Expected config key parameter.",
                try_this="Use `joplin-cli config get key=token`.",
            )
        arg = value
    return _normalize_key(arg)


def _pair_from_params(params: list[str]) -> tuple[str, str]:
    if len(params) != 1 or "=" not in params[0]:
        raise JoplinValidationError(
            "Expected exactly one config key=value pair.",
            try_this="Use `joplin-cli config set token=...`.",
        )
    key, value = params[0].split("=", 1)
    return _normalize_key(key), value


def _normalize_key(key: str) -> str:
    normalized = key.strip().replace("-", "_")
    if not normalized:
        raise JoplinValidationError(
            "Config key cannot be empty.",
            try_this="Use a key such as token, host, port, profile, or timeout.",
        )
    return normalized


def _display_value(key: str, value: object) -> str:
    if _is_sensitive_key(key) and value:
        return "[redacted]"
    if value is None:
        return ""
    return str(value)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in ("token", "secret", "password"))
