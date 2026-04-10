# src/engine/renderer.py
from __future__ import annotations

import sys
from typing import Generator, Union

from rich.console import Console
from rich.text import Text

from .persona import Persona
from .discussion import SpeechStream

__all__ = ["make_color_map", "render"]

_PALETTE = ["cyan", "yellow", "magenta", "green", "red"]
_SEPARATOR_CHAR = "━"
_STAGE_PREFIX = "*"

_console = Console()

# 预先构建颜色的 ANSI 转义码，chunk 输出时直接写 stdout，绕过 rich markup 解析
_ANSI_RESET = "\033[0m"
_ANSI_COLOR: dict[str, str] = {
    "cyan":    "\033[36m",
    "yellow":  "\033[33m",
    "magenta": "\033[35m",
    "green":   "\033[32m",
    "red":     "\033[31m",
    "white":   "\033[37m",
}


def make_color_map(personas: list[Persona]) -> dict[str, str]:
    """按调色板顺序为每个人格分配颜色，返回 {name: color} 映射。"""
    return {
        p.name: _PALETTE[i % len(_PALETTE)]
        for i, p in enumerate(personas)
    }


def _render_separator(line: str) -> None:
    """渲染开场框/散场框行（含 ━ 字符的行）。"""
    _console.print(f"[bold white]{line}[/bold white]")


def _render_stage(line: str) -> None:
    """渲染舞台提示行（以 * 开头和结尾的斜体灰色文本）。"""
    _console.print(f"[dim italic]{line}[/dim italic]")


def _render_speech_stream(speech: SpeechStream, color_map: dict[str, str]) -> None:
    """
    流式渲染一次发言：rich 渲染「姓名 │ 」前缀，
    chunk 正文直接写 stdout（绕过 rich markup 解析，零延迟）。
    """
    name = speech.name
    color = color_map.get(name, "white")

    # 前缀用 rich 渲染（只调用一次，没有性能问题）
    prefix = Text()
    prefix.append(f"{name}", style=f"bold {color}")
    prefix.append("  │  ", style="white dim")
    _console.print(prefix, end="")

    # chunk 直接写 stdout：无 markup 解析、无 flush 开销，真正实时
    ansi = _ANSI_COLOR.get(color, "")
    out = sys.stdout
    for chunk in speech:
        out.write(f"{ansi}{chunk}{_ANSI_RESET}")
        out.flush()

    # 发言结束换行
    out.write("\n")
    out.flush()


def render(
    lines: Generator[Union[str, SpeechStream], None, None],
    color_map: dict[str, str],
) -> None:
    """
    消费 discussion.run() 的输出，用 rich 渲染每一项。

    Args:
        lines:     discussion.run() 返回的 Generator（str 或 SpeechStream）
        color_map: make_color_map() 返回的 {name: color} 映射
    """
    for item in lines:
        if isinstance(item, SpeechStream):
            _render_speech_stream(item, color_map)
        elif not item:
            _console.print()
        elif _SEPARATOR_CHAR in item:
            _render_separator(item)
        elif item.startswith(_STAGE_PREFIX) and item.endswith(_STAGE_PREFIX):
            _render_stage(item)
        else:
            _console.print(item)
