from typing import Any

import pytest

from joplin_cli.sdk.client import JoplinClient
from joplin_cli.sdk.models import Note, Notebook, Resource, Tag
from joplin_cli.sdk.services.notebooks import NotebooksService
from joplin_cli.sdk.services.notes import NotesService


class FakeHttp:
    def __init__(self):
        self.calls = []

    def get(self, path, *, params=None):
        self.calls.append(("GET", path, params))
        if path == "folders":
            return {"items": [{"id": "f1", "title": "Inbox"}], "has_more": False}
        if path == "notes/n1":
            return {"id": "n1", "title": "Title", "body": "Body", "parent_id": "f1"}
        if path == "notes/todo1":
            return {
                "id": "todo1",
                "title": "Todo",
                "body": "",
                "is_todo": 1,
                "todo_completed": 123,
            }
        return {"items": [{"id": "n1", "title": "Title", "parent_id": "f1"}], "has_more": False}

    def post(self, path, *, json=None):
        self.calls.append(("POST", path, json))
        return {"id": "created", **(json or {})}

    def put(self, path, *, json=None):
        self.calls.append(("PUT", path, json))
        return {"id": path.split("/")[-1], **(json or {})}

    def delete(self, path):
        self.calls.append(("DELETE", path, None))
        return {}


def test_notebooks_list_returns_models():
    service = NotebooksService(FakeHttp())

    result = service.list()

    assert result[0].id == "f1"
    assert result[0].title == "Inbox"


def test_notebooks_tree_returns_models():
    http = FakeHttp()
    service = NotebooksService(http)

    result = service.tree()

    assert result == [Notebook(id="f1", title="Inbox", raw={"id": "f1", "title": "Inbox"})]
    assert ("GET", "folders", {"page": 1}) in http.calls


def test_notebooks_create_rename_and_delete_use_expected_endpoints():
    http = FakeHttp()
    service = NotebooksService(http)

    created = service.create(title="Archive", parent_id="f1")
    renamed = service.rename(notebook_id="f1", title="Renamed")
    deleted = service.delete(notebook_id="f1")

    assert created.id == "created"
    assert renamed.title == "Renamed"
    assert deleted is None
    assert ("POST", "folders", {"title": "Archive", "parent_id": "f1"}) in http.calls
    assert ("PUT", "folders/f1", {"title": "Renamed"}) in http.calls
    assert ("DELETE", "folders/f1", None) in http.calls


def test_notes_create_maps_notebook_to_parent_id():
    http = FakeHttp()
    service = NotesService(http)

    note = service.create(title="Title", body="Body", parent_id="f1")

    assert note.id == "created"
    assert ("POST", "notes", {"title": "Title", "body": "Body", "parent_id": "f1"}) in http.calls


def test_notes_append_reads_current_body_and_updates_note():
    http = FakeHttp()
    service = NotesService(http)

    service.append("n1", "\nMore")

    assert ("PUT", "notes/n1", {"body": "Body\nMore"}) in http.calls


def test_notes_get_update_prepend_move_copy_and_delete_support_spec_keywords():
    http = FakeHttp()
    service = NotesService(http)

    got = service.get(note_id="n1")
    updated = service.update(note_id="n1", title="Updated")
    prepended = service.prepend(note_id="n1", content="First\n")
    moved = service.move(note_id="n1", parent_id="f2")
    copied = service.copy(note_id="n1", parent_id="f2")
    deleted = service.delete(note_id="n1")

    assert got.id == "n1"
    assert updated.title == "Updated"
    assert prepended.body == "First\nBody"
    assert moved.parent_id == "f2"
    assert copied.id == "created"
    assert deleted is None
    assert any(call[0] == "GET" and call[1] == "notes/n1" for call in http.calls)
    assert ("PUT", "notes/n1", {"title": "Updated"}) in http.calls
    assert ("PUT", "notes/n1", {"body": "First\nBody"}) in http.calls
    assert ("PUT", "notes/n1", {"parent_id": "f2"}) in http.calls
    assert ("POST", "notes", {"title": "Title", "body": "Body", "parent_id": "f2"}) in http.calls
    assert ("DELETE", "notes/n1", None) in http.calls


