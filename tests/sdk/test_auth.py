import json

import pytest

from joplin_cli.sdk.auth import AuthResolver
from joplin_cli.sdk.config import JoplinCliConfig
from joplin_cli.sdk.errors import (
    JoplinApiError,
    JoplinAuthError,
    JoplinConflictError,
    JoplinConnectionError,
    JoplinError,
    JoplinNotFoundError,
    JoplinOutputError,
    JoplinValidationError,
)


def test_cli_token_wins_over_environment_and_profile(tmp_path, monkeypatch):
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "settings.json").write_text(json.dumps({"api.token": "profile-token"}))
    monkeypatch.setenv("JOPLIN_TOKEN", "env-token")

    config = JoplinCliConfig(path=tmp_path / "config.json")
    config.write({"token": "config-token"})

    resolved = AuthResolver(config=config).resolve(token="cli-token", profile=profile)

    assert resolved.token == "cli-token"
    assert resolved.token_source == "cli-option"


def test_environment_token_wins_over_config_and_profile(tmp_path, monkeypatch):
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "settings.json").write_text(json.dumps({"api.token": "profile-token"}))
    monkeypatch.setenv("JOPLIN_TOKEN", "env-token")

    config = JoplinCliConfig(path=tmp_path / "config.json")
    config.write({"token": "config-token"})

    resolved = AuthResolver(config=config).resolve(profile=profile)

    assert resolved.token == "env-token"
    assert resolved.token_source == "env"


def test_profile_token_is_used_when_no_override_exists(tmp_path, monkeypatch):
    monkeypatch.delenv("JOPLIN_TOKEN", raising=False)
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "settings.json").write_text(json.dumps({"api.token": "profile-token"}))

    resolved = AuthResolver(config=JoplinCliConfig(path=tmp_path / "missing.json")).resolve(
        profile=profile
    )

    assert resolved.token == "profile-token"
    assert resolved.token_source == "profile"


def test_config_token_wins_over_profile_when_no_override_exists(tmp_path, monkeypatch):
    monkeypatch.delenv("JOPLIN_TOKEN", raising=False)
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "settings.json").write_text(json.dumps({"api.token": "profile-token"}))

    config = JoplinCliConfig(path=tmp_path / "config.json")
    config.write({"token": "config-token"})

    resolved = AuthResolver(config=config).resolve(profile=profile)

    assert resolved.token == "config-token"
    assert resolved.token_source == "config"


def test_missing_token_raises_actionable_auth_error(tmp_path, monkeypatch):
    monkeypatch.delenv("JOPLIN_TOKEN", raising=False)

    error = None
    try:
        AuthResolver(config=JoplinCliConfig(path=tmp_path / "missing.json")).resolve(
            profile=tmp_path / "missing-profile"
        )
    except JoplinAuthError as exc:
        error = exc

    assert error is not None
    assert "no valid api token" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


def test_resolved_auth_repr_does_not_expose_token(tmp_path):
    resolved = AuthResolver(config=JoplinCliConfig(path=tmp_path / "missing.json")).resolve(
        token="secret-token"
    )

    assert "secret-token" not in repr(resolved)


def test_invalid_environment_port_raises_actionable_validation_error(tmp_path, monkeypatch):
    monkeypatch.setenv("JOPLIN_PORT", "abc")

    with pytest.raises(JoplinValidationError) as exc_info:
        AuthResolver(config=JoplinCliConfig(path=tmp_path / "missing.json")).resolve(
            token="secret-token"
        )

    error = exc_info.value
    assert "secret-token" not in str(error)
    assert "port" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


def test_invalid_environment_timeout_raises_actionable_validation_error(tmp_path, monkeypatch):
    monkeypatch.setenv("JOPLIN_TIMEOUT", "fast")

    with pytest.raises(JoplinValidationError) as exc_info:
        AuthResolver(config=JoplinCliConfig(path=tmp_path / "missing.json")).resolve(
            token="secret-token"
        )

    error = exc_info.value
    assert "secret-token" not in str(error)
    assert "timeout" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


@pytest.mark.parametrize(
    ("config_data", "expected_field"),
    [
        ({"port": "abc"}, "port"),
        ({"timeout": "fast"}, "timeout"),
        ({"port": []}, "port"),
        ({"timeout": []}, "timeout"),
        ({"port": 0}, "port"),
        ({"port": True}, "port"),
        ({"port": 65536}, "port"),
        ({"timeout": True}, "timeout"),
        ({"timeout": 0}, "timeout"),
        ({"timeout": -1}, "timeout"),
        ({"timeout": float("nan")}, "timeout"),
        ({"timeout": float("inf")}, "timeout"),
    ],
)
def test_invalid_config_numeric_values_raise_validation_error(
    tmp_path, config_data, expected_field
):
    config = JoplinCliConfig(path=tmp_path / "config.json")
    config.write(config_data)

    with pytest.raises(JoplinValidationError) as exc_info:
        AuthResolver(config=config).resolve(token="secret-token")

    error = exc_info.value
    assert "secret-token" not in str(error)
    assert expected_field in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


@pytest.mark.parametrize(
    "port",
    [
        True,
        0,
        65536,
    ],
)
def test_invalid_cli_port_raises_validation_error(tmp_path, port):
    with pytest.raises(JoplinValidationError) as exc_info:
        AuthResolver(config=JoplinCliConfig(path=tmp_path / "missing.json")).resolve(
            port=port,
            token="secret-token",
        )

    error = exc_info.value
    assert "secret-token" not in str(error)
    assert "port" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


