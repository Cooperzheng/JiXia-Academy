from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path


# 项目根目录（此文件位于 src/engine/，上溯两级）
_ROOT = Path(__file__).parent.parent.parent
_PERSONAS_DIR = _ROOT / "personas"
_SEARCH_DIRS = ["historical", "fictional", "modern"]


class PersonaNotFoundError(Exception):
    """找不到人格文件时抛出，错误信息包含所有可用人格名。"""
    pass


@dataclass
class Persona:
    name: str      # 从 frontmatter name: 字段读取的显示名，如"孔子"
    content: str   # .md 文件全文，直接塑入 system prompt


def _extract_name_from_frontmatter(content: str) -> str:
    """
    从 YAML frontmatter 中提取 name 字段。
    frontmatter 格式：文件以 '---' 开头，name: 值 在其中。
    若找不到则返回空字符串。
    """
    if not content.startswith("---"):
        return ""
    end = content.find("---", 3)
    if end == -1:
        return ""
    frontmatter = content[3:end]
    for line in frontmatter.splitlines():
        line = line.strip()
        if line.startswith("name:"):
            return line[len("name:"):].strip()
    return ""


def list_available_personas() -> list[str]:
    """返回所有可用人格的显示名列表（用于错误提示）。"""
    names = []
    for subdir in _SEARCH_DIRS:
        d = _PERSONAS_DIR / subdir
        if not d.exists():
            continue
        for md_file in sorted(d.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            name = _extract_name_from_frontmatter(content)
            if name:
                names.append(name)
            else:
                names.append(md_file.stem)
    return names


def load_persona(query: str) -> Persona:
    """
    按名字在 personas/ 下模糊匹配 .md 文件。
    搜索顺序：historical/ → fictional/ → modern/
    匹配规则：文件名 slug（不含扩展名）包含 query（大小写不敏感）。

    Args:
        query: 搜索词，如 "confucius"、"孔子"、"machiavelli"

    Returns:
        Persona dataclass，name 来自 frontmatter，content 为文件全文

    Raises:
        PersonaNotFoundError: 找不到匹配文件时，附带可用人格列表
    """
    query_lower = query.lower()

    for subdir in _SEARCH_DIRS:
        d = _PERSONAS_DIR / subdir
        if not d.exists():
            continue
        for md_file in d.glob("*.md"):
            if query_lower in md_file.stem.lower():
                content = md_file.read_text(encoding="utf-8")
                display_name = _extract_name_from_frontmatter(content) or md_file.stem
                return Persona(name=display_name, content=content)

    available = list_available_personas()
    raise PersonaNotFoundError(
        f"找不到人格 '{query}'。\n可用人格：{', '.join(available)}"
    )
