# Python 引擎 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 `src/engine/` 三个模块（persona.py / discussion.py / main.py），让 `python src/engine/main.py` 能跑出 3 人、6 轮真实争鸣。

**Architecture:** `persona.py` 负责从 `personas/` 下按名字模糊匹配并加载 `.md` 文件；`discussion.py` 固定轮转调用 Claude API，每轮把完整对话历史注入 user prompt；`main.py` 作为示例入口串联两者并打印输出。

**Tech Stack:** Python 3.10+、anthropic SDK（`pip install anthropic`）、标准库（`pathlib`、`dataclasses`、`os`）

---

## 文件结构

```
JiXia-Academy/
├── requirements.txt              # 新建：anthropic
└── src/
    └── engine/
        ├── __init__.py           # 新建：空文件，让 engine 成为包
        ├── persona.py            # 新建：Persona dataclass + load_persona()
        ├── discussion.py         # 新建：Discussion class
        └── main.py               # 新建：示例入口
```

---

### Task 1：脚手架 + requirements.txt

**Files:**
- Create: `requirements.txt`
- Create: `src/engine/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```
anthropic
```

文件路径：`F:/Coding/JiXia-Academy/requirements.txt`

- [ ] **Step 2: 创建 src/engine/__init__.py**

内容为空文件即可（让 Python 识别 engine 为包）：

```python
```

文件路径：`F:/Coding/JiXia-Academy/src/engine/__init__.py`

- [ ] **Step 3: 安装依赖**

```bash
pip install anthropic
```

Expected：输出 `Successfully installed anthropic-...`（或 `already satisfied`）

- [ ] **Step 4: 验证可以 import**

```bash
python -c "import anthropic; print(anthropic.__version__)"
```

Expected：打印版本号，无报错。

- [ ] **Step 5: Commit**

```bash
git add requirements.txt src/engine/__init__.py
git commit -m "feat: scaffold engine package and add anthropic dependency"
```

---

### Task 2：persona.py

**Files:**
- Create: `src/engine/persona.py`

人格加载逻辑：从 `personas/historical/`、`personas/fictional/`、`personas/modern/` 三个目录中，按文件名模糊匹配（文件名 slug 包含查询词，大小写不敏感），读取 `.md` 全文，并从 frontmatter 的 `name:` 字段提取显示名。

- [ ] **Step 1: 写 persona.py**

```python
# src/engine/persona.py
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
```

- [ ] **Step 2: 手动验证 persona 加载**

```bash
cd F:/Coding/JiXia-Academy
python -c "
from src.engine.persona import load_persona
p = load_persona('confucius')
print('name:', p.name)
print('content[:80]:', p.content[:80])
"
```

Expected：
```
name: 孔子
content[:80]: ---
name: 孔子
era: 前551–前479，春秋末期，鲁国
...
```

- [ ] **Step 3: 验证错误处理**

```bash
python -c "
from src.engine.persona import load_persona
try:
    load_persona('nonexistent')
except Exception as e:
    print(str(e))
"
```

Expected：打印"找不到人格 'nonexistent'。\n可用人格：孔子, 孙子, ..."

- [ ] **Step 4: Commit**

```bash
git add src/engine/persona.py
git commit -m "feat: add persona loader with fuzzy file matching"
```

---

### Task 3：discussion.py

**Files:**
- Create: `src/engine/discussion.py`

核心争鸣循环。每轮固定轮转，构造 system prompt（人格全文 + 议题说明）和 user prompt（对话历史 + 发言指令），调用 Claude API，yield 输出行。

- [ ] **Step 1: 写 discussion.py**

```python
# src/engine/discussion.py
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Generator

import anthropic

from .persona import Persona


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


def _format_history(history: list[dict]) -> str:
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


def _build_user_prompt(current_persona: Persona, history: list[dict]) -> str:
    history_text = _format_history(history)
    return (
        f"{history_text}\n\n"
        f"现在轮到你（{current_persona.name}）发言。\n"
        f"100字以内，直接表达立场，不必自报家门，不必客套。\n"
        f"若前面有你认为错误的观点，直接指出并反驳。"
    )


