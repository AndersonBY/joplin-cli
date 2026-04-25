# joplin-cli

Agent-friendly CLI and Python SDK for controlling a running local Joplin
desktop instance through the Joplin Clipper REST API.

[中文](README_ZH.md)

`joplin-cli` is designed for humans and coding agents that need predictable,
single-shot commands. It does not provide a REPL or TUI. Every command starts,
does one thing, prints useful output or a structured error, and exits.

## What It Does

- Connects to the local Joplin desktop Web Clipper service, usually at
  `http://127.0.0.1:41184`.
- Auto-discovers the local desktop profile token from Joplin's
  `settings.json` when Joplin is already configured on the machine.
- Exposes note, notebook, search, tag, todo, resource, diagnostic, config, and
  batch operations.
- Works as both an installable CLI and an importable Python SDK.
- Keeps token values out of normal output, diagnostics, error messages, and
  object representations.
- Returns agent-recoverable errors with `Error`, `Cause`, `Try`, and
  `Examples` sections where applicable.

## Installation

Install the published CLI from PyPI:

```bash
uv tool install joplin-cli
```

Upgrade an existing installation:

```bash
uv tool upgrade joplin-cli
```

Run directly from a checkout during development:

```bash
uv run joplin-cli --help
```

The package installs the `joplin-cli` command. It does not install a `joplin`
command by default, because that name may already belong to another Joplin
tool. Check the optional alias workflow with:

```bash
joplin-cli alias status
```

## Quick Start

```bash
uv tool install joplin-cli
joplin-cli doctor
joplin-cli notebooks list
joplin-cli notes list limit=10
joplin-cli search query="meeting notes" --json
```

`doctor` is the best first command. It checks whether the local Joplin server is
reachable, whether a token can be found, and what to run next.

## Agent Usage

Every command is single-shot. Use `--json` for machine-readable output.

```bash
joplin-cli notes read id=<note-id> --json
joplin-cli notes append id=<note-id> content="- [ ] Follow up"
joplin-cli batch delete query="tag:temporary" dry-run
```

Design rules that matter for agents:

- Use `key=value` arguments for predictable shell generation.
- Prefer `--json` when another tool will parse the result.
- Use `joplin-cli help` or `joplin-cli <group> --help` to discover commands.
- Errors explain the likely cause and a concrete next command.
- Validation errors exit with code `2`; connection, auth, not-found, and
  conflict errors use distinct exit codes.

## Authentication

Default behavior is intentionally low-friction for local use. If Joplin desktop
is already running and the Web Clipper service is enabled, `joplin-cli` tries to:

1. Connect to `127.0.0.1:41184`.
2. Find the Joplin desktop profile.
3. Read `api.token` from the profile `settings.json`.
4. Use the token without printing it.

Override discovery when needed:

```bash
$env:JOPLIN_TOKEN="..."; joplin-cli notes list
```

```bash
joplin-cli config set token=...
joplin-cli config set port=41184
joplin-cli config path
```

Supported environment variables:

- `JOPLIN_TOKEN`
- `JOPLIN_HOST`
- `JOPLIN_PORT`
- `JOPLIN_PROFILE`
- `JOPLIN_TIMEOUT`
- `JOPLIN_CLI_CONFIG`

Token precedence is: CLI option, environment variable, `joplin-cli` config,
auto-discovered Joplin profile.

## Common Commands

Notes:

```bash
joplin-cli notes list limit=20
joplin-cli notes read id=<note-id>
joplin-cli notes create title="Draft" body="# Draft"
joplin-cli notes update id=<note-id> title="New title"
joplin-cli notes append id=<note-id> content="- [ ] Follow up"
joplin-cli notes delete id=<note-id>
```

Notebooks:

```bash
joplin-cli notebooks list
joplin-cli notebooks tree
joplin-cli notebooks create title="Projects"
joplin-cli notebooks rename id=<notebook-id> title="Archive"
```

Search, tags, and todos:

```bash
joplin-cli search query="meeting notes" --json
joplin-cli tags list
joplin-cli tags add note=<note-id> tag=<tag-id>
joplin-cli todos list open
joplin-cli todos done id=<todo-id>
```

Resources:

```bash
joplin-cli resources list
joplin-cli resources attach note=<note-id> path="./file.pdf"
joplin-cli resources download id=<resource-id> output="./file.pdf"
```

## Output Formats

Text output is compact by default. Use JSON for automation:

```bash
joplin-cli notes list limit=10 --json
```

Other tabular formats are available where the output is list-like:

```bash
joplin-cli notes list limit=10 --format tsv
joplin-cli notes list limit=10 --format csv
```

## Batch Delete Safety

Batch delete is intentionally two-step. First run a dry run:

```bash
joplin-cli batch delete query="tag:temporary" dry-run
```

The dry run prints:

- The number of matching notes.
- A preview containing note IDs and titles.
- A confirmation token shaped like `delete-2-notes-<hash>`.

Only then run the destructive command:

```bash
joplin-cli batch delete query="tag:temporary" confirm=delete-2-notes-<hash>
```

The confirmation token is bound to the query and matched note IDs, not just the
count. A token from one query cannot confirm another query that happens to match
the same number of notes.

For automation that has already done its own safety checks, `yes` bypasses the
confirmation token:

```bash
joplin-cli batch delete query="tag:temporary" yes
```

## Python SDK

The SDK is the core layer; the CLI is a thin wrapper around it.

```python
from joplin_cli import JoplinClient

with JoplinClient.auto() as client:
    notes = client.notes.list(limit=10)
    first = notes[0]
    print(first.id, first.title)
```

Explicit connection:

```python
from joplin_cli import JoplinClient

client = JoplinClient(host="127.0.0.1", port=41184, token="...")
try:
    notebooks = client.notebooks.list()
finally:
    client.close()
```

Main SDK services:

- `client.notebooks`
- `client.notes`
- `client.search`
- `client.tags`
- `client.todos`
- `client.resources`
- `client.batch`

## Error Model

CLI errors are intended to be actionable without reading source code:

```text
Error: Parameter limit must be an integer.
Try: Use limit=5.
```

Exit codes:

- `0`: success
- `1`: general API/output error
- `2`: validation or CLI usage error
- `3`: local Joplin connection error
- `4`: authentication error
- `5`: not found
- `6`: conflict or destructive action not confirmed

## Development

Install the current checkout as a tool while testing packaging:

```bash
uv tool install . --force
```

Install dependencies and run checks:

```bash
uv sync
uv run pytest -v
uv run ruff check .
uv run ty check
```

Optional live smoke test against a running local Joplin desktop:

```powershell
$env:JOPLIN_CLI_LIVE="1"; uv run pytest tests/live/test_live_joplin.py -v
```

The live test only reads notebooks. It does not create, edit, or delete Joplin
data.

## Troubleshooting

If `doctor` says the server is offline:

```bash
joplin-cli doctor
```

Check that Joplin desktop is running and that the Web Clipper service is
enabled.

If token discovery fails, inspect configuration:

```bash
joplin-cli auth
joplin-cli config path
joplin-cli config get token
```

Token values are redacted in command output.
