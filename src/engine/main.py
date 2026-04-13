# src/engine/main.py
"""
稷下学宫争鸣引擎 — 入口

使用方式：
    # 交互模式
    python -m src.engine.main

    # 命令行指定
    python -m src.engine.main --topic "游戏应该让玩家快乐还是痛苦" --personas miyamoto-shigeru miyazaki-hidetaka kojima-hideo

    # 指定轮数
    python -m src.engine.main --rounds 9 --personas socrates descartes wittgenstein

    # 列出所有人格
    python -m src.engine.main --list

前置条件：
    .env 文件写入 GEMINI_API_KEY=your_key
    可选：TAVILY_API_KEY=your_key（不设置则用 DuckDuckGo）
    可选：SEARCH_DISABLED=1（关闭联网搜索）
"""
from dotenv import load_dotenv
load_dotenv()

import sys
import argparse
from pathlib import Path
from .persona import load_persona, list_available_personas
from .discussion import Discussion, SearchEvent
from .moderator import Moderator
from .interruptor import Interruptor
from .renderer import render, make_color_map, render_user_speech, render_search_event

_DEFAULT_PERSONAS = ["confucius", "machiavelli", "sunzi"]
_DEFAULT_TOPIC = "乱世中，应该讲道德还是讲实力？"
_SEP = "━" * 39
_FILE_EXTENSIONS = {".txt", ".md", ".pdf", ".csv", ".json"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="稷下学宫争鸣引擎")
    parser.add_argument("--topic", "-t", type=str, default=None)
    parser.add_argument("--personas", "-p", nargs="+", default=None, metavar="SLUG")
    parser.add_argument("--rounds", "-r", type=int, default=6)
    parser.add_argument("--list", "-l", action="store_true")
    return parser.parse_args()


def _parse_opening_input(text: str) -> tuple[str | None, str | None]:
    """
    识别输入是文件路径还是开场观点。
    返回 (opening_statement, file_path)，其中一个为 None。
    """
    text = text.strip()
    if not text:
        return None, None
    p = Path(text)
    if (
        text.startswith("./") or text.startswith("/")
        or (len(text) > 2 and text[1] == ":" and text[2] in "\\/")  # Windows 盘符
        or p.suffix.lower() in _FILE_EXTENSIONS
    ):
        return None, text
    return text, None


def _load_material(file_path: str) -> str | None:
    """读取文件内容，失败时返回 None 并打印错误。"""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        return content
    except FileNotFoundError:
        print(f"  [错误] 文件不存在：{file_path}")
        return None
    except Exception as e:
        print(f"  [错误] 读取文件失败：{e}")
        return None


def main() -> None:
    args = _parse_args()

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
        print(f"\n{_SEP}\n  稷 下 学 宫\n{_SEP}")
        print(f"  今日议题：{topic}")
    else:
        print(f"\n{_SEP}\n  稷 下 学 宫\n{_SEP}")
        sys.stdout.write("  今日议题：")
        sys.stdout.flush()
        topic = input().strip() or _DEFAULT_TOPIC

    discussion = Discussion(
        personas=personas,
        topic=topic,
        rounds=args.rounds,
    )

    color_map = make_color_map(personas)

    # ── 开场提问 / 资料注入 ───────────────────────────────
    print(f"\n{_SEP}")
    print("  你有什么想法或背景资料带入今天的争鸣？")
    print("  （直接写观点，或输入文件路径如 ./article.txt，回车跳过）")
    sys.stdout.write("  你  │  ")
    sys.stdout.flush()
    opening_raw = input().strip()

    if opening_raw:
        stmt, fpath = _parse_opening_input(opening_raw)
        if fpath:
            content = _load_material(fpath)
            if content:
                discussion.material_store.add(content, f"file:{fpath}", round=0)
                tokens_est = int(len(content.split()) * 1.5)
                print(f"  ✓ 已注入背景资料（约 {tokens_est} tokens）")
        elif stmt:
            discussion.opening_statement = stmt

    print(f"\n  [提示] 争鸣进行中，按 Tab 键可随时插话或注入资料\n")

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

        stmt, fpath = _parse_opening_input(user_text)

        if fpath:
            # 资料注入
            content = _load_material(fpath)
            if content:
                discussion.material_store.add(content, f"file:{fpath}")
                tokens_est = int(len(content.split()) * 1.5)
                print(f"  ✓ 已追加背景资料（约 {tokens_est} tokens），从下一位发言起生效")
            return

        # 普通插话
        render_user_speech(user_text)
        discussion.inject_user_speech(user_text)

        for persona_name, gen in discussion.respond_to_user(user_text, moderator):
            # 渲染人格回应（含可能的搜索事件）
            from .renderer import render_gen_stream
            full_text, _ = render_gen_stream(persona_name, gen, color_map)
            discussion.history.append(
                {"name": persona_name, "text": full_text, "role": "persona"}
            )
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
