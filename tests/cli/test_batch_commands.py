from typer.testing import CliRunner

from joplin_cli.cli.app import build_app
from joplin_cli.sdk.services.batch import BatchService


class FakeBatch:
    def __init__(self):
        self.calls = []

    def delete_by_query(self, query, **kwargs):
        self.calls.append({"query": query, **kwargs})
        return {
            "query": query,
            "count": 2,
            "confirm": "delete-2-notes",
            "deleted": kwargs.get("confirm") == "delete-2-notes",
        }


class FakeClient:
    def __init__(self):
        self.batch = FakeBatch()


class FakeNotes:
    def delete(self, note_id):
        raise AssertionError("dry-run must not delete notes")


class FakeSearch:
    def query(self, query, limit=None):
        return [{"id": "n1", "title": "One"}, {"id": "n2", "title": "Two"}]


class RealBatchClient:
    def __init__(self):
        self.batch = BatchService(notes=FakeNotes(), search=FakeSearch(), tags=None)


def test_batch_delete_dry_run_prints_confirm_token():
    result = CliRunner().invoke(
        build_app(client_factory=lambda **kwargs: FakeClient()),
        ["batch", "delete", "query=tag:temporary", "dry-run"],
    )

    assert result.exit_code == 0
    assert "delete-2-notes" in result.output


def test_batch_delete_dry_run_prints_preview_content():
    result = CliRunner().invoke(
        build_app(client_factory=lambda **kwargs: RealBatchClient()),
        ["batch", "delete", "query=tag:temporary", "dry-run"],
    )

    assert result.exit_code == 0
    assert "preview:" in result.output
    assert '"id": "n1"' in result.output
    assert '"title": "One"' in result.output


def test_batch_delete_forwards_confirm_and_yes_flags():
    client = FakeClient()

    result = CliRunner().invoke(
        build_app(client_factory=lambda **kwargs: client),
        ["batch", "delete", "query=tag:temporary", "confirm=delete-2-notes", "yes"],
    )

    assert result.exit_code == 0
    assert client.batch.calls == [
        {
            "query": "tag:temporary",
            "dry_run": False,
            "confirm": "delete-2-notes",
            "yes": True,
        }
    ]


def test_batch_delete_missing_query_does_not_create_client():
    created = False

    def client_factory(**kwargs):
        nonlocal created
        created = True
        return FakeClient()

    result = CliRunner().invoke(
        build_app(client_factory=client_factory),
        ["batch", "delete", "dry-run"],
    )

    assert result.exit_code == 2
    assert "Missing required parameter: query." in result.output
    assert created is False


def test_batch_delete_blank_query_does_not_create_client():
    created = False

    def client_factory(**kwargs):
        nonlocal created
        created = True
        return FakeClient()

    result = CliRunner().invoke(
        build_app(client_factory=client_factory),
        ["batch", "delete", "query=   ", "yes"],
    )

    assert result.exit_code == 2
    assert "Missing required parameter: query." in result.output
    assert created is False
