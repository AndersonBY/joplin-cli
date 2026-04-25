import json
from pathlib import Path

from typer.testing import CliRunner

from joplin_cli.cli.app import build_app


class FakeService:
    def __init__(self, *, delete_returns_none=False, tag_mutations_return_none=False):
        self.calls = []
        self.delete_returns_none = delete_returns_none
        self.tag_mutations_return_none = tag_mutations_return_none

    def __getattr__(self, name):
        def method(*args, **kwargs):
            self.calls.append({"method": name, "args": list(args), "kwargs": kwargs})
            return {
                "method": name,
                "args": [_output_arg(arg) for arg in args],
                "kwargs": kwargs,
            }

        return method

    def list(self, **kwargs):
        self.calls.append({"method": "list", "args": [], "kwargs": kwargs})
        return [{"id": "x1", "title": "Item"}]

    def delete(self, item_id):
        self.calls.append({"method": "delete", "args": [item_id], "kwargs": {}})
        if self.delete_returns_none:
            return None
        return {"method": "delete", "args": [item_id], "kwargs": {}}

    def add_to_note(self, tag_id, note_id):
        self.calls.append({"method": "add_to_note", "args": [tag_id, note_id], "kwargs": {}})
        if self.tag_mutations_return_none:
            return None
        return {"method": "add_to_note", "args": [tag_id, note_id], "kwargs": {}}

    def remove_from_note(self, tag_id, note_id):
        self.calls.append(
            {"method": "remove_from_note", "args": [tag_id, note_id], "kwargs": {}}
        )
        if self.tag_mutations_return_none:
            return None
        return {"method": "remove_from_note", "args": [tag_id, note_id], "kwargs": {}}

    def download(self, resource_id):
        self.calls.append({"method": "download", "args": [resource_id], "kwargs": {}})
        return b"resource bytes"


def _output_arg(value):
    if isinstance(value, Path):
        return str(value)
    return value


class FakeClient:
    def __init__(self, *, none_delete_services=(), tag_mutations_return_none=False):
        self.notes = FakeService(delete_returns_none="notes" in none_delete_services)
        self.notebooks = FakeService(
            delete_returns_none="notebooks" in none_delete_services
        )
        self.tags = FakeService(tag_mutations_return_none=tag_mutations_return_none)
        self.todos = FakeService()
        self.resources = FakeService(delete_returns_none="resources" in none_delete_services)


def app(client=None):
    return build_app(client_factory=lambda **kwargs: client or FakeClient())


def assert_missing_key_output(command, expected_keys):
    result = CliRunner().invoke(app(), command)

    assert result.exit_code != 0
    output = result.output.lower()
    assert "missing required parameter" in output
    for key in expected_keys:
        assert key in output


def test_tags_list_command():
    result = CliRunner().invoke(app(), ["tags", "list", "--json"])

    assert result.exit_code == 0
    assert '"id": "x1"' in result.output


def test_todos_done_command():
    result = CliRunner().invoke(app(), ["todos", "done", "id=todo1", "--json"])

    assert result.exit_code == 0
    assert '"method": "done"' in result.output


def test_resources_info_command():
    result = CliRunner().invoke(app(), ["resources", "info", "id=r1", "--json"])

    assert result.exit_code == 0
    assert '"method": "get"' in result.output


def test_bare_commands_report_key_specific_missing_params():
    assert_missing_key_output(["notes", "read"], ["id"])
    assert_missing_key_output(["notebooks", "create"], ["title"])
    assert_missing_key_output(["tags", "add"], ["note"])
    assert_missing_key_output(["todos", "done"], ["id"])
    assert_missing_key_output(["resources", "info"], ["id"])


def test_notes_read_and_create_validate_required_params_before_client_creation():
    calls = {"client_factory": 0}

    def raising_client_factory(**kwargs):
        calls["client_factory"] += 1
        raise AssertionError("client_factory should not be called")

    cli_app = build_app(client_factory=raising_client_factory)

    read = CliRunner().invoke(cli_app, ["notes", "read"])
    create = CliRunner().invoke(cli_app, ["notes", "create"])

    assert read.exit_code != 0
    assert create.exit_code != 0
    assert "id" in read.output.lower()
    assert "title" in create.output.lower()
    assert calls["client_factory"] == 0