@pytest.mark.parametrize(
    "port",
    [
        "0",
        "65536",
        "true",
    ],
)
def test_invalid_environment_port_range_raises_validation_error(tmp_path, monkeypatch, port):
    monkeypatch.setenv("JOPLIN_PORT", port)

    with pytest.raises(JoplinValidationError) as exc_info:
        AuthResolver(config=JoplinCliConfig(path=tmp_path / "missing.json")).resolve(
            token="secret-token"
        )

    error = exc_info.value
    assert "secret-token" not in str(error)
    assert "port" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


@pytest.mark.parametrize(
    "timeout",
    [
        True,
        0,
        -1,
        float("nan"),
        float("inf"),
    ],
)
def test_invalid_cli_timeout_raises_validation_error(tmp_path, timeout):
    with pytest.raises(JoplinValidationError) as exc_info:
        AuthResolver(config=JoplinCliConfig(path=tmp_path / "missing.json")).resolve(
            timeout=timeout,
            token="secret-token",
        )

    error = exc_info.value
    assert "secret-token" not in str(error)
    assert "timeout" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


@pytest.mark.parametrize(
    "timeout",
    [
        "0",
        "-1",
        "nan",
        "inf",
        "Infinity",
        "true",
    ],
)
def test_invalid_environment_timeout_range_raises_validation_error(
    tmp_path, monkeypatch, timeout
):
    monkeypatch.setenv("JOPLIN_TIMEOUT", timeout)

    with pytest.raises(JoplinValidationError) as exc_info:
        AuthResolver(config=JoplinCliConfig(path=tmp_path / "missing.json")).resolve(
            token="secret-token"
        )

    error = exc_info.value
    assert "secret-token" not in str(error)
    assert "timeout" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


def test_malformed_config_read_raises_validation_error(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{not json", encoding="utf-8")

    with pytest.raises(JoplinValidationError) as exc_info:
        JoplinCliConfig(path=config_path).read()

    error = exc_info.value
    assert "config" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


@pytest.mark.parametrize("raw_json", ["[]", "null"])
def test_non_object_config_read_raises_validation_error(tmp_path, raw_json):
    config_path = tmp_path / "config.json"
    config_path.write_text(raw_json, encoding="utf-8")

    with pytest.raises(JoplinValidationError) as exc_info:
        JoplinCliConfig(path=config_path).read()

    error = exc_info.value
    assert "config" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


def test_invalid_utf8_config_read_raises_validation_error(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_bytes(b"\xff\xfe")

    with pytest.raises(JoplinValidationError) as exc_info:
        JoplinCliConfig(path=config_path).read()

    error = exc_info.value
    assert "config" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


def test_set_value_preserves_malformed_config(tmp_path):
    config_path = tmp_path / "config.json"
    original = '{"token": "secret-token"'
    config_path.write_text(original, encoding="utf-8")

    with pytest.raises(JoplinValidationError) as exc_info:
        JoplinCliConfig(path=config_path).set_value("host", "127.0.0.1")

    error = exc_info.value
    assert "secret-token" not in str(error)
    assert "config" in str(error).lower()
    assert config_path.read_text(encoding="utf-8") == original


def test_invalid_utf8_profile_settings_behaves_like_missing_token(tmp_path, monkeypatch):
    monkeypatch.delenv("JOPLIN_TOKEN", raising=False)
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "settings.json").write_bytes(b"\xff\xfe")

    with pytest.raises(JoplinAuthError) as exc_info:
        AuthResolver(config=JoplinCliConfig(path=tmp_path / "missing.json")).resolve(
            profile=profile
        )

    error = exc_info.value
    assert "no valid api token" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


def test_malformed_profile_settings_behaves_like_missing_token(tmp_path, monkeypatch):
    monkeypatch.delenv("JOPLIN_TOKEN", raising=False)
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "settings.json").write_text("{not json", encoding="utf-8")

    with pytest.raises(JoplinAuthError) as exc_info:
        AuthResolver(config=JoplinCliConfig(path=tmp_path / "missing.json")).resolve(
            profile=profile
        )

    error = exc_info.value
    assert "no valid api token" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


def test_unset_value_preserves_malformed_config(tmp_path):
    config_path = tmp_path / "config.json"
    original = '{"token": "secret-token"'
    config_path.write_text(original, encoding="utf-8")

    with pytest.raises(JoplinValidationError) as exc_info:
        JoplinCliConfig(path=config_path).unset_value("token")

    error = exc_info.value
    assert "secret-token" not in str(error)
    assert "config" in str(error).lower()
    assert config_path.read_text(encoding="utf-8") == original


def test_missing_config_read_returns_empty_dict(tmp_path):
    assert JoplinCliConfig(path=tmp_path / "missing.json").read() == {}


def test_config_read_write_round_trips_utf8_text(tmp_path):
    config = JoplinCliConfig(path=tmp_path / "config.json")
    data = {"profile": "C:/Users/ASUS/Joplin/笔记", "label": "cafe-été"}

    config.write(data)

    assert config.read() == data


def test_config_write_wraps_os_error(tmp_path):
    parent = tmp_path / "not-a-dir"
    parent.write_text("file", encoding="utf-8")
    config = JoplinCliConfig(path=parent / "config.json")

    with pytest.raises(JoplinValidationError) as exc_info:
        config.write({"host": "127.0.0.1"})

    error = exc_info.value
    assert "config" in str(error).lower()
    assert "joplin-cli doctor" in error.try_this


def test_error_hierarchy_exit_codes_match_plan():
    assert JoplinError.exit_code == 1
    assert JoplinApiError.exit_code == 1
    assert JoplinOutputError.exit_code == 1
    assert JoplinValidationError.exit_code == 2
    assert JoplinConnectionError.exit_code == 3
    assert JoplinAuthError.exit_code == 4
    assert JoplinNotFoundError.exit_code == 5
    assert JoplinConflictError.exit_code == 6
