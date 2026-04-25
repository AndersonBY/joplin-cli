from __future__ import annotations

from typing import Any

import httpx

from joplin_cli.sdk.errors import (
    JoplinApiError,
    JoplinAuthError,
    JoplinConnectionError,
    JoplinNotFoundError,
)


class JoplinHttpClient:
    def __init__(
        self,
        host: str,
        port: int,
        token: str,
        timeout: float = 10,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self._token = token
        self._client = httpx.Client(
            base_url=f"http://{host}:{port}",
            timeout=timeout,
            transport=transport,
        )

    def ping(self) -> str:
        try:
            response = self._client.get("/ping")
        except httpx.HTTPError:
            raise self._connection_error() from None
        if response.status_code >= 400:
            self._raise_api_error("GET", "ping", response)
        return response.text

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        files: Any | None = None,
    ) -> Any:
        return self.request("POST", path, params=params, json=json, data=data, files=files)

    def put(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        files: Any | None = None,
    ) -> Any:
        return self.request("PUT", path, params=params, json=json, data=data, files=files)

    def delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self.request("DELETE", path, params=params)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        files: Any | None = None,
    ) -> Any:
        response = self._send(method, path, params=params, json=json, data=data, files=files)
        return self._decode_response(response)

    def raw(self, path: str, *, params: dict[str, Any] | None = None) -> bytes:
        response = self._send("GET", path, params=params)
        return response.content

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> JoplinHttpClient:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _send(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        data: Any | None = None,
        files: Any | None = None,
    ) -> httpx.Response:
        clean_path = path.lstrip("/")
        request_params = dict(params or {})
        request_params["token"] = self._token

        try:
            response = self._client.request(
                method,
                f"/{clean_path}",
                params=request_params,
                json=json,
                data=data,
                files=files,
            )
        except httpx.HTTPError:
            raise self._connection_error() from None

        if response.status_code >= 400:
            self._raise_api_error(method, clean_path, response)
        return response

    def _raise_api_error(self, method: str, path: str, response: httpx.Response) -> None:
        cause = self._sanitize_token(self._error_cause(path, response))
        if response.status_code in {401, 403}:
            raise JoplinAuthError(
                "Joplin rejected the API token.",
                cause=cause,
                try_this="Check the token, then run `joplin-cli doctor`.",
                examples=["joplin-cli doctor", "joplin-cli auth"],
            )
        if response.status_code == 404:
            raise JoplinNotFoundError(
                "Joplin API resource was not found.",
                cause=cause,
                try_this="Check the item id or endpoint path, then retry the command.",
            )
        composed_cause = self._sanitize_token(
            f"{method.upper()} /{path} returned HTTP {response.status_code}: {cause}"
        )
        raise JoplinApiError(
            "Joplin API request failed.",
            cause=composed_cause,
            try_this="Run `joplin-cli doctor` to confirm the local Joplin data API is healthy.",
        )

    def _connection_error(self) -> JoplinConnectionError:
        return JoplinConnectionError(
            "Joplin data API is not reachable.",
            cause=f"Could not connect to http://{self.host}:{self.port}.",
            try_this=(
                "Open Joplin, enable the Web Clipper service, then run `joplin-cli doctor`."
            ),
            examples=["joplin-cli doctor", "joplin-cli --host 127.0.0.1 --port 41184 doctor"],
        )

    def _error_cause(self, path: str, response: httpx.Response) -> str:
        body = self._decode_response(response)
        if isinstance(body, dict):
            for key in ("error", "message"):
                value = body.get(key)
                if isinstance(value, str) and value:
                    return f"/{path} returned HTTP {response.status_code}: {value}"
        if isinstance(body, str) and body:
            return f"/{path} returned HTTP {response.status_code}: {body}"
        return f"/{path} returned HTTP {response.status_code}."

    def _decode_response(self, response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text

    def _sanitize_token(self, value: str) -> str:
        if not self._token:
            return value
        return value.replace(self._token, "[redacted]")