def test_notes_append_update_and_delete_commands():
    client = FakeClient()
    runner = CliRunner()

    append = runner.invoke(app(client), ["notes", "append", "id=n1", "content=more", "--json"])
    update = runner.invoke(
        app(client),
        ["notes", "update", "id=n1", "title=New", "body=Body", "--json"],
    )
    delete = runner.invoke(app(client), ["notes", "delete", "id=n1", "--json"])

    assert append.exit_code == 0
    assert update.exit_code == 0
    assert delete.exit_code == 0
    assert client.notes.calls == [
        {"method": "append", "args": ["n1", "more"], "kwargs": {}},
        {"method": "update", "args": ["n1"], "kwargs": {"title": "New", "body": "Body"}},
        {"method": "delete", "args": ["n1"], "kwargs": {}},
    ]
    assert '"method": "append"' in append.output
    assert '"method": "update"' in update.output
    assert '"method": "delete"' in delete.output


def test_notes_prepend_move_and_copy_commands():
    client = FakeClient()
    runner = CliRunner()

    prepend = runner.invoke(
        app(client),
        ["notes", "prepend", "id=n1", "content=intro", "--json"],
    )
    move = runner.invoke(
        app(client),
        ["notes", "move", "id=n1", "notebook=f1", "--json"],
    )
    copy = runner.invoke(
        app(client),
        ["notes", "copy", "id=n1", "notebook=f2", "--json"],
    )

    assert prepend.exit_code == 0
    assert move.exit_code == 0
    assert copy.exit_code == 0
    assert client.notes.calls == [
        {"method": "prepend", "args": ["n1", "intro"], "kwargs": {}},
        {"method": "move", "args": ["n1", "f1"], "kwargs": {}},
        {"method": "copy", "args": ["n1", "f2"], "kwargs": {}},
    ]


def test_notebooks_create_and_tree_commands():
    client = FakeClient()
    runner = CliRunner()

    create = runner.invoke(app(client), ["notebooks", "create", "title=Folder", "--json"])
    tree = runner.invoke(app(client), ["notebooks", "tree", "--json"])

    assert create.exit_code == 0
    assert tree.exit_code == 0
    assert client.notebooks.calls == [
        {"method": "create", "args": ["Folder"], "kwargs": {}},
        {"method": "tree", "args": [], "kwargs": {}},
    ]


def test_notebooks_rename_and_delete_commands():
    client = FakeClient()
    runner = CliRunner()

    rename = runner.invoke(
        app(client),
        ["notebooks", "rename", "id=f1", "title=Archive", "--json"],
    )
    delete = runner.invoke(app(client), ["notebooks", "delete", "id=f1", "--json"])

    assert rename.exit_code == 0
    assert delete.exit_code == 0
    assert client.notebooks.calls == [
        {"method": "rename", "args": ["f1", "Archive"], "kwargs": {}},
        {"method": "delete", "args": ["f1"], "kwargs": {}},
    ]


def test_tags_notes_add_and_remove_commands():
    client = FakeClient()
    runner = CliRunner()

    notes = runner.invoke(app(client), ["tags", "notes", "tag=t1", "--json"])
    add = runner.invoke(
        app(client),
        ["tags", "add", "note=n1", "tag=t1", "--json"],
    )
    remove = runner.invoke(
        app(client),
        ["tags", "remove", "note=n1", "tag=t1", "--json"],
    )

    assert notes.exit_code == 0
    assert add.exit_code == 0
    assert remove.exit_code == 0
    assert client.tags.calls == [
        {"method": "notes", "args": ["t1"], "kwargs": {}},
        {"method": "add_to_note", "args": ["t1", "n1"], "kwargs": {}},
        {"method": "remove_from_note", "args": ["t1", "n1"], "kwargs": {}},
    ]


def test_tag_mutations_output_confirmation_when_service_returns_none():
    client = FakeClient(tag_mutations_return_none=True)
    runner = CliRunner()

    add = runner.invoke(app(client), ["tags", "add", "note=n1", "tag=t1", "--json"])
    remove = runner.invoke(
        app(client),
        ["tags", "remove", "note=n1", "tag=t1", "--json"],
    )

    assert add.exit_code == 0
    assert remove.exit_code == 0
    assert json.loads(add.output) == {
        "success": True,
        "action": "add",
        "note": "n1",
        "tag": "t1",
    }
    assert json.loads(remove.output) == {
        "success": True,
        "action": "remove",
        "note": "n1",
        "tag": "t1",
    }


