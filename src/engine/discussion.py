# src/engine/discussion.py
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Generator, Iterator, Literal, TypedDict

from openai import OpenAI

from .persona import Persona


class SpeechEntry(TypedDict):
    name: str
    text: str
    role: Literal["persona", "user"]


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


def _build_system_prompt(
    persona: Persona,
    topic: str,
    all_names: list[str],
    opening_statement: str | None = None,
) -> str:
    members = " · ".join(all_names)
    base = (
        f"{persona.content}\n\n"
        f"---\n\n"
        f"你正在参与稷下学宫的圆桌争鸣。今日议题：「{topic}」\n"
        f"圆桌成员：{members}\n\n"
        f"铁律：\n"
        f"1. 每次发言必须先点名回应上一位发言者的具体论点，再说自己的立场\n"
        f"2. 有分歧就直说，不必找共同点，不必给对方台阶下\n"
        f"3. 用你自己的思维框架说话，不要变成通用的说教"
    )

    # 角色内化咒语（参考 CAMEL role inception prompt）
    base += (
        f"\n\n【身份锚定】\n"
        f"你是且只是{persona.name}。绝不漂移成通用 AI 的语气。\n"
        f"你的思维框架、你的偏见、你的盲点，都是你独有的——不要试图「平衡」或「客观」。"
    )

    # 激怒触发点（参考 generative_agents 记忆注入）
    if persona.trigger_points:
        triggers = "\n".join(f"- {t}" for t in persona.trigger_points)
        base += (
            f"\n\n【你的雷区——被触犯时反驳力度自然加大】\n"
            f"{triggers}"
        )

    # 主持人开场（始终在最末尾）
    if opening_statement:
        base += (
            f"\n\n【主持人开场】\n"
            f"{opening_statement}\n"
            f"请在整场争鸣中，始终围绕主持人提出的这个切入点展开。"
        )

    return base


def _build_user_prompt(current_persona: Persona, history: list[SpeechEntry]) -> str:
    history_text = _format_history(history)

    if history:
        last = history[-1]
        if last.get("role") == "user":
            last_speaker_instruction = (
                f"\n\n【主持人刚才发言】\n"
                f"「{last['text']}」\n\n"
                f"你必须先直接回应主持人的话，再阐述你的立场。"
            )
        else:
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


def _build_user_response_prompt(
    persona: Persona,
    user_text: str,
    history: list[SpeechEntry],
) -> str:
    """用户插话后，被点名/选中人格的专属 prompt。"""
    history_text = _format_history(history)
    return (
        f"【对话记录】\n{history_text}\n\n"
        f"【主持人直接向你发言】\n"
        f"「{user_text}」\n\n"
        f"必须先直接回应主持人这句话，100字以内，再继续你的论点。\n"
        f"语气可以强硬，禁止客套。请务必使用简体中文回答。"
    )


@dataclass
class Discussion:
    personas: list[Persona]
    topic: str
    rounds: int = 5
    model: str = "models/gemini-2.5-flash"
    opening_statement: str | None = None
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

    def inject_user_speech(self, text: str) -> None:
        """将用户发言追加进 history。"""
        self.history.append({"name": "你", "text": text, "role": "user"})

    def _speak_stream(
        self,
        persona: Persona,
        user_text: str | None = None,
    ) -> SpeechStream:
        """调用流式 API，返回 SpeechStream。user_text 非空时使用用户回应 prompt。"""
        all_names = [p.name for p in self.personas]
        system = _build_system_prompt(
            persona, self.topic, all_names, self.opening_statement
        )
        if user_text is not None:
            user = _build_user_response_prompt(persona, user_text, self.history)
        else:
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

    def respond_to_user(
        self,
        user_text: str,
        moderator: "Moderator",  # type: ignore[name-defined]  # noqa: F821
    ) -> Generator[SpeechStream, None, None]:
        """
        决定回应人选，逐个 yield SpeechStream。
        解析 user_text 中的点名，传给 moderator。
        """
        named = [p.name for p in self.personas if p.name in user_text]

        speakers = moderator.next_speakers_for_user(
            self.history, user_text, named
        )

        for persona in speakers:
            speech = self._speak_stream(persona, user_text=user_text)
            yield speech
            self.history.append(
                {"name": persona.name, "text": speech.full_text(), "role": "persona"}
            )

    def run(self) -> Generator[str | SpeechStream, None, None]:
        """
        主争鸣循环。固定轮转。

        yield 类型：
          - str          → 开场框/散场框/空行，直接打印
          - SpeechStream → 流式发言，renderer 负责逐 chunk 输出
        """
        yield _make_header(self.topic, self.personas)
        yield ""

        for i in range(self.rounds):
            persona = self.personas[i % len(self.personas)]
            speech = self._speak_stream(persona)
            yield speech
            self.history.append(
                {"name": persona.name, "text": speech.full_text(), "role": "persona"}
            )
            yield ""

        yield _make_footer()
