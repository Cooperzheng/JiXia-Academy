# 资料注入 + AI 联网搜索 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现用户资料注入（文本/文件）和 AI 联网搜索（Tavily + DuckDuckGo fallback），让争鸣基于真实信息展开。

**Spec:** `docs/superpowers/specs/2026-04-13-material-and-search-design.md`

**Tech Stack:** Python 3.13、tavily-python、duckduckgo-search、已有 openai SDK

---

## 文件变动

```
新增：
  src/engine/material.py
  src/engine/search.py

修改：
  src/engine/discussion.py
  src/engine/renderer.py
  src/engine/main.py
  src/engine/__init__.py
  requirements.txt
```

---

### Task 1：新建 material.py

**File:** `src/engine/material.py`

- [ ] 定义 `Material` dataclass：`content: str`、`source: str`、`round: int`
- [ ] 定义 `MaterialStore` dataclass
- [ ] 实现 `add(content, source, round=0)`：
  - 用 `len(content.split()) * 1.5` 粗估 token 数
  - 超出 2000 tokens 时截断并打印提示
- [ ] 实现 `get_prompt_block() -> str`：
  ```
  \n\n---\n## 背景资料（由主持人提供）\n{合并所有 material.content}\n---
  ```
- [ ] 实现 `is_empty() -> bool`

**验收：**
```python
store = MaterialStore()
store.add("测试内容", "paste")
assert not store.is_empty()
assert "背景资料" in store.get_prompt_block()
```

---

### Task 2：新建 search.py

**File:** `src/engine/search.py`

- [ ] 定义 `SearchResult` dataclass：`title: str`、`url: str`、`snippet: str`
- [ ] 定义 `SearchEngine` Protocol：`def search(self, query: str, max_results: int = 3) -> list[SearchResult]`
- [ ] 实现 `TavilySearch`：
  - `__init__` 接收 `api_key: str`
  - 调用 `tavily-python` SDK，`search_depth="basic"`，只取 `title + url + content[:300]`
  - 超时 5 秒，失败抛异常
- [ ] 实现 `DuckDuckGoSearch`：
  - 调用 `duckduckgo-search` SDK
  - 返回相同 `SearchResult` 格式
- [ ] 实现 `make_search_engine() -> SearchEngine | None`：
  - `SEARCH_DISABLED=1` → 返回 `None`
  - `TAVILY_API_KEY` 存在 → `TavilySearch`
  - 否则 → `DuckDuckGoSearch`
- [ ] 实现失败计数器：连续 3 次失败后设 `_disabled = True`，后续调用直接返回 `[]`

**验收：**
```python
from src.engine.search import DuckDuckGoSearch
engine = DuckDuckGoSearch()
results = engine.search("python programming", max_results=2)
assert len(results) <= 2
assert all(hasattr(r, 'snippet') for r in results)
```

---

### Task 3：修改 discussion.py

**File:** `src/engine/discussion.py`

- [ ] 顶部新增 import：`from .material import MaterialStore`、`from .search import SearchEngine, SearchResult, make_search_engine`
- [ ] 定义 `_SEARCH_TOOL_SCHEMA`（模块级常量）：
  ```python
  _SEARCH_TOOL_SCHEMA = {
      "type": "function",
      "function": {
          "name": "search_web",
          "description": "搜索互联网获取实时信息。仅在以下情况使用：议题涉及近期事件或最新数据；需要具体数字或事实支撑论点；对方引用了你不确定的信息。不要为了显得博学而搜索。",
          "parameters": {
              "type": "object",
              "properties": {
                  "query": {"type": "string", "description": "搜索关键词，简洁精准"}
              },
              "required": ["query"]
          }
      }
  }
  ```
- [ ] `_build_system_prompt` 新增参数 `material_store: MaterialStore | None = None`：
  - 在 prompt 末尾追加 `material_store.get_prompt_block()`（若非空）
- [ ] `Discussion` 新增字段：
  - `material_store: MaterialStore = field(default_factory=MaterialStore)`
  - `_search_engine: SearchEngine | None = field(init=False)`
