# src/engine/main.py
"""
稷下学宫争鸣引擎 — 入口

使用方式：
    # 交互模式（在程序里输入议题和人格）
    python -m src.engine.main

    # 命令行指定
    python -m src.engine.main --topic "游戏应该让玩家快乐还是痛苦" --personas miyamoto-shigeru miyazaki-hidetaka kojima-hideo

    # 指定轮数
    python -m src.engine.main --rounds 9 --personas socrates descartes wittgenstein

前置条件：
    在项目根目录建 .env 文件，写入：
    GEMINI_API_KEY=your_key_here
"""
from dotenv import load_dotenv
load_dotenv()

import sys
import argparse
from .persona import load_persona, list_available_personas
from .discussion import Discussion
from .moderator import Moderator
from .interruptor import Interruptor
from .renderer import render, make_color_map, render_speech_stream, render_user_speech

_DEFAULT_PERSONAS = ["confucius", "machiavelli", "sunzi"]
_DEFAULT_TOPIC = "乱世中，应该讲道德还是讲实力？"
_SEP = "━" * 39


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="稷下学宫争鸣引擎")
    parser.add_argument(
        "--topic", "-t",
        type=str,
        default=None,
        help="今日议题（不指定则交互输入）",
    )
    parser.add_argument(
        "--personas", "-p",
        nargs="+",
        default=None,
        metavar="SLUG",
        help="人格 slug 列表，如 confucius machiavelli sunzi（不指定则使用默认三人组）",
    )
    parser.add_argument(
        "--rounds", "-r",
        type=int,
        default=6,
        help="争鸣轮数（默认 6）",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有可用人格后退出",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # ── 列出可用人格 ──────────────────────────────────────
    if args.list:
        print("\n可用人格：")
        for name in list_available_personas():
            print(f"  · {name}")
        return

    # ── 加载人格 ──────────────────────────────────────────
    persona_slugs = args.personas or _DEFAULT_PERSONAS
    try:
        personas = [load_persona(slug) for slug in persona_slugs]
    except Exception as e:
        print(f"错误：{e}")
        sys.exit(1)

    # ── 议题 ──────────────────────────────────────────────
    if args.topic:
        topic = args.topic
        print(f"\n{_SEP}")
        print("  稷 下 学 宫")
        print(f"{_SEP}")
        print(f"  今日议题：{topic}")
    else:
        print(f"\n{_SEP}")
        print("  稷 下 学 宫")
        print(f"{_SEP}")
        sys.stdout.write("  今日议题：")
        sys.stdout.flush()
        topic = input().strip() or _DEFAULT_TOPIC

    discussion = Discussion(
        personas=personas,
        topic=topic,
        rounds=args.rounds,
    )

    color_map = make_color_map(personas)

    # ── 开场提问 ──────────────────────────────────────────
    print(f"\n{_SEP}")
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

        render_user_speech(user_text)
        discussion.inject_user_speech(user_text)

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

    # ── 史官层 ────────────────────────────────────────────
    sys.stdout.write(f"\n{_SEP}\n  学宫史官\n{_SEP}\n")
    sys.stdout.flush()
    for chunk in discussion.generate_historian_report():
        sys.stdout.write(chunk)
        sys.stdout.flush()
    sys.stdout.write("\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
