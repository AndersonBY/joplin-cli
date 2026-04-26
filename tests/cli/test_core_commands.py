from dataclasses import dataclass
from pathlib import Path

from typer.testing import CliRunner

from joplin_cli.cli.app import build_app, main


@dataclass(frozen=True)
class Item:
    id: str
    title: str


class FakeClient:
    def __init__(self):
        self.notebooks = self
        self.notes = self
        self.search = self
        self.created = []
        self.queries = []
        self.lists = []

    def list(self, **kwargs):
        self.lists.append(kwargs)
        return [Item("n1", "Note")]

    def get(self, note_id):
        return {"id": note_id, "title": "Note", "body": "Body"}

    def create(self, **kwargs):
        self.created.append(kwargs)
        return {"id": "created", **kwargs}

    def query(self, query, **kwargs):
        self.queries.append({"query": query, **kwargs})
        return [{"id": "n1", "title": query}]


def app(client=None):
    return build_app(client_factory=lambda **kwargs: client or FakeClient())


def test_notes_list_accepts_key_value_params_and_json():
    result = CliRunner().invoke(app(), ["notes", "list", "limit=5", "--json"])

    assert result.exit_code == 0
    assert '"id": "n1"' in result.output


def test_notes_read_prints_note_body():
    result = CliRunner().invoke(app(), ["notes", "read", "id=n1"])

    assert result.exit_code == 0
    assert "Body" in result.output


def test_search_command_uses_query_parameter():
    result = CliRunner().invoke(app(), ["search", "query=hello", "--json"])

    assert result.exit_code == 0
    assert '"title": "hello"' in result.output


def test_notes_create_forwards_kwargs_and_outputs_created_note_json():
    client = FakeClient()

    result = CliRunner().invoke(
        app(client),
        ["notes", "create", "title=Draft", "body=Body", "parent_id=f1", "--json"],
    )

    assert result.exit_code == 0
    assert client.created == [{"title": "Draft", "body": "Body", "parent_id": "f1"}]
    assert '"id": "created"' in result.output
    assert '"body": "Body"' in result.output


def test_notes_create_reads_body_from_markdown_file(tmp_path: Path):
    client = FakeClient()
    note_file = tmp_path / "draft.md"
    note_file.write_text("# Draft\n\nCreated from disk.\n", encoding="utf-8")

    result = CliRunner().invoke(
        app(client),
        ["notes", "create", "title=Draft", f"body=@{note_file}", "--json"],
    )

    assert result.exit_code == 0
    assert client.created == [
        {"title": "Draft", "body": "# Draft\n\nCreated from disk.\n", "parent_id": None}
    ]


def test_notes_create_reports_missing_body_file_before_client_creation(tmp_path: Path):
    calls = {"client_factory": 0}
    missing = tmp_path / "missing.md"

    def raising_client_factory(**kwargs):
        calls["client_factory"] += 1
        raise AssertionError("client_factory should not be called")

    cli_app = build_app(client_factory=raising_client_factory)

    result = CliRunner().invoke(
        cli_app,
        ["notes", "create", "title=Draft", f"body=@{missing}"],
    )

    assert result.exit_code == 2
    assert "Error: Cannot read body from file." in result.output
    assert "Try: Use body=@./draft.md" in result.output
    assert calls["client_factory"] == 0


def test_notes_create_help_mentions_file_backed_body_values():
    result = CliRunner().invoke(app(), ["notes", "create", "--help"])

    assert result.exit_code == 0
    assert "body=@./draft.md" in result.output
    assert "@@literal" in result.output


def test_notebooks_list_uses_injected_client_factory_and_json():
    client = FakeClient()

    result = CliRunner().invoke(app(client), ["notebooks", "list", "--json"])

    assert result.exit_code == 0
    assert client.lists == [{"limit": None}]
    assert '"id": "n1"' in result.output


def test_root_without_subcommand_prints_getting_started_message():
    result = CliRunner().invoke(app(), [])

    assert result.exit_code == 0
    assert (
        "Run `joplin-cli help` or `joplin-cli doctor` to get started."
        in result.output
    )


def test_help_includes_cli_description():
    result = CliRunner().invoke(app(), ["--help"])

    assert result.exit_code == 0
    assert "Agent-friendly CLI for local Joplin desktop." in result.output


def test_help_command_prints_root_help_for_agents():
    result = CliRunner().invoke(app(), ["help"])

    assert result.exit_code == 0
    assert "Agent-friendly CLI for local Joplin desktop." in result.output
    assert "notes" in result.output
    assert "doctor" in result.output


def test_notes_list_supports_tsv_format():
    result = CliRunner().invoke(app(), ["notes", "list", "limit=5", "--format", "tsv"])

    assert result.exit_code == 0
    assert "id\ttitle" in result.output
    assert "n1\tNote" in result.output


def test_search_command_forwards_limit_parameter():
    client = FakeClient()

    result = CliRunner().invoke(app(client), ["search", "query=hello", "limit=7", "--json"])

    assert result.exit_code == 0
    assert client.queries == [{"query": "hello", "limit": 7}]


def test_invalid_limit_renders_agent_friendly_error_without_traceback():
    result = CliRunner().invoke(app(), ["notes", "list", "limit=abc"])

    assert result.exit_code == 2
    assert "Error: Parameter limit must be an integer." in result.output
    assert "Try: Use limit=5." in result.output
    assert "Traceback" not in result.output


def test_main_builds_and_invokes_app(monkeypatch):
    calls = {"build_app": 0, "app": 0}

    def fake_app():
        calls["app"] += 1

    def fake_build_app():
        calls["build_app"] += 1
        return fake_app

    monkeypatch.setattr("joplin_cli.cli.app.build_app", fake_build_app)

    main()

    assert calls == {"build_app": 1, "app": 1}
