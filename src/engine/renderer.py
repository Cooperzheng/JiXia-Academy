# src/engine/renderer.py
from __future__ import annotations

import sys
from typing import Callable, Generator

from rich.console import Console
from rich.text import Text

from .persona import Persona
from .discussion import SearchEvent
from .interruptor import Interruptor

__all__ = ["make_color_map", "render", "render_user_speech", "render_search_event"]

_PALETTE = ["cyan", "yellow", "magenta", "green", "red"]
_SEPARATOR_CHAR = "━"
_STAGE_PREFIX = "*"

_console = Console()

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
    return {
        p.name: _PALETTE[i % len(_PALETTE)]
        for i, p in enumerate(personas)
    }


def _render_separator(line: str) -> None:
    _console.print(f"[bold white]{line}[/bold white]")


def _render_stage(line: str) -> None:
    _console.print(f"[dim italic]{line}[/dim italic]")


def render_user_speech(text: str) -> None:
    t = Text()
    t.append("你", style="bold white")
    t.append("  │  ", style="white dim")
    t.append(text, style="white")
    _console.print(t)


def render_search_event(event: SearchEvent) -> None:
    """渲染搜索状态提示（dim 样式）。"""
    if not event.done:
        _console.print(f"  [dim]🔍 {event.name} 正在查证：{event.query}...[/dim]")
    elif event.count > 0:
        _console.print(f"  [dim]✓  {event.name} 查证完毕（{event.count} 篇来源）[/dim]")


def render(
    lines: Generator,
    color_map: dict[str, str],
    interruptor: Interruptor | None = None,
    on_interrupt: Callable[[], None] | None = None,
) -> None:
    """
    消费 discussion.run() 的输出，用 rich 渲染每一项。

    协议：
      "__PERSONA_START__:{name}" → 打印姓名前缀，进入发言模式
      "__PERSONA_END__"          → 发言结束，换行
      SearchEvent                → 显示搜索状态
      普通 str chunk             → 发言模式下直接写 stdout（带颜色）
      空字符串                   → 空行
      含 ━ 的字符串              → 分隔线
    """
    out = sys.stdout
    current_name: str | None = None
    current_color: str = "white"
    current_ansi: str = ""
    in_speech = False
    interrupted = False

    for item in lines:
        # 搜索事件
        if isinstance(item, SearchEvent):
            if in_speech:
                out.write("\n")
                out.flush()
                in_speech = False
            render_search_event(item)
            continue

        if not isinstance(item, str):
            continue

        # 发言开始标记
        if item.startswith("__PERSONA_START__:"):
            current_name = item[len("__PERSONA_START__:"):]
            current_color = color_map.get(current_name, "white")
            current_ansi = _ANSI_COLOR.get(current_color, "")
            # 打印「姓名 │ 」前缀
            prefix = Text()
            prefix.append(current_name, style=f"bold {current_color}")
            prefix.append("  │  ", style="white dim")
            _console.print(prefix, end="")
            in_speech = True
            interrupted = False
            continue

        # 发言结束标记
        if item == "__PERSONA_END__":
            if in_speech:
                out.write("\n")
                out.flush()
                in_speech = False
            if interrupted and on_interrupt:
                on_interrupt()
                if interruptor:
                    interruptor.clear()
                interrupted = False
            continue

        # 发言模式下的文本 chunk
        if in_speech:
            out.write(f"{current_ansi}{item}{_ANSI_RESET}")
            out.flush()
            if interruptor and interruptor.interrupt_flag.is_set():
                interrupted = True
                # 继续消费 generator 直到 __PERSONA_END__，但不输出
                # 通过设置 interrupted 标记，让 __PERSONA_END__ 处理
            continue

        # 非发言模式的普通内容
        if not item:
            _console.print()
        elif _SEPARATOR_CHAR in item:
            _render_separator(item)
        elif item.startswith(_STAGE_PREFIX) and item.endswith(_STAGE_PREFIX):
            _render_stage(item)
        else:
            _console.print(item)