def test_todos_create_open_and_toggle_commands():
    client = FakeClient()
    runner = CliRunner()

    create = runner.invoke(
        app(client),
        ["todos", "create", "title=Call", "notebook=f1", "--json"],
    )
    open_result = runner.invoke(app(client), ["todos", "open", "id=t1", "--json"])
    toggle = runner.invoke(app(client), ["todos", "toggle", "id=t1", "--json"])

    assert create.exit_code == 0
    assert open_result.exit_code == 0
    assert toggle.exit_code == 0
    assert client.todos.calls == [
        {"method": "create", "args": [], "kwargs": {"title": "Call", "parent_id": "f1"}},
        {"method": "open", "args": ["t1"], "kwargs": {}},
        {"method": "toggle", "args": ["t1"], "kwargs": {}},
    ]


def test_resources_list_attach_and_delete_commands(tmp_path: Path):
    client = FakeClient()
    runner = CliRunner()
    resource_path = tmp_path / "attachment.txt"
    resource_path.write_text("attachment")

    list_result = runner.invoke(app(client), ["resources", "list", "--json"])
    attach = runner.invoke(
        app(client),
        [
            "resources",
            "attach",
            "note=n1",
            f"path={resource_path}",
            "--json",
        ],
    )
    delete = runner.invoke(app(client), ["resources", "delete", "id=r1", "--json"])

    assert list_result.exit_code == 0
    assert attach.exit_code == 0
    assert delete.exit_code == 0
    assert client.resources.calls == [
        {"method": "list", "args": [], "kwargs": {}},
        {"method": "attach_file", "args": ["n1", resource_path], "kwargs": {}},
        {"method": "delete", "args": ["r1"], "kwargs": {}},
    ]


def test_note_delete_outputs_fallback_when_service_returns_none():
    client = FakeClient(none_delete_services=("notes",))

    result = CliRunner().invoke(app(client), ["notes", "delete", "id=n1", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.output) == {"deleted": True, "id": "n1"}


def test_resources_download_writes_file(tmp_path: Path):
    output = tmp_path / "resource.bin"

    result = CliRunner().invoke(
        app(),
        ["resources", "download", "id=r1", f"output={output}", "--json"],
    )

    assert result.exit_code == 0
    assert output.read_bytes() == b"resource bytes"
    assert json.loads(result.output)["output"] == str(output)


def test_resources_download_refuses_to_overwrite_existing_file(tmp_path: Path):
    client = FakeClient()
    output = tmp_path / "resource.bin"
    output.write_bytes(b"existing")

    result = CliRunner().invoke(
        app(client),
        ["resources", "download", "id=r1", f"output={output}", "--json"],
    )

    assert result.exit_code != 0
    assert "existing" in result.output.lower() or "overwrite" in result.output.lower()
    assert output.read_bytes() == b"existing"
    assert client.resources.calls == []


def test_resources_download_overwrite_flag_allows_existing_output(tmp_path: Path):
    client = FakeClient()
    output = tmp_path / "resource.bin"
    output.write_bytes(b"existing")

    result = CliRunner().invoke(
        app(client),
        ["resources", "download", "id=r1", f"output={output}", "overwrite", "--json"],
    )

    assert result.exit_code == 0
    assert output.read_bytes() == b"resource bytes"
    assert client.resources.calls == [
        {"method": "download", "args": ["r1"], "kwargs": {}},
    ]


def test_todos_list_flags_forward_filters():
    client = FakeClient()
    runner = CliRunner()

    open_result = runner.invoke(app(client), ["todos", "list", "open", "--json"])
    done_result = runner.invoke(app(client), ["todos", "list", "done", "--json"])

    assert open_result.exit_code == 0
    assert done_result.exit_code == 0
    assert client.todos.calls == [
        {"method": "list", "args": [], "kwargs": {"open": True, "done": False}},
        {"method": "list", "args": [], "kwargs": {"open": False, "done": True}},
    ]
