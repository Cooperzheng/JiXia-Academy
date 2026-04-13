# src/engine/discussion.py
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Generator, Iterator, Literal, TypedDict

from openai import OpenAI

from .persona import Persona
from .material import MaterialStore
from .search import SearchEngine, SearchResult, make_search_engine


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


@dataclass
class SearchEvent:
    """搜索事件，用于 renderer 显示搜索状态。"""
    name: str
    query: str
    done: bool = False
    count: int = 0


_HEADER_WIDTH = 39

_SEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": (
            "搜索互联网获取实时信息。仅在以下情况使用：\n"
            "- 议题涉及近期事件或最新数据\n"
            "- 需要具体数字或事实支撑论点\n"
            "- 对方引用了你不确定的信息\n"
            "不要为了显得博学而搜索。搜索是论据武器，不是装饰。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词，简洁精准"}
            },
            "required": ["query"]
        }
    }
}


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
    if not history:
        return "（尚无发言，你是第一位开口的。）"
    lines = []
    for entry in history:
        name = entry["name"]
        text = entry["text"]
        lines.append(f"{name}\t│ {text}")
    return "\n".join(lines)


def _format_search_results(results: list[SearchResult]) -> str:
    """将搜索结果格式化为注入 user message 的文本块。"""
    if not results:
        return ""
    lines = ["---", "（以下为搜索到的背景资料，请用你自己的思维框架和语言消化，不要直接引用来源或 URL）"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. 【{r.title}】")
        if r.snippet:
            lines.append(f"   {r.snippet}")
    lines.append("---")
    return "\n".join(lines)


def _build_system_prompt(
    persona: Persona,
    topic: str,
    all_names: list[str],
    opening_statement: str | None = None,
    material_store: MaterialStore | None = None,
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

    # 角色内化咒语
    base += (
        f"\n\n【身份锚定】\n"
        f"你是且只是{persona.name}。绝不漂移成通用 AI 的语气。\n"
        f"你的思维框架、你的偏见、你的盲点，都是你独有的——不要试图「平衡」或「客观」。"
    )

    # 激怒触发点
    if persona.trigger_points:
        triggers = "\n".join(f"- {t}" for t in persona.trigger_points)
        base += (
            f"\n\n【你的雷区——被触犯时反驳力度自然加大】\n"
            f"{triggers}"
        )

    # 背景资料（主持人注入）
    if material_store and not material_store.is_empty():
        base += material_store.get_prompt_block()

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
    material_store: MaterialStore = field(default_factory=MaterialStore)
    history: list[SpeechEntry] = field(default_factory=list, init=False)
    _client: OpenAI = field(init=False, repr=False)
    _search_engine: SearchEngine | None = field(init=False, repr=False)

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
        self._search_engine = make_search_engine()

    def inject_user_speech(self, text: str) -> None:
        self.history.append({"name": "你", "text": text, "role": "user"})

    def _speak_stream(
        self,
        persona: Persona,
        user_text: str | None = None,
    ) -> Generator[str | SearchEvent, None, None]:
        """
        调用 API，yield SearchEvent（搜索状态）和 str chunks（发言内容）。
        支持 Function Calling：若模型决定搜索，先 yield SearchEvent 再 yield 发言。
        """
        all_names = [p.name for p in self.personas]
        system = _build_system_prompt(
            persona, self.topic, all_names, self.opening_statement, self.material_store
        )
        if user_text is not None:
            user = _build_user_response_prompt(persona, user_text, self.history)
        else:
            user = _build_user_prompt(persona, self.history)

        tools = [_SEARCH_TOOL_SCHEMA] if self._search_engine else None

        try:
            # 第一次调用：可能触发 Function Calling
            response = self._client.chat.completions.create(
                model=self.model,
                max_tokens=2000,
                stream=False,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **({"tools": tools} if tools else {}),
            )

            choice = response.choices[0]

            # 处理 Function Calling
            if (
                tools
                and choice.finish_reason == "tool_calls"
                and choice.message.tool_calls
            ):
                tool_call = choice.message.tool_calls[0]
                import json
                args = json.loads(tool_call.function.arguments)
                query = args.get("query", "")

                yield SearchEvent(name=persona.name, query=query, done=False)

                results = []
                if self._search_engine:
                    try:
                        results = self._search_engine.search(query, max_results=3)
                    except Exception:
                        pass

                yield SearchEvent(name=persona.name, query=query, done=True, count=len(results))

                # 将搜索结果追加到 user message，第二次调用生成发言
                search_block = _format_search_results(results)
                user_with_search = f"{user}\n\n{search_block}" if search_block else user

                stream2 = self._client.chat.completions.create(
                    model=self.model,
                    max_tokens=2000,
                    stream=True,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_with_search},
                    ],
                )
                for chunk in stream2:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
            else:
                # 无 Function Calling，直接流式重新调用（保持流式体验）
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

    def generate_historian_report(self) -> Iterator[str]:
        """以学宫史官视角分析整场争鸣，流式输出。"""
        history_text = _format_history(self.history)
        names = " · ".join(p.name for p in self.personas)

        prompt = (
            f"以下是一场圆桌争鸣的完整记录：\n\n"
            f"议题：「{self.topic}」\n"
            f"参与者：{names}\n\n"
            f"{history_text}\n\n"
            f"请作为旁观者，用简洁的现代分析语言（不超过200字）回答两个问题：\n"
            f"1. 这场争鸣暴露了哪些真正的分歧断层？（参与者在哪些根本假设上不一致）\n"
            f"2. 留下了哪些悬而未决的问题？（争鸣结束后仍然开放的核心问题）\n\n"
            f"不要评判谁对谁错，不要替读者下结论。请用简体中文回答。"
        )

        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                max_tokens=600,
                stream=True,
                messages=[{"role": "user", "content": prompt}],
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            yield f"（史官此刻无言——{e}）"

    def respond_to_user(
        self,
        user_text: str,
        moderator: "Moderator",  # type: ignore[name-defined]  # noqa: F821
    ) -> Generator[tuple[str, Generator[str | SearchEvent, None, None]], None, None]:
        """决定回应人选，逐个 yield (persona_name, speech_generator)。"""
        named = [p.name for p in self.personas if p.name in user_text]
        speakers = moderator.next_speakers_for_user(self.history, user_text, named)

        for persona in speakers:
            gen = self._speak_stream(persona, user_text=user_text)
            yield persona.name, gen

    def run(self) -> Generator[str | SearchEvent, None, None]:
        """
        主争鸣循环。固定轮转。

        yield 类型：
          - str         → 开场框/散场框/空行/文本 chunk，renderer 直接输出
          - SearchEvent → 搜索状态，renderer 显示提示

        发言格式通过特殊 str 标记传递人名：
          "__PERSONA_START__:{name}"  → 新发言开始，renderer 打印姓名前缀
          "__PERSONA_END__"           → 发言结束，renderer 换行
        """
        yield _make_header(self.topic, self.personas)
        yield ""

        for i in range(self.rounds):
            persona = self.personas[i % len(self.personas)]
            buf: list[str] = []

            yield f"__PERSONA_START__:{persona.name}"
            for item in self._speak_stream(persona):
                if isinstance(item, SearchEvent):
                    yield item
                else:
                    buf.append(item)
                    yield item
            yield "__PERSONA_END__"

            self.history.append(
                {"name": persona.name, "text": "".join(buf), "role": "persona"}
            )
            yield ""

        yield _make_footer()
