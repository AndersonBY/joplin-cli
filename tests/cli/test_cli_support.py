from dataclasses import dataclass

import pytest

from joplin_cli.cli.errors import render_error
from joplin_cli.cli.output import normalize, render_output
from joplin_cli.cli.params import parse_kv_args
from joplin_cli.sdk.errors import JoplinAuthError, JoplinOutputError, JoplinValidationError


@dataclass(frozen=True)
class Item:
    id: str
    title: str


def test_parse_kv_args_supports_values_and_flags():
    parsed = parse_kv_args(["title=Hello world", "limit=5", "open"])

    assert parsed.values == {"title": "Hello world", "limit": "5"}
    assert parsed.flags == {"open"}


def test_parse_kv_args_normalizes_dashes_and_rejects_empty_keys():
    parsed = parse_kv_args(["parent-id=n1", "include-deleted"])

    assert parsed.values == {"parent_id": "n1"}
    assert parsed.flags == {"include_deleted"}

    with pytest.raises(JoplinValidationError):
        parse_kv_args(["=value"])


def test_render_output_json_includes_dataclasses():
    rendered = render_output([Item("n1", "Note")], output_format="json")

    assert '"id": "n1"' in rendered
    assert '"title": "Note"' in rendered


def test_normalize_removes_raw_from_dicts_and_dataclasses():
    @dataclass(frozen=True)
    class RawItem:
        id: str
        raw: dict[str, str]

    assert normalize({"id": "n1", "raw": {"secret": "value"}}) == {"id": "n1"}
    assert normalize(RawItem("n1", {"secret": "value"})) == {"id": "n1"}


def test_render_output_tsv_has_header():
    rendered = render_output([{"id": "n1", "title": "Note"}], output_format="tsv")

    assert rendered.splitlines()[0] == "id\ttitle"
    assert rendered.splitlines()[1] == "n1\tNote"


def test_render_output_tsv_uses_ordered_union_headers_for_heterogeneous_rows():
    rendered = render_output([{"id": "n1"}, {"id": "n2", "title": "Note"}], output_format="tsv")

    assert rendered.splitlines()[0] == "id\ttitle"
    assert rendered.splitlines()[1] == "n1\t"
    assert rendered.splitlines()[2] == "n2\tNote"


def test_render_output_csv_quotes_values_correctly():
    rendered = render_output([{"id": "n1", "title": "Hello, world"}], output_format="csv")

    assert rendered.splitlines()[0] == "id,title"
    assert rendered.splitlines()[1] == 'n1,"Hello, world"'


def test_render_output_csv_uses_ordered_union_headers_for_heterogeneous_rows():
    rendered = render_output([{"id": "n1"}, {"id": "n2", "title": "Note"}], output_format="csv")

    assert rendered.splitlines()[0] == "id,title"
    assert rendered.splitlines()[1] == "n1,"
    assert rendered.splitlines()[2] == "n2,Note"


def test_render_output_text_is_compact_for_lists():
    rendered = render_output([Item("n1", "Note")], output_format="text")

    assert rendered == "id: n1\ttitle: Note"


def test_render_output_rejects_unsupported_formats():
    with pytest.raises(JoplinOutputError):
        render_output({"id": "n1"}, output_format="xml")


def test_render_error_contains_agent_recovery_sections():
    error = JoplinAuthError(
        "Cannot access Joplin data API.",
        cause="Invalid token",
        try_this="Run `joplin-cli doctor`.",
        examples=["joplin-cli doctor"],
    )

    rendered = render_error(error)

    assert "Error:" in rendered
    assert "Cause:" in rendered
    assert "Try:" in rendered
    assert "Examples:" in rendered
