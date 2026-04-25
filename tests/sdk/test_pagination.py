import httpx
import pytest

from joplin_cli.sdk.client import JoplinClient
from joplin_cli.sdk.errors import JoplinApiError
from joplin_cli.sdk.pagination import collect_pages


class FakeHttp:
    def __init__(self):
        self.pages = []

    def get(self, path, *, params=None):
        assert params is not None
        self.pages.append(params["page"])
        if params["page"] == 1:
            return {"items": [{"id": "1"}], "has_more": True}
        return {"items": [{"id": "2"}], "has_more": False}


def test_collect_pages_reads_until_has_more_is_false():
    http = FakeHttp()

    result = collect_pages(http, "notes", params={"limit": 1})

    assert result == [{"id": "1"}, {"id": "2"}]
    assert http.pages == [1, 2]


def test_collect_pages_honors_total_limit():
    http = FakeHttp()

    result = collect_pages(http, "notes", params={"limit": 1}, total_limit=1)

    assert result == [{"id": "1"}]
    assert http.pages == [1]


def test_collect_pages_does_not_mutate_params():
    http = FakeHttp()
    params = {"limit": 1}

    collect_pages(http, "notes", params=params, total_limit=1)

    assert params == {"limit": 1}


@pytest.mark.parametrize(
    "response",
    [
        "not a dict",
        {"items": "not a list", "has_more": False},
    ],
)
def test_collect_pages_rejects_unexpected_response_shape(response):
    class BadHttp:
        def get(self, path, *, params=None):
            return response

    with pytest.raises(JoplinApiError):
        collect_pages(BadHttp(), "notes")


@pytest.mark.parametrize(
    "response",
    [
        {"items": []},
        {"items": [{"id": "1"}], "has_more": "true"},
    ],
)
def test_collect_pages_rejects_invalid_has_more(response):
    class BadHttp:
        def get(self, path, *, params=None):
            return response

    with pytest.raises(JoplinApiError):
        collect_pages(BadHttp(), "notes", total_limit=1)


def test_client_constructor_composes_http_client_without_exposing_token():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"ok": True}))

    client = JoplinClient(
        host="localhost",
        port=1234,
        token="secret-token",
        timeout=3,
        transport=transport,
    )

    assert client.http.host == "localhost"
    assert client.http.port == 1234
    assert "secret-token" not in repr(client)
    assert "secret-token" not in repr(client.http)


def test_client_close_closes_http_client():
    client = JoplinClient(
        token="secret-token",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"ok": True})),
    )

    client.close()

    assert client.http._client.is_closed


def test_client_context_manager_closes_http_client_after_exit():
    with JoplinClient(
        token="secret-token",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"ok": True})),
    ) as client:
        assert not client.http._client.is_closed

    assert client.http._client.is_closed


def test_client_auto_uses_resolved_auth_without_exposing_token():
    client = JoplinClient.auto(
        host="localhost",
        port=1234,
        token="secret-token",
        timeout=3,
        profile="missing-profile",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"ok": True})),
    )

    assert client.http.host == "localhost"
    assert client.http.port == 1234
    assert "secret-token" not in repr(client)
    assert "secret-token" not in repr(client.http)