- [ ] `__post_init__` 中初始化 `self._search_engine = make_search_engine()`
- [ ] 新增 `_format_search_results(results: list[SearchResult]) -> str`：格式化搜索结果注入 user message
- [ ] `_speak_stream` 重构为两阶段：
  - 阶段一：调用 API，传入 `tools=[_SEARCH_TOOL_SCHEMA]`（若 `_search_engine` 非 None）
  - 若 response 有 `tool_calls`：
    - 解析 `query`
    - yield `SearchEvent(name=persona.name, query=query, done=False)`
    - 执行搜索
    - yield `SearchEvent(name=persona.name, query=query, done=True, count=len(results))`
    - 将结果追加到 user message
    - 阶段二：再次调用 API（不带 tools）生成最终发言，流式 yield chunks
  - 若无 `tool_calls`：直接流式 yield chunks

- [ ] 新增 `SearchEvent` dataclass（在文件顶部）：
  ```python
  @dataclass
  class SearchEvent:
      name: str
      query: str
      done: bool = False
      count: int = 0
  ```
- [ ] `Discussion.run()` 中 `_build_system_prompt` 调用传入 `self.material_store`
- [ ] `respond_to_user` 中同样支持搜索（同 `_speak_stream` 逻辑）

**验收：**
```python
from src.engine.discussion import _build_system_prompt, _SEARCH_TOOL_SCHEMA
from src.engine.persona import load_persona
from src.engine.material import MaterialStore
p = load_persona("confucius")
store = MaterialStore()
store.add("测试背景资料", "paste")
prompt = _build_system_prompt(p, "测试", ["孔子"], material_store=store)
assert "背景资料" in prompt
assert _SEARCH_TOOL_SCHEMA["function"]["name"] == "search_web"
```

---

### Task 4：修改 renderer.py

**File:** `src/engine/renderer.py`

- [ ] import `SearchEvent` from `.discussion`
- [ ] 新增 `render_search_event(event: SearchEvent) -> None`：
  ```python
  # done=False: dim 样式，"  🔍 孔子 正在查证：xxx..."
  # done=True:  dim 样式，"  ✓  孔子 查证完毕（3篇来源）"
  ```
- [ ] `render()` 主循环新增对 `SearchEvent` 类型的处理分支

**验收：** import 不报错，`render_search_event` 可调用

---

### Task 5：修改 main.py

**File:** `src/engine/main.py`

- [ ] 新增 `_parse_opening_input(text: str) -> tuple[str | None, str | None]`：
  - 返回 `(opening_statement, file_path)`
  - 识别文件路径：以 `./`、`/`、盘符（如 `C:\`）开头，或以 `.txt .md .pdf .csv` 结尾
  - 否则 `file_path=None`，`opening_statement=text`
- [ ] 开场提问处理：
  - 提示文字改为"你有什么想法或背景资料带入今天的争鸣？（直接写观点，或输入文件路径如 ./article.txt）"
  - 调用 `_parse_opening_input()`
  - 若有 `file_path`：读取文件 → `discussion.material_store.add(content, f"file:{file_path}")`，打印"✓ 已注入 X tokens 的背景资料"
  - 若有 `opening_statement`：`discussion.opening_statement = opening_statement`
- [ ] Tab 插话回调 `on_interrupt()` 同样调用 `_parse_opening_input()`：
  - 识别到文件路径：`discussion.material_store.add()` → 打印提示 → 不走插话逻辑
  - 识别到文本：走现有插话逻辑
- [ ] `render()` 调用时 `lines` generator 需能处理 `SearchEvent`（已在 renderer.py 处理）

**验收：**
```python
from src.engine.main import _parse_opening_input
stmt, path = _parse_opening_input("./article.txt")
assert path == "./article.txt" and stmt is None

stmt, path = _parse_opening_input("我认为道德是长期实力")
assert stmt == "我认为道德是长期实力" and path is None
```

---

### Task 6：更新 requirements.txt 和 __init__.py

- [ ] `requirements.txt` 新增：`tavily-python` 和 `duckduckgo-search`
- [ ] `.venv` 安装：`.venv/Scripts/pip install tavily-python duckduckgo-search`
- [ ] `__init__.py` 导出 `MaterialStore`、`SearchEngine`、`SearchResult`、`SearchEvent`

---

### Task 7：端到端验收

- [ ] `python -c "from src.engine import MaterialStore, SearchEvent; print('imports OK')"`
- [ ] 跑所有单元测试：`pytest tests/ -q`（14个原有测试必须全过）
- [ ] 功能测试：
  - 输入 `./README.md` 作为开场资料 → 打印"已注入 X tokens"
  - 输入文字观点 → 正常开场
  - `SEARCH_DISABLED=1` 启动 → 无搜索行为
  - `TAVILY_API_KEY` 未设置 → 自动用 DuckDuckGo
