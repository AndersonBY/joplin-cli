from pathlib import Path

from joplin_cli.sdk.client import JoplinClient
from joplin_cli.sdk.services.resources import ResourcesService
from joplin_cli.sdk.services.search import SearchService
from joplin_cli.sdk.services.tags import TagsService
from joplin_cli.sdk.services.todos import TodosService


class FakeHttp:
    def __init__(self):
        self.calls = []
        self.notes = {
            "n1": {"id": "n1", "title": "Note", "body": "Body"},
            "todo1": {"id": "todo1", "title": "Task", "is_todo": 1, "todo_completed": 0},
            "todo2": {"id": "todo2", "title": "Done", "is_todo": 1, "todo_completed": 123},
        }

    def get(self, path, *, params=None):
        self.calls.append(("GET", path, params))
        if path == "search":
            return {"items": [{"id": "n1", "title": "Match"}], "has_more": False}
        if path == "tags":
            return {"items": [{"id": "t1", "title": "project"}], "has_more": False}
        if path == "tags/t1/notes":
            return {"items": [{"id": "n1", "title": "Tagged"}], "has_more": False}
        if path == "resources":
            return {
                "items": [
                    {
                        "id": "r1",
                        "title": "file.pdf",
                        "mime": "application/pdf",
                        "size": 42,
                    }
                ],
                "has_more": False,
            }
        if path == "resources/r1":
            return {"id": "r1", "title": "file.pdf", "mime": "application/pdf", "size": 42}
        if path.startswith("notes/"):
            return self.notes[path.split("/")[-1]]
        if path == "notes":
            return {"items": list(self.notes.values()), "has_more": False}
        return {"items": [], "has_more": False}

    def post(self, path, *, json=None):
        self.calls.append(("POST", path, json))
        return {"id": "created", **(json or {})}

    def put(self, path, *, json=None):
        self.calls.append(("PUT", path, json))
        note_id = path.split("/")[-1]
        self.notes[note_id] = {"id": note_id, **self.notes.get(note_id, {}), **(json or {})}
        return self.notes[note_id]

    def delete(self, path):
        self.calls.append(("DELETE", path, None))
        return {}

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return {"id": "resource-created", "title": "file.txt"}

    def raw(self, path, *, params=None):
        self.calls.append(("RAW", path, params))
        return b"contents"


class ManySearchResultsHttp:
    def __init__(self):
        self.calls = []

    def get(self, path, *, params=None):
        self.calls.append(("GET", path, params))
        assert params is not None
        page = params["page"]
        start = (page - 1) * 100
        return {
            "items": [{"id": f"n{index}", "title": f"Match {index}"} for index in range(start, start + 100)],
            "has_more": page < 3,
        }


def test_search_passes_query_to_joplin_search_endpoint():
    http = FakeHttp()

    results = SearchService(http).query("hello", limit=5)

    assert results[0]["title"] == "Match"
    assert ("GET", "search", {"query": "hello", "limit": 5, "type": "note", "page": 1}) in http.calls


def test_search_caps_api_page_limit_while_preserving_total_limit():
    http = ManySearchResultsHttp()

    results = SearchService(http).query("x", limit=250)

    assert len(results) == 250
    assert http.calls[0] == ("GET", "search", {"query": "x", "limit": 100, "type": "note", "page": 1})
    assert http.calls[-1] == ("GET", "search", {"query": "x", "limit": 100, "type": "note", "page": 3})


def test_tags_list_create_notes_add_and_remove_note():
    http = FakeHttp()
    service = TagsService(http)

    tags = service.list(limit=5)
    created = service.create("work")
    notes = service.notes("t1")
    service.add_to_note("t1", "n1")
    service.remove_from_note("t1", "n1")

    assert tags[0].title == "project"
    assert created.title == "work"
    assert notes[0].title == "Tagged"
    assert ("GET", "tags", {"limit": 5, "page": 1}) in http.calls
    assert ("POST", "tags", {"title": "work"}) in http.calls
    assert ("GET", "tags/t1/notes", {"limit": 100, "page": 1}) in http.calls
    assert ("POST", "tags/t1/notes", {"id": "n1"}) in http.calls
    assert ("DELETE", "tags/t1/notes/n1", None) in http.calls


def test_tags_list_caps_api_page_limit():
    http = FakeHttp()

    TagsService(http).list(limit=250)

    assert ("GET", "tags", {"limit": 100, "page": 1}) in http.calls


def test_todos_create_sets_is_todo_flag():
    http = FakeHttp()

    todo = TodosService(http).create(title="Task", parent_id="f1")

    assert todo.is_todo == 1
    assert ("POST", "notes", {"title": "Task", "body": "", "is_todo": 1, "parent_id": "f1"}) in http.calls


def test_todos_list_and_state_updates_use_note_todo_fields():
    http = FakeHttp()
    service = TodosService(http)

    open_todos = service.list(open=True)
    done_todos = service.list(done=True)
    closed = service.done("todo1")
    reopened = service.open("todo2")
    toggled = service.toggle("todo1")

    assert [todo.id for todo in open_todos] == ["todo1"]
    assert [todo.id for todo in done_todos] == ["todo2"]
    assert closed.todo_completed > 0
    assert reopened.todo_completed == 0
    assert toggled.todo_completed == 0
    assert ("PUT", "notes/todo2", {"todo_completed": 0}) in http.calls


def test_todos_list_applies_limit_after_filtering_notes():
    http = FakeHttp()

    todos = TodosService(http).list(limit=1)

    assert [todo.id for todo in todos] == ["todo1"]
    get_call = next(call for call in http.calls if call[0] == "GET" and call[1] == "notes")
    assert get_call[2].get("limit") != 1


def test_resources_list_get_download_delete_and_attach_file(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("hello", encoding="utf-8")
    http = FakeHttp()
    service = ResourcesService(http)

    resources = service.list(limit=2)
    got = service.get("r1")
    contents = service.download("r1")
    resource = service.attach_file("n1", Path(path))
    deleted = service.delete("r1")

    assert resources[0].size == 42
    assert got.mime == "application/pdf"
    assert contents == b"contents"
    assert resource.id == "resource-created"
    assert deleted is None
    assert http.calls[0] == ("GET", "resources", {"limit": 2, "page": 1})
    assert ("GET", "resources/r1", None) in http.calls
    assert ("RAW", "resources/r1/file", None) in http.calls
    assert ("DELETE", "resources/r1", None) in http.calls
    assert ("PUT", "notes/n1", {"body": "Body\n[](:/resource-created)"}) in http.calls
    assert http.calls[3][0] == "POST"
    assert http.calls[3][1] == "resources"
    assert "files" in http.calls[3][2]
    assert "data" in http.calls[3][2]


def test_resources_list_caps_api_page_limit():
    http = FakeHttp()

    ResourcesService(http).list(limit=250)

    assert ("GET", "resources", {"limit": 100, "page": 1}) in http.calls


def test_client_wires_secondary_services():
    client = JoplinClient(token="secret-token")

    assert isinstance(client.search, SearchService)
    assert isinstance(client.tags, TagsService)
    assert isinstance(client.todos, TodosService)
    assert isinstance(client.resources, ResourcesService)

    client.close()
