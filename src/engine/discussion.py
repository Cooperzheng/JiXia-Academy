# src/engine/discussion.py
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Generator, Iterator, TypedDict

from openai import OpenAI

from .persona import Persona


class SpeechEntry(TypedDict):
    name: str
    text: str


@dataclass
class SpeechStream:
    """封装一次流式发言：持有人名和 chunk 迭代器，同时缓冲已消费的文本。"""
    name: str
    _iter: Iterator[str]
    _buf: list[str] = field(default_factory=list)

    def __iter__(self) -> Generator[str, None, None]:
        for chunk in self._iter:
            self._buf.append(chunk)
            yield chunk

    def full_text(self) -> str:
        return "".join(self._buf)


_HEADER_WIDTH = 39


def _make_header(topic: str, personas: list[Persona]) -> str:
    names = " · ".join(p.name for p in personas)
    sep = "━" * _HEADER_WIDTH
    return (
        f"{sep}\n"
        f"  稷 下 学 宫 · 今 日 议 题\n"
        f"{sep}\n"
        f"  「{topic}」\n"
        f"  入席：{names}\n"
        f"{sep}"
    )


def _make_footer() -> str:
    sep = "━" * _HEADER_WIDTH
    return f"{sep}\n  今日学宫，就此散场。你怎么看？\n{sep}"


def _format_history(history: list[SpeechEntry]) -> str:
    """将对话历史格式化为对齐的文本块，供 user prompt 使用。"""
    if not history:
        return "（尚无发言，你是第一位开口的。）"
    lines = []
    for entry in history:
        name = entry["name"]
        text = entry["text"]
        lines.append(f"{name}\t│ {text}")
    return "\n".join(lines)


def _build_system_prompt(persona: Persona, topic: str, all_names: list[str]) -> str:
    members = " · ".join(all_names)
    return (
        f"{persona.content}\n\n"
        f"---\n\n"
        f"你正在参与稷下学宫的圆桌争鸣。今日议题：「{topic}」\n"
        f"圆桌成员：{members}\n\n"
        f"铁律：\n"
        f"1. 每次发言必须先点名回应上一位发言者的具体论点，再说自己的立场\n"
        f"2. 有分歧就直说，不必找共同点，不必给对方台阶下\n"
        f"3. 用你自己的思维框架说话，不要变成通用的说教"
    )


def _build_user_prompt(current_persona: Persona, history: list[SpeechEntry]) -> str:
    history_text = _format_history(history)

    if history:
        last = history[-1]
        last_speaker_instruction = (
            f"\n\n【刚才发言的是：{last['name']}】\n"
            f"他/她说：「{last['text']}」\n\n"
            f"你必须先用一句话直接回应他/她的具体观点（可以反驳、质疑、或追问），"
            f"再阐述你自己的立场。不许跳过这步。"
        )
    else:
        last_speaker_instruction = "\n\n你是第一位开口的，直接亮出你的核心立场。"

    return (
        f"【对话记录】\n{history_text}"
        f"{last_speaker_instruction}\n\n"
        f"字数 300 字以内，语气可以强硬，禁止客套。\n"
        f"请务必使用简体中文回答。"
    )


@dataclass
class Discussion:
    personas: list[Persona]
    topic: str
    rounds: int = 5
    model: str = "gemini-2.0-flash"
    history: list[SpeechEntry] = field(default_factory=list, init=False)
    _client: OpenAI = field(init=False, repr=False)

    def __post_init__(self) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "环境变量 GEMINI_API_KEY 未设置。\n"
                "请执行：export GEMINI_API_KEY=your_key_here"
            )
        self._client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

    def _speak_stream(self, persona: Persona) -> SpeechStream:
        """调用流式 API，返回 SpeechStream（可实时迭代 chunk）。"""
        all_names = [p.name for p in self.personas]
        system = _build_system_prompt(persona, self.topic, all_names)
        user = _build_user_prompt(persona, self.history)

        def _chunks() -> Iterator[str]:
            try:
                stream = self._client.chat.completions.create(
                    model=self.model,
                    max_tokens=2000,
                    stream=True,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
            except Exception as e:
                yield f"（{persona.name} 此刻无言——{e}）"

        return SpeechStream(name=persona.name, _iter=_chunks())

    def run(self) -> Generator[str | SpeechStream, None, None]:
        """
        主争鸣循环。固定轮转（personas[0]→[1]→...→[n-1]→[0]→...）。

        yield 类型：
          - str          → 开场框/散场框/空行，直接打印
          - SpeechStream → 流式发言，renderer 负责逐 chunk 输出
        """
        yield _make_header(self.topic, self.personas)
        yield ""

        for i in range(self.rounds):
            persona = self.personas[i % len(self.personas)]
            speech = self._speak_stream(persona)
            yield speech                        # renderer 流式渲染
            # 等渲染完毕后，speech.full_text() 已填充
            self.history.append({"name": persona.name, "text": speech.full_text()})
            yield ""

        yield _make_footer()
