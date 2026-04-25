import pytest

from joplin_cli.sdk.errors import JoplinConflictError, JoplinValidationError
from joplin_cli.sdk.services.batch import BatchService


class FakeNotes:
    def __init__(self):
        self.deleted = []

    def delete(self, note_id):
        self.deleted.append(note_id)


class FakeSearch:
    def query(self, query, limit=None):
        return [{"id": "n1", "title": "One"}, {"id": "n2", "title": "Two"}]


class TrackingSearch:
    def __init__(self):
        self.queries = []

    def query(self, query, limit=None):
        self.queries.append(query)
        return []


def test_delete_dry_run_returns_confirmation_token():
    batch = BatchService(notes=FakeNotes(), search=FakeSearch(), tags=None)

    result = batch.delete_by_query("tag:temporary", dry_run=True)

    assert result["count"] == 2
    assert result["confirm"].startswith("delete-2-notes-")
    assert result["deleted"] is False


def test_delete_dry_run_includes_stable_preview_of_affected_notes():
    batch = BatchService(notes=FakeNotes(), search=FakeSearch(), tags=None)

    result = batch.delete_by_query("tag:temporary", dry_run=True)

    assert result["preview"] == [
        {"id": "n1", "title": "One"},
        {"id": "n2", "title": "Two"},
    ]


def test_delete_requires_matching_confirmation_token():
    notes = FakeNotes()
    batch = BatchService(notes=notes, search=FakeSearch(), tags=None)

    dry_run = batch.delete_by_query("tag:temporary", dry_run=True)
    result = batch.delete_by_query("tag:temporary", confirm=dry_run["confirm"])

    assert result["deleted"] is True
    assert notes.deleted == ["n1", "n2"]


def test_delete_without_confirmation_raises_conflict_and_does_not_delete():
    notes = FakeNotes()
    batch = BatchService(notes=notes, search=FakeSearch(), tags=None)

    with pytest.raises(JoplinConflictError) as exc_info:
        batch.delete_by_query("tag:temporary")

    assert "delete-2-notes" in str(exc_info.value)
    assert notes.deleted == []


def test_delete_rejects_count_only_confirmation_token():
    notes = FakeNotes()
    batch = BatchService(notes=notes, search=FakeSearch(), tags=None)

    with pytest.raises(JoplinConflictError):
        batch.delete_by_query("tag:temporary", confirm="delete-2-notes")

    assert notes.deleted == []


def test_delete_confirmation_token_is_bound_to_query():
    notes = FakeNotes()
    batch = BatchService(notes=notes, search=FakeSearch(), tags=None)
    dry_run = batch.delete_by_query("tag:temporary", dry_run=True)

    with pytest.raises(JoplinConflictError):
        batch.delete_by_query("tag:other", confirm=dry_run["confirm"])

    assert notes.deleted == []


def test_delete_yes_bypasses_confirmation_token():
    notes = FakeNotes()
    batch = BatchService(notes=notes, search=FakeSearch(), tags=None)

    result = batch.delete_by_query("tag:temporary", yes=True)

    assert result["deleted"] is True
    assert notes.deleted == ["n1", "n2"]


def test_delete_rejects_blank_query_before_searching():
    search = TrackingSearch()
    batch = BatchService(notes=FakeNotes(), search=search, tags=None)

    with pytest.raises(JoplinValidationError):
        batch.delete_by_query("   ", dry_run=True)

    assert search.queries == []
