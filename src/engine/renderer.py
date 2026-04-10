# src/engine/renderer.py
from __future__ import annotations

from typing import Generator

from rich.console import Console
from rich.text import Text

from .persona import Persona

__all__ = ["make_color_map", "render"]

_PALETTE = ["cyan", "yellow", "magenta", "green", "red"]
_SEPARATOR_CHAR = "━"
_STAGE_PREFIX = "*"

_console = Console()


def make_color_map(personas: list[Persona]) -> dict[str, str]:
    """按调色板顺序为每个人格分配颜色，返回 {name: color} 映射。"""
    return {
        p.name: _PALETTE[i % len(_PALETTE)]
        for i, p in enumerate(personas)
    }


def _render_separator(line: str) -> None:
    """渲染开场框/散场框行（含 ━ 字符的行）。"""
    _console.print(f"[bold white]{line}[/bold white]")


def _render_speech(line: str, color_map: dict[str, str]) -> None:
    """
    渲染发言行，格式：{name}\t│ {text}
    名字用人格专属色加粗，│ 白色，正文用人格专属色。
    """
    name, _, text = line.partition("\t│ ")
    name = name.strip()
    color = color_map.get(name, "white")
    t = Text()
    t.append(f"{name}", style=f"bold {color}")
    t.append("  │  ", style="white dim")
    t.append(text, style=color)
    _console.print(t)


def _render_stage(line: str) -> None:
    """渲染舞台提示行（以 * 开头和结尾的斜体灰色文本）。"""
    _console.print(f"[dim italic]{line}[/dim italic]")


def render(lines: Generator[str, None, None], color_map: dict[str, str]) -> None:
    """
    消费 discussion.run() 的输出，用 rich 渲染每一行。

    Args:
        lines: discussion.run() 返回的 Generator
        color_map: make_color_map() 返回的 {name: color} 映射
    """
    for line in lines:
        if not line:
            _console.print()
        elif _SEPARATOR_CHAR in line:
            _render_separator(line)
        elif "\t│ " in line:
            _render_speech(line, color_map)
        elif line.startswith(_STAGE_PREFIX) and line.endswith(_STAGE_PREFIX):
            _render_stage(line)
        else:
            _console.print(line)
