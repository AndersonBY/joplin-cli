from importlib.metadata import version

from typer.testing import CliRunner

from joplin_cli import JoplinClient
from joplin_cli.cli.app import app


runner = CliRunner()


def test_package_exports_client_class():
    assert JoplinClient.__name__ == "JoplinClient"


def test_installed_distribution_has_version():
    assert version("joplin-cli") == "0.1.0"


def test_cli_help_path_exits_successfully():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Agent-friendly CLI for local Joplin desktop." in result.output
