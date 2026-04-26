from pathlib import Path


README = Path(__file__).resolve().parents[1] / "README.md"
README_ZH = Path(__file__).resolve().parents[1] / "README_ZH.md"


def test_readmes_include_quick_start_and_agent_usage_commands():
    readme = README.read_text(encoding="utf-8")
    readme_zh = README_ZH.read_text(encoding="utf-8")

    assert "[中文](README_ZH.md)" in readme
    assert "[English](README.md)" in readme_zh

    for heading in [
        "## What It Does",
        "## Installation",
        "## Quick Start",
        "## Agent Usage",
        "## Python SDK",
        "## Batch Delete Safety",
        "## Development",
    ]:
        assert heading in readme

    for heading in [
        "## 这个工具做什么",
        "## 安装",
        "## 快速开始",
        "## Agent 使用方式",
        "## Python SDK",
        "## 批量删除安全机制",
        "## 开发",
    ]:
        assert heading in readme_zh

    assert "Every command is single-shot." in readme
    assert "每个命令都是单次执行" in readme_zh

    for command in [
        "uv tool install joplin-cli",
        "joplin-cli doctor",
        "joplin-cli notebooks list",
        "joplin-cli notes list limit=10",
        'joplin-cli search query="meeting notes" --json',
        "joplin-cli notes read id=<note-id> --json",
        'joplin-cli notes create title="Draft" body=@./draft.md',
        'joplin-cli notes append id=<note-id> content="- [ ] Follow up"',
        'joplin-cli batch delete query="tag:temporary" dry-run',
        'joplin-cli batch delete query="tag:temporary" confirm=delete-2-notes-<hash>',
        "uv tool install . --force",
        "uv run ruff check .",
        "uv run ty check",
    ]:
        assert command in readme
        assert command in readme_zh
