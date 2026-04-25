from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path

from joplin_cli.sdk.config import JoplinCliConfig
from joplin_cli.sdk.errors import JoplinAuthError, JoplinValidationError


@dataclass(frozen=True)
class ResolvedAuth:
    host: str
    port: int
    token: str = field(repr=False)
    token_source: str
    profile: Path | None
    timeout: float


class AuthResolver:
    def __init__(self, config: JoplinCliConfig | None = None) -> None:
        self.config = config or JoplinCliConfig()

    def resolve(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        token: str | None = None,
        profile: str | Path | None = None,
        timeout: float | None = None,
    ) -> ResolvedAuth:
        config_data = self.config.read()
        resolved_host = self._resolve_host(host, config_data)
        resolved_port = self._resolve_port(port, config_data)
        resolved_timeout = self._resolve_timeout(timeout, config_data)
        resolved_profile = self._resolve_profile(profile, config_data)

        token_value, source = self._resolve_token(token, config_data, resolved_profile)
        if not token_value:
            raise JoplinAuthError(
                "Cannot access Joplin data API.",
                cause="Joplin is running, but no valid API token was found.",
                try_this="Run `joplin-cli doctor` to inspect token discovery.",
                examples=[
                    "joplin-cli doctor",
                    "joplin-cli auth",
                    '$env:JOPLIN_TOKEN="..."; joplin-cli notes list',
                ],
            )

        return ResolvedAuth(
            host=resolved_host,
            port=resolved_port,
            token=token_value,
            token_source=source,
            profile=resolved_profile,
            timeout=resolved_timeout,
        )

    def _resolve_host(self, host: str | None, config_data: dict[str, object]) -> str:
        if host:
            return host
        env_host = os.getenv("JOPLIN_HOST")
        if env_host:
            return env_host
        config_host = config_data.get("host")
        return config_host if isinstance(config_host, str) and config_host else "127.0.0.1"

    def _resolve_port(self, port: int | None, config_data: dict[str, object]) -> int:
        if port is not None:
            return self._parse_int("port", port, "CLI option")
        env_port = os.getenv("JOPLIN_PORT")
        if env_port:
            return self._parse_int("port", env_port, "JOPLIN_PORT")
        if "port" in config_data:
            return self._parse_int("port", config_data["port"], "config")
        return 41184

    def _resolve_timeout(self, timeout: float | None, config_data: dict[str, object]) -> float:
        if timeout is not None:
            return self._parse_float("timeout", timeout, "CLI option")
        env_timeout = os.getenv("JOPLIN_TIMEOUT")
        if env_timeout:
            return self._parse_float("timeout", env_timeout, "JOPLIN_TIMEOUT")
        if "timeout" in config_data:
            return self._parse_float("timeout", config_data["timeout"], "config")
        return 10.0

    def _parse_int(self, name: str, value: object, source: str) -> int:
        if isinstance(value, bool):
            raise JoplinValidationError(
                f"Invalid Joplin {name} value.",
                cause=f"{source} must be an integer from 1 to 65535.",
                try_this=(
                    "Correct the Joplin environment/config value or run `joplin-cli doctor`."
                ),
            )
        if isinstance(value, int):
            parsed = value
        elif isinstance(value, str):
            try:
                parsed = int(value)
            except ValueError as exc:
                raise JoplinValidationError(
                    f"Invalid Joplin {name} value.",
                    cause=f"{source} must be an integer from 1 to 65535.",
                    try_this=(
                        "Correct the Joplin environment/config value or run `joplin-cli doctor`."
                    ),
                ) from exc
        else:
            raise JoplinValidationError(
                f"Invalid Joplin {name} value.",
                cause=f"{source} must be an integer from 1 to 65535.",
                try_this=(
                    "Correct the Joplin environment/config value or run `joplin-cli doctor`."
                ),
            )
        if name == "port" and not 1 <= parsed <= 65535:
            raise JoplinValidationError(
                f"Invalid Joplin {name} value.",
                cause=f"{source} must be an integer from 1 to 65535.",
                try_this=(
                    "Correct the Joplin environment/config value or run `joplin-cli doctor`."
                ),
            )
        return parsed

    def _parse_float(self, name: str, value: object, source: str) -> float:
        if isinstance(value, bool):
            raise JoplinValidationError(
                f"Invalid Joplin {name} value.",
                cause=f"{source} must be a finite positive number.",
                try_this=(
                    "Correct the Joplin environment/config value or run `joplin-cli doctor`."
                ),
            )
        if isinstance(value, (int, float, str)):
            try:
                parsed = float(value)
            except ValueError as exc:
                raise JoplinValidationError(
                    f"Invalid Joplin {name} value.",
                    cause=f"{source} must be a finite positive number.",
                    try_this=(
                        "Correct the Joplin environment/config value or run `joplin-cli doctor`."
                    ),
                ) from exc
        else:
            raise JoplinValidationError(
                f"Invalid Joplin {name} value.",
                cause=f"{source} must be a finite positive number.",
                try_this=(
                    "Correct the Joplin environment/config value or run `joplin-cli doctor`."
                ),
            )
        if not math.isfinite(parsed) or parsed <= 0:
            raise JoplinValidationError(
                f"Invalid Joplin {name} value.",
                cause=f"{source} must be a finite positive number.",
                try_this=(
                    "Correct the Joplin environment/config value or run `joplin-cli doctor`."
                ),
            )
        return parsed

    def _resolve_profile(
        self, profile: str | Path | None, config_data: dict[str, object]
    ) -> Path | None:
        explicit = profile or os.getenv("JOPLIN_PROFILE") or config_data.get("profile")
        if explicit:
            return Path(str(explicit)).expanduser()
        default_profile = Path.home() / ".config" / "joplin-desktop"
        return default_profile if default_profile.exists() else None

    def _resolve_token(
        self, token: str | None, config_data: dict[str, object], profile: Path | None
    ) -> tuple[str | None, str]:
        if token:
            return token, "cli-option"
        env_token = os.getenv("JOPLIN_TOKEN")
        if env_token:
            return env_token, "env"
        config_token = config_data.get("token")
        if isinstance(config_token, str) and config_token:
            return config_token, "config"
        profile_token = self._read_profile_token(profile)
        if profile_token:
            return profile_token, "profile"
        return None, "missing"

    def _read_profile_token(self, profile: Path | None) -> str | None:
        if profile is None:
            return None
        settings_path = profile / "settings.json"
        if not settings_path.exists():
            return None
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict):
            return None
        token = data.get("api.token")
        return token if isinstance(token, str) and token else None
