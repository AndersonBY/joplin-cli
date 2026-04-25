from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_dir

from joplin_cli.sdk.errors import JoplinValidationError


@dataclass(frozen=True)
class JoplinCliConfig:
    path: Path | None = None

    @property
    def resolved_path(self) -> Path:
        if self.path is not None:
            return self.path
        return Path(user_config_dir("joplin-cli", "joplin-cli")) / "config.json"

    def read(self) -> dict[str, object]:
        path = self.resolved_path
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError as exc:
            raise JoplinValidationError(
                "Invalid joplin-cli config file.",
                cause=f"Config file is not valid UTF-8: {path}",
                try_this="Correct the config file or run `joplin-cli doctor`.",
            ) from exc
        except json.JSONDecodeError as exc:
            raise JoplinValidationError(
                "Invalid joplin-cli config file.",
                cause=f"Config file is not valid JSON: {path}",
                try_this="Correct the config file or run `joplin-cli doctor`.",
            ) from exc
        except OSError as exc:
            raise JoplinValidationError(
                "Cannot read joplin-cli config file.",
                cause=f"Config file could not be read: {path}",
                try_this="Check the config file permissions or run `joplin-cli doctor`.",
            ) from exc
        if not isinstance(data, dict):
            raise JoplinValidationError(
                "Invalid joplin-cli config file.",
                cause=f"Config file must contain a JSON object: {path}",
                try_this="Correct the config file or run `joplin-cli doctor`.",
            )
        return data

    def write(self, data: Mapping[str, object]) -> None:
        path = self.resolved_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        except OSError as exc:
            raise JoplinValidationError(
                "Cannot write joplin-cli config file.",
                cause=f"Config file could not be written: {path}",
                try_this="Check the config path and permissions or run `joplin-cli doctor`.",
            ) from exc

    def set_value(self, key: str, value: object) -> None:
        data = self.read()
        data[key] = value
        self.write(data)

    def unset_value(self, key: str) -> None:
        data = self.read()
        data.pop(key, None)
        self.write(data)
