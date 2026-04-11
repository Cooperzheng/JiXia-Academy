# src/engine/main.py
"""
稷下学宫争鸣引擎 — 示例入口

使用方式：
    python -m src.engine.main

前置条件：
    在项目根目录建 .env 文件，写入：
    GEMINI_API_KEY=your_key_here
"""
from dotenv import load_dotenv
load_dotenv()

import sys
from .persona import load_persona
from .discussion import Discussion
from .moderator import Moderator
from .interruptor import Interruptor
from .renderer import render, make_color_map, render_speech_stream, render_user_speech


def main() -> None:
    personas = [
        load_persona("confucius"),    # → 孔子
        load_persona("machiavelli"),  # → 马基雅维利
        load_persona("sunzi"),        # → 孙子
    ]

    # ── 议题输入 ──────────────────────────────────────────
    sep = "━" * 39
    print(f"\n{sep}")
    print("  稷 下 学 宫")
    print(f"{sep}")
    sys.stdout.write("  今日议题：")
    sys.stdout.flush()
    topic = input().strip()
    if not topic:
        topic = "乱世中，应该讲道德还是讲实力？"

    discussion = Discussion(
        personas=personas,
        topic=topic,
        rounds=6,
    )

    color_map = make_color_map(personas)

    # ── 开场提问 ──────────────────────────────────────────
    sep = "━" * 39
    print(f"\n{sep}")
    print("  你有什么想法想带入今天的争鸣？（直接回车跳过）")
    sys.stdout.write("  你  │  ")
    sys.stdout.flush()
    opening = input().strip()
    if opening:
        discussion.opening_statement = opening

    print(f"\n  [提示] 争鸣进行中，按 Tab 键可随时插话\n")

    # ── 初始化 Moderator 和 Interruptor ──────────────────
    moderator = Moderator(
        personas=personas,
        model=discussion.model,
        _client=discussion._client,
    )
    interruptor = Interruptor()
    interruptor.start()

    # ── 插话回调 ──────────────────────────────────────────
    def on_interrupt() -> None:
        sys.stdout.write("\n  你  │  ")
        sys.stdout.flush()
        try:
            user_text = input().strip()
        except EOFError:
            return

        if not user_text:
            return

        # 渲染用户发言
        render_user_speech(user_text)

        # 注入 history
        discussion.inject_user_speech(user_text)

        # 人格回应
        for speech in discussion.respond_to_user(user_text, moderator):
            render_speech_stream(speech, color_map)
            sys.stdout.write("\n")
            sys.stdout.flush()

    # ── 主争鸣循环 ────────────────────────────────────────
    try:
        render(
            discussion.run(),
            color_map,
            interruptor=interruptor,
            on_interrupt=on_interrupt,
        )
    finally:
        interruptor.stop()


if __name__ == "__main__":
    main()