@dataclass
class Discussion:
    personas: list[Persona]
    topic: str
    rounds: int = 5
    model: str = "claude-opus-4-5"
    history: list[dict] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "环境变量 ANTHROPIC_API_KEY 未设置。\n"
                "请执行：export ANTHROPIC_API_KEY=your_key_here"
            )
        self._client = anthropic.Anthropic(api_key=api_key)

    def _speak(self, persona: Persona) -> str:
        """调用 Claude API，返回该人格本轮发言文本。失败时重试一次。"""
        all_names = [p.name for p in self.personas]
        system = _build_system_prompt(persona, self.topic, all_names)
        user = _build_user_prompt(persona, self.history)

        for attempt in range(2):
            try:
                message = self._client.messages.create(
                    model=self.model,
                    max_tokens=300,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                return message.content[0].text.strip()
            except Exception as e:
                if attempt == 0:
                    continue  # 静默重试一次
                return f"（{persona.name} 此刻无言——{e}）"

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
```

- [ ] **Step 2: 验证 Discussion 在 API key 缺失时报错**

```bash
python -c "
import os
os.environ.pop('ANTHROPIC_API_KEY', None)
from src.engine.persona import load_persona
from src.engine.discussion import Discussion
p = load_persona('confucius')
try:
    d = Discussion([p], '测试')
except EnvironmentError as e:
    print('OK:', str(e)[:40])
"
```

Expected：`OK: 环境变量 ANTHROPIC_API_KEY 未设置。`

- [ ] **Step 3: Commit**

```bash
git add src/engine/discussion.py
git commit -m "feat: add Discussion class with fixed round-robin and Claude API calls"
```

---

### Task 4：main.py + 端到端验收

**Files:**
- Create: `src/engine/main.py`

- [ ] **Step 1: 写 main.py**

```python
# src/engine/main.py
"""
稷下学宫争鸣引擎 — 示例入口

使用方式：
    python src/engine/main.py

前置条件：
    export ANTHROPIC_API_KEY=your_key_here
"""
from .persona import load_persona
from .discussion import Discussion


def main() -> None:
    personas = [
        load_persona("confucius"),    # → 孔子
        load_persona("machiavelli"),  # → 马基雅维利
        load_persona("sunzi"),        # → 孙子
    ]

    discussion = Discussion(
        personas=personas,
        topic="乱世中，应该讲道德还是讲实力？",
        rounds=6,
    )

    for line in discussion.run():
        print(line)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 端到端运行（需要 ANTHROPIC_API_KEY）**

```bash
cd F:/Coding/JiXia-Academy
python -m src.engine.main
```

Expected 输出示例（内容会变，结构固定）：
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  稷 下 学 宫 · 今 日 议 题
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  「乱世中，应该讲道德还是讲实力？」
  入席：孔子 · 马基雅维利 · 孙子
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

孔子	│ 仁义非软弱，是最深的战略……
...
```

验收标准：
1. 开场框正确输出
2. 出现 6 行 `姓名\t│ 发言` 格式的内容
3. 散场框正确输出
4. 整体运行无报错，< 60s 完成

- [ ] **Step 3: Commit**

```bash
git add src/engine/main.py
git commit -m "feat: add main.py example entry point, engine MVP complete"
```

---

## 自检（plan 完成后核对）

- [x] spec 中所有需求均有对应 task：persona 加载 ✓、discussion 循环 ✓、错误处理 ✓、main 入口 ✓
- [x] 无 TBD / TODO / placeholder
- [x] 类型签名一致：`load_persona(str) -> Persona`，`Discussion.run() -> Generator[str]`，全文贯通
- [x] `_build_system_prompt` 和 `_build_user_prompt` 在 Task 3 中定义，Task 4 的 main.py 不直接调用它们
- [x] 每个 task 都有 commit 步骤
