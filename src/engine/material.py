# src/engine/material.py
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Material:
    content: str
    source: str
    round: int = 0


@dataclass
class MaterialStore:
    _items: list[Material] = field(default_factory=list, repr=False)

    _TOKEN_LIMIT = 2000

    def add(self, content: str, source: str, round: int = 0) -> None:
        """注入一段资料。超出 token 限制时截断并提示。"""
        estimated_tokens = len(content.split()) * 1.5
        if estimated_tokens > self._TOKEN_LIMIT:
            # 按比例截断：保留 TOKEN_LIMIT / 1.5 个单词
            max_words = int(self._TOKEN_LIMIT / 1.5)
            words = content.split()
            content = " ".join(words[:max_words])
            print(
                f"[material] ⚠ 资料过长（约 {int(estimated_tokens)} tokens），"
                f"已截断至约 {self._TOKEN_LIMIT} tokens。来源：{source}"
            )
        self._items.append(Material(content=content, source=source, round=round))

    def get_prompt_block(self) -> str:
        """返回注入 system prompt 的背景资料块。"""
        if self.is_empty():
            return ""
        combined = "\n\n".join(m.content for m in self._items)
        return f"\n\n---\n## 背景资料（由主持人提供）\n{combined}\n---"

    def is_empty(self) -> bool:
        return len(self._items) == 0
