from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release.yml"


def test_release_workflow_uses_pypi_trusted_publishing():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "release:" in workflow
    assert "types: [published]" in workflow
    assert "id-token: write" in workflow
    assert "contents: read" in workflow
    assert "astral-sh/setup-uv@" in workflow
    assert "uv build" in workflow
    assert "uv publish --trusted-publishing always" in workflow
    assert "UV_PUBLISH_TOKEN" not in workflow
    assert "PYPI_TOKEN" not in workflow
