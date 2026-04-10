# src/engine/main.py
"""
稷下学宫争鸣引擎 — 示例入口

使用方式：
    python -m src.engine.main

前置条件：
    export GEMINI_API_KEY=your_key_here
"""
from .persona import load_persona
from .discussion import Discussion
from .renderer import render, make_color_map


def main() -> None:
    personas = [
        load_persona("confucius"),    # → 孔子
        load_persona("machiavelli"),  # → 马基雅维利
        load_persona("sunzi"),        # → 孙子
    ]

    discussion = Discussion(
        personas=personas,
        topic="乱世中，应该讲道德还是讲实力？",
        rounds=6,
    )

    color_map = make_color_map(personas)
    render(discussion.run(), color_map)


if __name__ == "__main__":
    main()
