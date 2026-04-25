import os

import pytest

from joplin_cli import JoplinClient

pytestmark = pytest.mark.skipif(
    os.getenv("JOPLIN_CLI_LIVE") != "1",
    reason="live Joplin tests require JOPLIN_CLI_LIVE=1",
)


def test_live_client_can_list_notebooks():
    with JoplinClient.auto() as client:
        notebooks = client.notebooks.list(limit=1)
    assert isinstance(notebooks, list)
