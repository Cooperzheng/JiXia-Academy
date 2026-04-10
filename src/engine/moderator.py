# src/engine/moderator.py
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from openai import OpenAI

if TYPE_CHECKING:
    from .discussion import SpeechEntry
    from .persona import Persona

__all__ = ["Moderator"]


def _fuzzy_match(name: str, personas: list[Persona]) -> Persona | None:
    """在 personas 中模糊匹配名字，返回第一个包含该名字的人格。"""
    for p in personas:
        if name in p.name or p.name in name:
            return p
    return None


@dataclass
class Moderator:
    """
    决定用户插话后谁来回应。
    - 用户点名：定向回应
    - 未点名：调用 API 选 1-2 人
    - API 失败：fallback 到 personas[0]
    """
    personas: list[Persona]
    model: str
    _client: OpenAI

    def next_speakers_for_user(
        self,
        history: list[SpeechEntry],
        user_text: str,
        named: list[str],
    ) -> list[Persona]:
        """
        返回应回应用户的人格列表。
        named: 用户明确点名的名字列表（可为空）。
        """
        # 优先处理点名
        if named:
            result = []
            for name in named:
                p = _fuzzy_match(name, self.personas)
                if p:
                    result.append(p)
            if result:
                return result[:3]  # 最多3人

        # 无点名：调用 API 选 1-2 人
        try:
            return self._api_select(history, user_text)
        except Exception:
            return [self.personas[0]]

    def _api_select(
        self,
        history: list[SpeechEntry],
        user_text: str,
    ) -> list[Persona]:
        names = " · ".join(p.name for p in self.personas)
        recent = "\n".join(
            f"{e['name']}：{e['text'][:80]}..."
            for e in history[-3:]
            if e.get("role", "persona") == "persona"
        )

        prompt = (
            f"用户刚才说：「{user_text}」\n"
            f"圆桌成员：{names}\n"
            f"最近对话：\n{recent}\n\n"
            f"谁最应该回应这句话？选1-2人，只返回名字，逗号分隔，不含其他文字。"
        )

        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content.strip()

        result = []
        for part in raw.split(","):
            name = part.strip()
            p = _fuzzy_match(name, self.personas)
            if p and p not in result:
                result.append(p)

        return result[:2] if result else [self.personas[0]]
