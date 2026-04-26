from importlib.metadata import metadata, version

from typer.testing import CliRunner

from joplin_cli import JoplinClient
from joplin_cli.cli.app import app


runner = CliRunner()


def test_package_exports_client_class():
    assert JoplinClient.__name__ == "JoplinClient"


def test_installed_distribution_has_version():
    assert version("joplin-cli") == "0.1.3"


def test_distribution_metadata_supports_pypi_discovery():
    package_metadata = metadata("joplin-cli")
    project_urls = package_metadata.get_all("Project-URL") or []
    classifiers = package_metadata.get_all("Classifier") or []
    keywords = package_metadata["Keywords"]

    assert "Homepage, https://github.com/AndersonBY/joplin-cli" in project_urls
    assert "PyPI, https://pypi.org/project/joplin-cli/" in project_urls
    assert "joplin" in keywords
    assert "agent-friendly" in keywords
    assert "Environment :: Console" in classifiers
    assert "Topic :: Utilities" in classifiers


def test_cli_help_path_exits_successfully():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Agent-friendly CLI for local Joplin desktop." in result.output
