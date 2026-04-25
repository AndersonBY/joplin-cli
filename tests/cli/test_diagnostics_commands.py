import json

from typer.testing import CliRunner

from joplin_cli.cli.app import build_app
from joplin_cli.sdk.errors import JoplinConnectionError


class FakeHttp:
    def ping(self):
        return "JoplinClipperServer"


class FakeClient:
    def __init__(self):
        self.http = FakeHttp()


def app():
    return build_app(client_factory=lambda **kwargs: FakeClient())


def failing_app():
    def fail(**kwargs):
        raise JoplinConnectionError(
            "Cannot connect to Joplin server.",
            try_this="Start Joplin and enable the Web Clipper service.",
        )

    return build_app(client_factory=fail)


def test_status_outputs_json_without_token_value():
    result = CliRunner().invoke(app(), ["status", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert set(data) == {"server", "host", "port", "token", "token_source"}
    assert data == {
        "server": "online",
        "host": "127.0.0.1",
        "port": 41184,
        "token": "valid",
        "token_source": "profile",
    }
    assert "secret" not in result.output


def test_doctor_outputs_next_steps():
    result = CliRunner().invoke(app(), ["doctor"])

    assert result.exit_code == 0
    assert "Joplin server" in result.output
    assert "Next:" in result.output


def test_doctor_outputs_next_steps_on_connection_failure():
    result = CliRunner().invoke(failing_app(), ["doctor"])

    assert result.exit_code == 0
    assert "Joplin server: offline" in result.output
    assert "Token:" in result.output
    assert "Problem: Cannot connect to Joplin server." in result.output
    assert "Next:" in result.output


def test_alias_status_reports_available_when_no_command(monkeypatch):
    monkeypatch.setattr("joplin_cli.cli.commands.alias.shutil.which", lambda name: None)

    result = CliRunner().invoke(app(), ["alias", "status"])

    assert result.exit_code == 0
    assert "joplin alias: available" in result.output


def test_alias_status_reports_blocked_when_existing_command(monkeypatch):
    monkeypatch.setattr(
        "joplin_cli.cli.commands.alias.shutil.which",
        lambda name: "C:\\Tools\\joplin.exe",
    )

    result = CliRunner().invoke(app(), ["alias", "status"])

    assert result.exit_code == 0
    assert "joplin alias: blocked by existing command at C:\\Tools\\joplin.exe" in result.output


def test_alias_status_reports_already_installed_for_joplin_cli_alias(tmp_path, monkeypatch):
    alias_path = tmp_path / "joplin"
    alias_path.write_text("joplin-cli @args", encoding="utf-8")
    monkeypatch.setattr(
        "joplin_cli.cli.commands.alias.shutil.which",
        lambda name: str(alias_path),
    )

    result = CliRunner().invoke(app(), ["alias", "status"])

    assert result.exit_code == 0
    assert "joplin alias: already installed by joplin-cli" in result.output


def test_alias_install_refuses_existing_command_without_force(monkeypatch):
    monkeypatch.setattr(
        "joplin_cli.cli.commands.alias.shutil.which",
        lambda name: "C:\\Tools\\joplin.exe",
    )

    result = CliRunner().invoke(app(), ["alias", "install"])

    assert result.exit_code == 6
    assert "Error: A joplin command already exists." in result.output
    assert "C:\\Tools\\joplin.exe" in result.output


def test_alias_install_force_prints_safe_setup_instructions(monkeypatch):
    monkeypatch.setattr(
        "joplin_cli.cli.commands.alias.shutil.which",
        lambda name: "C:\\Tools\\joplin.exe",
    )

    result = CliRunner().invoke(app(), ["alias", "install", "--force"])

    assert result.exit_code == 0
    assert "does not modify your shell automatically" in result.output
    assert "function joplin" in result.output


def test_alias_install_overwrite_prints_safe_setup_instructions(monkeypatch):
    monkeypatch.setattr(
        "joplin_cli.cli.commands.alias.shutil.which",
        lambda name: "C:\\Tools\\joplin.exe",
    )

    result = CliRunner().invoke(app(), ["alias", "install", "--overwrite"])

    assert result.exit_code == 0
    assert "does not modify your shell automatically" in result.output
    assert "alias joplin" in result.output


def test_auth_output_redacts_token_and_gives_next_steps(monkeypatch):
    monkeypatch.setenv("JOPLIN_TOKEN", "secret")

    result = CliRunner().invoke(app(), ["auth"])

    assert result.exit_code == 0
    assert "secret" not in result.output
    assert "Token: valid" in result.output
    assert "joplin-cli config set token=..." in result.output


def test_config_path_outputs_config_path(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    monkeypatch.setenv("JOPLIN_CLI_CONFIG", str(config_path))

    result = CliRunner().invoke(app(), ["config", "path"])

    assert result.exit_code == 0
    assert str(config_path) in result.output


def test_config_set_redacts_token(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    monkeypatch.setenv("JOPLIN_CLI_CONFIG", str(config_path))

    result = CliRunner().invoke(app(), ["config", "set", "token=secret"])

    assert result.exit_code == 0
    assert "[redacted]" in result.output
    assert "secret" not in result.output


def test_config_set_redacts_token_like_keys(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    monkeypatch.setenv("JOPLIN_CLI_CONFIG", str(config_path))

    result = CliRunner().invoke(app(), ["config", "set", "api.token=secret"])

    assert result.exit_code == 0
    assert "api.token=[redacted]" in result.output
    assert "secret" not in result.output


def test_config_get_token_redacts_token(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"token": "secret"}', encoding="utf-8")
    monkeypatch.setenv("JOPLIN_CLI_CONFIG", str(config_path))

    result = CliRunner().invoke(app(), ["config", "get", "token"])

    assert result.exit_code == 0
    assert "token=[redacted]" in result.output
    assert "secret" not in result.output


def test_config_get_redacts_token_like_keys(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"api.token": "secret"}', encoding="utf-8")
    monkeypatch.setenv("JOPLIN_CLI_CONFIG", str(config_path))

    result = CliRunner().invoke(app(), ["config", "get", "api.token"])

    assert result.exit_code == 0
    assert "api.token=[redacted]" in result.output
    assert "secret" not in result.output


def test_config_unset_key_token_removes_token(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"token": "secret"}', encoding="utf-8")
    monkeypatch.setenv("JOPLIN_CLI_CONFIG", str(config_path))

    result = CliRunner().invoke(app(), ["config", "unset", "key=token"])

    assert result.exit_code == 0
    assert "unset token" in result.output
    assert "secret" not in config_path.read_text(encoding="utf-8")


def test_config_get_invalid_json_renders_joplin_error(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text("{", encoding="utf-8")
    monkeypatch.setenv("JOPLIN_CLI_CONFIG", str(config_path))

    result = CliRunner().invoke(app(), ["config", "get", "key=token"])

    assert result.exit_code == 2
    assert "Error: Invalid joplin-cli config file." in result.output
    assert "Traceback" not in result.output