def test_notes_get_requests_fields_required_for_content_operations():
    http = FakeHttp()
    service = NotesService(http)

    service.get(note_id="n1")

    get_call = next(call for call in http.calls if call[0] == "GET" and call[1] == "notes/n1")
    params = get_call[2]
    assert params is not None
    assert set(params["fields"].split(",")) >= {
        "id",
        "title",
        "body",
        "parent_id",
        "is_todo",
        "todo_completed",
    }


def test_notes_list_for_notebook_uses_folder_notes_endpoint():
    http = FakeHttp()
    service = NotesService(http)

    result = service.list(parent_id="f1", limit=10)

    assert result[0].id == "n1"
    get_call = next(call for call in http.calls if call[0] == "GET" and call[1] == "folders/f1/notes")
    params = get_call[2]
    assert params is not None
    assert params["limit"] == 10
    assert params["page"] == 1
    assert set(params["fields"].split(",")) >= {
        "id",
        "title",
        "parent_id",
        "is_todo",
        "todo_completed",
    }


def test_notes_list_without_notebook_uses_top_level_notes_endpoint():
    http = FakeHttp()
    service = NotesService(http)

    result = service.list(parent_id=None)

    assert result[0].id == "n1"
    get_call = next(call for call in http.calls if call[0] == "GET" and call[1] == "notes")
    params = get_call[2]
    assert params is not None
    assert params["page"] == 1
    assert set(params["fields"].split(",")) >= {
        "id",
        "title",
        "parent_id",
        "is_todo",
        "todo_completed",
    }


def test_notes_create_omits_empty_parent_id():
    http = FakeHttp()
    service = NotesService(http)

    service.create(title="Title")

    assert ("POST", "notes", {"title": "Title", "body": ""}) in http.calls


def test_notes_create_sends_todo_flag_and_maps_returned_model():
    http = FakeHttp()
    service = NotesService(http)

    note = service.create(title="Todo", is_todo=1)

    assert note.is_todo == 1
    assert note.todo_completed == 0
    assert ("POST", "notes", {"title": "Todo", "body": "", "is_todo": 1}) in http.calls


def test_notes_copy_preserves_body_and_allows_parent_override():
    http = FakeHttp()
    service = NotesService(http)

    note = service.copy("n1", parent_id="f2")

    assert note.id == "created"
    assert ("POST", "notes", {"title": "Title", "body": "Body", "parent_id": "f2"}) in http.calls


def test_notes_copy_preserves_original_parent_when_target_is_not_supplied():
    http = FakeHttp()
    service = NotesService(http)

    note = service.copy(note_id="n1")

    assert note.parent_id == "f1"
    assert ("POST", "notes", {"title": "Title", "body": "Body", "parent_id": "f1"}) in http.calls


def test_client_wires_note_and_notebook_services():
    client = JoplinClient(token="secret-token")

    assert isinstance(client.notes, NotesService)
    assert isinstance(client.notebooks, NotebooksService)

    client.close()


def test_model_repr_excludes_raw_payload():
    notebook = Notebook(id="f1", title="Inbox", raw={"body": "large"})
    note = Note(id="n1", title="Title", raw={"body": "large"})

    assert "raw" not in repr(notebook)
    assert "large" not in repr(note)


def test_note_model_defaults_todo_fields_to_zero():
    note = Note(id="n1", title="Title")

    assert note.is_todo == 0
    assert note.todo_completed == 0


def test_note_model_maps_todo_fields_from_response():
    note = NotesService(FakeHttp()).get(note_id="todo1")

    assert note.is_todo == 1
    assert note.todo_completed == 123


def test_resource_model_matches_spec_shape():
    resource = Resource(id="r1", title="file.pdf", mime=None, size=None, raw={"blob": "large"})

    assert resource.id == "r1"
    assert resource.title == "file.pdf"
    assert resource.mime is None
    assert resource.size is None
    assert not hasattr(resource, "filename")
    assert "raw" not in repr(resource)
    assert "large" not in repr(resource)


def test_resource_model_requires_title():
    kwargs: dict[str, Any] = {"id": "r1"}
    with pytest.raises(TypeError):
        Resource(**kwargs)


def test_tag_model_matches_spec_shape():
    tag = Tag(id="t1", title="project", raw={"notes": ["n1"]})

    assert tag.id == "t1"
    assert tag.title == "project"
    assert "raw" not in repr(tag)
