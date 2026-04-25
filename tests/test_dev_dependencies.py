import tomllib
from pathlib import Path


def test_dev_dependencies_include_lint_tools():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    dev_dependencies = pyproject["dependency-groups"]["dev"]
    names = {dependency.split(">=", 1)[0] for dependency in dev_dependencies}

    assert {"ruff", "ty"} <= names
