# joplin-cli

面向 Agent 和开发者的 Joplin 命令行工具与 Python SDK，用于通过 Joplin
desktop 的 Clipper REST API 控制本机正在运行的 Joplin。

[English](README.md)

`joplin-cli` 的核心目标是可脚本化、可预测、无交互。它不提供 REPL 或 TUI；
每个命令都是单次执行：启动、完成一个明确动作、输出结果或结构化错误，然后退出。

## 这个工具做什么

- 连接本机 Joplin desktop Web Clipper 服务，默认地址通常是
  `http://127.0.0.1:41184`。
- 当本机 Joplin 已经配置好时，自动从 desktop profile 的 `settings.json` 读取
  `api.token`。
- 提供 notes、notebooks、search、tags、todos、resources、diagnostics、config、
  batch 等能力。
- 同时作为 CLI 工具和可 import 的 Python SDK 使用。
- 正常输出、诊断输出、错误信息和对象 repr 都不打印 token 明文。
- 错误信息面向 Agent 设计，尽量包含 `Error`、`Cause`、`Try`、`Examples` 等可恢复信息。

## 安装

从 PyPI 安装已发布的 CLI：

```bash
uv tool install joplin-cli
```

升级已安装版本：

```bash
uv tool upgrade joplin-cli
```

开发时也可以从 checkout 直接运行：

```bash
uv run joplin-cli --help
```

默认只安装 `joplin-cli` 命令，不安装 `joplin` 命令，避免覆盖用户已有的 Joplin
相关工具。如需检查可选 alias：

```bash
joplin-cli alias status
```

## 快速开始

```bash
uv tool install joplin-cli
joplin-cli doctor
joplin-cli notebooks list
joplin-cli notes list limit=10
joplin-cli search query="meeting notes" --json
```

建议先运行 `doctor`。它会检查本机 Joplin 服务是否在线、token 是否可用，并给出下一步命令。

## Agent 使用方式

每个命令都是单次执行。需要机器解析时使用 `--json`。

```bash
joplin-cli notes read id=<note-id> --json
joplin-cli notes create title="Draft" body=@./draft.md
joplin-cli notes append id=<note-id> content="- [ ] Follow up"
joplin-cli batch delete query="tag:temporary" dry-run
```

长 Markdown 内容建议先写入 UTF-8 文件，再通过文本参数传给 CLI。
`body=@./draft.md` 会从磁盘读取 note body，`content=@./section.md`
会读取 append/prepend 的内容。如果确实要传入以 `@` 开头的字面量，
使用 `body=@@literal`。

对 Agent 友好的约定：

- 优先使用 `key=value` 参数，便于生成 shell 命令。
- 需要解析结果时使用 `--json`。
- 大段 `body` 或 `content` 使用 `@file`，不要把整段 Markdown 直接塞进 shell 命令。
- 使用 `joplin-cli help` 或 `joplin-cli <group> --help` 自发现命令。
- 错误信息会说明原因和下一条可尝试命令。
- validation 错误退出码为 `2`；连接、认证、未找到、冲突错误有独立退出码。

## 认证

默认流程尽量无感。如果 Joplin desktop 已经启动，并且 Web Clipper 服务已启用，
`joplin-cli` 会尝试：

1. 连接 `127.0.0.1:41184`。
2. 查找 Joplin desktop profile。
3. 从 profile 的 `settings.json` 读取 `api.token`。
4. 使用 token 发起请求，但不打印 token。

需要覆盖自动发现时可以用：

```bash
$env:JOPLIN_TOKEN="..."; joplin-cli notes list
```

```bash
joplin-cli config set token=...
joplin-cli config set port=41184
joplin-cli config path
```

支持的环境变量：

- `JOPLIN_TOKEN`
- `JOPLIN_HOST`
- `JOPLIN_PORT`
- `JOPLIN_PROFILE`
- `JOPLIN_TIMEOUT`
- `JOPLIN_CLI_CONFIG`

token 优先级为：CLI option、环境变量、`joplin-cli` config、自动发现的 Joplin profile。

## 常用命令

Notes：

```bash
joplin-cli notes list limit=20
joplin-cli notes read id=<note-id>
joplin-cli notes create title="Draft" body="# Draft"
joplin-cli notes create title="Draft" body=@./draft.md
joplin-cli notes update id=<note-id> title="New title"
joplin-cli notes update id=<note-id> body=@./draft.md
joplin-cli notes append id=<note-id> content="- [ ] Follow up"
joplin-cli notes append id=<note-id> content=@./section.md
joplin-cli notes delete id=<note-id>
```

