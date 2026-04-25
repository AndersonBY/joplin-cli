from __future__ import annotations

from joplin_cli.sdk.errors import JoplinError


def render_error(error: JoplinError) -> str:
    sections = [f"Error: {error.message}"]

    if error.cause:
        sections.append(f"Cause: {error.cause}")
    if error.try_this:
        sections.append(f"Try: {error.try_this}")
    if error.examples:
        examples = "\n".join(f"  {example}" for example in error.examples)
        sections.append(f"Examples:\n{examples}")

    docs = getattr(error, "docs", "")
    if docs:
        sections.append(f"Docs: {docs}")

    return "\n".join(sections)
