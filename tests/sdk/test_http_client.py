import pytest
import httpx

from joplin_cli.sdk.errors import (
    JoplinApiError,
    JoplinAuthError,
    JoplinConnectionError,
    JoplinNotFoundError,
)
from joplin_cli.sdk.http import JoplinHttpClient


def test_get_adds_token_and_decodes_json():
    seen_url = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_url
        seen_url = str(request.url)
        return httpx.Response(200, json={"items": [{"id": "n1"}], "has_more": False})

    client = JoplinHttpClient(
        "127.0.0.1",
        41184,
        "secret",
        transport=httpx.MockTransport(handler),
    )

    result = client.get("notes")

    assert result["items"][0]["id"] == "n1"
    assert "token=secret" in seen_url


def test_constructor_accepts_timeout_as_positional_argument():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text="ok"))

    client = JoplinHttpClient("127.0.0.1", 41184, "secret", 3, transport=transport)

    assert client.get("notes") == "ok"


def test_valid_json_without_json_content_type_decodes_object():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text='{"id": "n1"}'))
    client = JoplinHttpClient("127.0.0.1", 41184, "secret", transport=transport)

    result = client.get("notes/n1")

    assert result == {"id": "n1"}


def test_invalid_json_with_json_content_type_returns_text():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            text="not json",
            headers={"content-type": "application/json"},
        )
    )
    client = JoplinHttpClient("127.0.0.1", 41184, "secret", transport=transport)

    result = client.get("notes/n1")

    assert result == "not json"


def test_request_forwards_multipart_files_and_data():
    seen_content_type = ""
    seen_body = b""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_content_type, seen_body
        seen_content_type = request.headers["content-type"]
        seen_body = request.read()
        return httpx.Response(200, json={"id": "r1"})

    client = JoplinHttpClient(
        "127.0.0.1",
        41184,
        "secret",
        transport=httpx.MockTransport(handler),
    )

    result = client.request(
        "POST",
        "resources",
        files={"data": ("note.txt", b"hello", "text/plain")},
        data={"props": '{"title": "note.txt"}'},
    )

    assert result == {"id": "r1"}
    assert seen_content_type.startswith("multipart/form-data; boundary=")
    assert b'name="props"' in seen_body
    assert b'{"title": "note.txt"}' in seen_body
    assert b'name="data"; filename="note.txt"' in seen_body
    assert b"hello" in seen_body


def test_raw_returns_binary_response_content_unmodified():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b"\x00\xffdata"))
    client = JoplinHttpClient("127.0.0.1", 41184, "secret", transport=transport)

    result = client.raw("resources/r1/file")

    assert result == b"\x00\xffdata"


def test_close_closes_underlying_httpx_client():
    client = JoplinHttpClient(
        "127.0.0.1",
        41184,
        "secret",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, text="ok")),
    )

    client.close()

    assert client._client.is_closed


def test_context_manager_closes_underlying_httpx_client():
    with JoplinHttpClient(
        "127.0.0.1",
        41184,
        "secret",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, text="ok")),
    ) as client:
        assert not client._client.is_closed

    assert client._client.is_closed


def test_error_cause_sanitizes_token_from_path_and_string():
    transport = httpx.MockTransport(lambda request: httpx.Response(500, text="failure"))
    client = JoplinHttpClient("127.0.0.1", 41184, "secret", transport=transport)

    with pytest.raises(JoplinApiError) as error:
        client.get("notes?token=secret")

    assert "secret" not in error.value.cause
    assert "secret" not in str(error.value)


def test_unauthorized_response_maps_to_auth_error():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(403, json={"error": "Invalid token"})
    )
    client = JoplinHttpClient("127.0.0.1", 41184, "bad", transport=transport)

    try:
        client.get("notes")
    except JoplinAuthError as exc:
        assert "Invalid token" in exc.cause
    else:
        raise AssertionError("expected auth error")


def test_not_found_response_maps_to_not_found_error():
    transport = httpx.MockTransport(lambda request: httpx.Response(404, json={"error": "Not found"}))
    client = JoplinHttpClient("127.0.0.1", 41184, "secret", transport=transport)

    try:
        client.get("notes/missing")
    except JoplinNotFoundError as exc:
        assert "notes/missing" in exc.cause
    else:
        raise AssertionError("expected not found error")


def test_auth_error_does_not_include_token_in_string_or_repr():
    transport = httpx.MockTransport(lambda request: httpx.Response(401, json={"error": "Invalid token"}))
    client = JoplinHttpClient("127.0.0.1", 41184, "secret-token", transport=transport)

    try:
        client.get("notes")
    except JoplinAuthError as exc:
        assert "secret-token" not in str(exc)
        assert "secret-token" not in repr(exc)
    else:
        raise AssertionError("expected auth error")


def test_non_json_error_body_uses_response_text_as_cause():
    transport = httpx.MockTransport(lambda request: httpx.Response(500, text="plain failure"))
    client = JoplinHttpClient("127.0.0.1", 41184, "secret", transport=transport)

    try:
        client.get("notes")
    except JoplinApiError as exc:
        assert "plain failure" in exc.cause
    else:
        raise AssertionError("expected api error")


def test_ping_does_not_add_token():
    seen_url = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_url
        seen_url = str(request.url)
        return httpx.Response(200, text="JoplinClipperServer")

    client = JoplinHttpClient(
        "127.0.0.1",
        41184,
        "secret",
        transport=httpx.MockTransport(handler),
    )

    result = client.ping()

    assert result == "JoplinClipperServer"
    assert seen_url == "http://127.0.0.1:41184/ping"


def test_ping_maps_connection_errors_without_token_leak():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused secret-token", request=request)

    client = JoplinHttpClient(
        "127.0.0.1",
        41184,
        "secret-token",
        transport=httpx.MockTransport(handler),
    )

    try:
        client.ping()
    except JoplinConnectionError as exc:
        assert "Joplin data API is not reachable" in str(exc)
        assert "joplin-cli doctor" in str(exc)
        assert "secret-token" not in str(exc)
        assert "secret-token" not in repr(exc)
    else:
        raise AssertionError("expected connection error")


def test_tokenized_connection_error_does_not_leak_token_in_chained_cause():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"failed {request.url}", request=request)

    client = JoplinHttpClient(
        "127.0.0.1",
        41184,
        "secret-token",
        transport=httpx.MockTransport(handler),
    )

    try:
        client.get("notes")
    except JoplinConnectionError as exc:
        assert "secret-token" not in str(exc)
        assert "secret-token" not in repr(exc)
        assert "secret-token" not in exc.cause
        if exc.__cause__ is not None:
            assert "secret-token" not in str(exc.__cause__)
    else:
        raise AssertionError("expected connection error")