Notebooks：

```bash
joplin-cli notebooks list
joplin-cli notebooks tree
joplin-cli notebooks create title="Projects"
joplin-cli notebooks rename id=<notebook-id> title="Archive"
```

Search、Tags、Todos：

```bash
joplin-cli search query="meeting notes" --json
joplin-cli tags list
joplin-cli tags add note=<note-id> tag=<tag-id>
joplin-cli todos list open
joplin-cli todos done id=<todo-id>
```

Resources：

```bash
joplin-cli resources list
joplin-cli resources attach note=<note-id> path="./file.pdf"
joplin-cli resources download id=<resource-id> output="./file.pdf"
```

## 输出格式

默认文本输出尽量紧凑。自动化场景建议使用 JSON：

```bash
joplin-cli notes list limit=10 --json
```

列表类输出也支持表格格式：

```bash
joplin-cli notes list limit=10 --format tsv
joplin-cli notes list limit=10 --format csv
```

## 批量删除安全机制

批量删除必须分两步。先 dry-run：

```bash
joplin-cli batch delete query="tag:temporary" dry-run
```

dry-run 会输出：

- 匹配到的 note 数量。
- 包含 note ID 和 title 的预览。
- 类似 `delete-2-notes-<hash>` 的确认 token。

确认无误后再执行删除：

```bash
joplin-cli batch delete query="tag:temporary" confirm=delete-2-notes-<hash>
```

确认 token 绑定 query 和匹配到的 note IDs，不只是绑定数量。因此，一个 query 的
dry-run token 不能拿去确认另一个刚好匹配相同数量 notes 的 query。

如果外层自动化已经完成自己的安全检查，也可以使用 `yes` 跳过确认 token：

```bash
joplin-cli batch delete query="tag:temporary" yes
```

## Python SDK

SDK 是核心层，CLI 是它的薄封装。

```python
from joplin_cli import JoplinClient

with JoplinClient.auto() as client:
    notes = client.notes.list(limit=10)
    first = notes[0]
    print(first.id, first.title)
```

显式连接：

```python
from joplin_cli import JoplinClient

client = JoplinClient(host="127.0.0.1", port=41184, token="...")
try:
    notebooks = client.notebooks.list()
finally:
    client.close()
```

主要 SDK services：

- `client.notebooks`
- `client.notes`
- `client.search`
- `client.tags`
- `client.todos`
- `client.resources`
- `client.batch`

## 错误模型

CLI 错误设计成不看源码也能恢复：

```text
Error: Parameter limit must be an integer.
Try: Use limit=5.
```

退出码：

- `0`：成功
- `1`：通用 API 或输出错误
- `2`：参数校验或 CLI 使用错误
- `3`：本机 Joplin 连接错误
- `4`：认证错误
- `5`：目标不存在
- `6`：冲突或破坏性操作未确认

## 开发

测试打包时，可以把当前 checkout 安装成 tool：

```bash
uv tool install . --force
```

安装依赖并运行检查：

```bash
uv sync
uv run pytest -v
uv run ruff check .
uv run ty check
```

可选：对本机正在运行的 Joplin desktop 跑 live smoke test：

```powershell
$env:JOPLIN_CLI_LIVE="1"; uv run pytest tests/live/test_live_joplin.py -v
```

live test 只读取 notebooks，不会创建、修改或删除 Joplin 数据。

## 发布

PyPI 发布已经配置为 GitHub Actions trusted publishing。创建并发布 GitHub
Release 后，`release.yml` workflow 会运行测试、lint、类型检查，构建发行文件，并在
不保存 PyPI token 的情况下发布到 PyPI。

创建 release 前，先更新 `pyproject.toml` 里的 `version`，并在本地验证：

```bash
uv run pytest -q
uv run ruff check .
uv run ty check
uv build
```

## 故障排查

如果 `doctor` 显示 server offline：

```bash
joplin-cli doctor
```

确认 Joplin desktop 已启动，并且 Web Clipper service 已启用。

如果 token 自动发现失败，检查配置：

```bash
joplin-cli auth
joplin-cli config path
joplin-cli config get token
```

命令输出会对 token 明文做脱敏。
