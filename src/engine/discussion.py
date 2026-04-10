# src/engine/discussion.py
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Generator, TypedDict

from openai import OpenAI

from .persona import Persona


class SpeechEntry(TypedDict):
    name: str
    text: str


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
        f"你是稷下学宫的参与者。今日议题：「{topic}」\n"
        f"圆桌成员：{members}\n"
        f"规则：你必须直接回应前面的发言，不能各说各话。"
    )


def _build_user_prompt(current_persona: Persona, history: list[SpeechEntry]) -> str:
    history_text = _format_history(history)
    return (
        f"{history_text}\n\n"
        f"现在轮到你（{current_persona.name}）发言。\n"
        f"500字以内，直接表达立场，不必自报家门，不必客套。\n"
        f"若前面有你认为错误的观点，直接指出并反驳。\n"
        f"请务必使用简体中文回答。"
    )


@dataclass
class Discussion:
    personas: list[Persona]
    topic: str
    rounds: int = 5
    model: str = "models/gemini-2.5-flash"
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

    def _speak(self, persona: Persona) -> str:
        """调用 API，返回该人格本轮发言文本。失败时重试一次。"""
        all_names = [p.name for p in self.personas]
        system = _build_system_prompt(persona, self.topic, all_names)
        user = _build_user_prompt(persona, self.history)

        for attempt in range(2):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    max_tokens=1200,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                if attempt == 0:
                    continue
                return f"（{persona.name} 此刻无言——{e}）"
        # unreachable, satisfies type checker
        return f"（{persona.name} 此刻无言）"

    def run(self) -> Generator[str, None, None]:
        """
        主争鸣循环。固定轮转（personas[0]→[1]→...→[n-1]→[0]→...）。
        yield 每行可打印文本，包括开场框、发言行、散场框。
        """
        yield _make_header(self.topic, self.personas)
        yield ""

        for i in range(self.rounds):
            persona = self.personas[i % len(self.personas)]
            text = self._speak(persona)
            self.history.append({"name": persona.name, "text": text})
            yield f"{persona.name}\t│ {text}"
            yield ""

        yield _make_footer()
