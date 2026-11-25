"""Plan → 복사해서 옮겨 적기 쉬운 텍스트(Markdown)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .schema import Plan

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=False,
    trim_blocks=False,
    lstrip_blocks=False,
)


def render_markdown(plan: Plan) -> str:
    return _env.get_template("plan.md.j2").render(p=plan, c=plan.cover)
