from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from joplin_cli.sdk.auth import AuthResolver
from joplin_cli.sdk.config import JoplinCliConfig
from joplin_cli.sdk.errors import JoplinError

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 41184


def config_from_env() -> JoplinCliConfig:
    config_path = os.getenv("JOPLIN_CLI_CONFIG")
    return JoplinCliConfig(Path(config_path)) if config_path else JoplinCliConfig()


def build_status(client_factory: Any, *, config: JoplinCliConfig | None = None) -> dict[str, Any]:
    auth = _inspect_auth(config or config_from_env())
    client = None
    server = "offline"
    error = ""
    token_status = auth["token"]
    token_source = auth["token_source"]

    try:
        client = client_factory()
        ping = getattr(getattr(client, "http", None), "ping", None)
        if callable(ping):
            ping()
        server = "online"
        token_status = "valid"
        if token_source == "missing":
            token_source = "profile"
    except JoplinError as exc:
        error = exc.message
        token_status = "missing" if exc.__class__.__name__ == "JoplinAuthError" else token_status
    except Exception as exc:  # noqa: BLE001 - diagnostics must report failures, not crash.
        error = str(exc)
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()

    status: dict[str, Any] = {
        "server": server,
        "host": auth["host"],
        "port": auth["port"],
        "token": token_status,
        "token_source": token_source,
    }
    if error:
        status["error"] = error
    return status


def build_doctor(status: dict[str, Any]) -> str:
    lines = [
        f"Joplin server: {status['server']}",
        f"Host: {status['host']}",
        f"Port: {status['port']}",
        f"Token: {status['token']}",
        f"Token source: {status['token_source']}",
    ]
    if status.get("error"):
        lines.append(f"Problem: {status['error']}")
    lines.extend(
        [
            "Next:",
            '  joplin-cli notes list limit=10',
            '  joplin-cli search query="..."',
        ]
    )
    return "\n".join(lines)


def _inspect_auth(config: JoplinCliConfig) -> dict[str, Any]:
    resolver = AuthResolver(config)
    data = config.read()
    host = resolver._resolve_host(None, data)
    port = resolver._resolve_port(None, data)
    profile = resolver._resolve_profile(None, data)
    token, source = resolver._resolve_token(None, data, profile)
    return {
        "host": host or DEFAULT_HOST,
        "port": port or DEFAULT_PORT,
        "token": "valid" if token else "missing",
        "token_source": source,
    }
