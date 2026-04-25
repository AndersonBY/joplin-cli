from __future__ import annotations

import time
from typing import Any, List

from joplin_cli.sdk.models import Note
from joplin_cli.sdk.services.notes import NotesService


class TodosService:
    def __init__(self, http: Any) -> None:
        self._notes = NotesService(http)

    def list(
        self,
        open: bool = False,
        done: bool = False,
        limit: int | None = None,
    ) -> List[Note]:
        todos = [note for note in self._notes.list() if note.is_todo == 1]
        if open:
            todos = [note for note in todos if note.todo_completed == 0]
        if done:
            todos = [note for note in todos if note.todo_completed != 0]
        return todos if limit is None else todos[:limit]

    def create(self, title: str, body: str = "", parent_id: str | None = None) -> Note:
        return self._notes.create(title=title, body=body, parent_id=parent_id, is_todo=1)

    def done(self, note_id: str) -> Note:
        return self._notes.update(note_id, todo_completed=int(time.time() * 1000))

    def open(self, note_id: str) -> Note:
        return self._notes.update(note_id, todo_completed=0)

    def toggle(self, note_id: str) -> Note:
        todo = self._notes.get(note_id)
        if todo.todo_completed:
            return self.open(note_id)
        return self.done(note_id)
