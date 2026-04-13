# 资料注入 + AI 联网搜索 设计文档

**日期**：2026-04-13
**状态**：待审批

---

## 目标

让争鸣从"基于训练数据的推演"升级为"基于当下真实信息的判断"：
1. **资料注入**：用户带着文章/数据进入争鸣，人格们基于真实资料展开
2. **AI 联网搜索**：人格在争鸣过程中主动查证，搜索行为对用户透明可见

---

## 设计决策

| 决策 | 结论 |
|------|------|
| 搜索服务 | Tavily Basic（免费 1000次/月）+ DuckDuckGo 兜底（无需 Key）|
| 搜索权限 | 所有人格（含历史/虚构），历史人格通过 prompt 引导用自己语言消化结果 |
| 触发机制 | Function Calling，LLM 自决要不要搜、搜什么 |
| 注入内容 | Snippet only（title + description），≤300 tokens/条，≤3条，丢弃全文 |
| 搜索结果存储 | 即用即弃，**不写入 conversation history**，注入当轮 user message 末尾 |
| 默认状态 | 默认开启，`SEARCH_DISABLED=1` 环境变量可关闭 |
| 用户透明度 | 拦截 tool_calls，打印"[孔子 正在查证：xxx]"，搜索结束后继续发言 |
| 资料注入交互 | 融入开场提问输入框，自动识别文件路径 vs 文本；中途 Tab 插话同样支持 |
| 资料存储 | 注入所有人格 system prompt 末尾，不写入 history |
| 资料 token 上限 | 2000 tokens（约 1500 字），超出截断并提示 |

---

## 架构

### 新增文件

```
src/engine/
├── material.py     # MaterialStore：管理用户注入的背景资料
└── search.py       # SearchEngine：Tavily + DuckDuckGo 抽象层
```

### 修改文件

```
src/engine/
├── discussion.py   # _build_system_prompt 接受 material；_speak_stream 支持 Function Calling
├── persona.py      # Persona 新增 search_focus 可选字段（搜索意图提示）
├── renderer.py     # 新增 render_search_event()
└── main.py         # 开场提问识别文件路径；Tab 插话支持资料注入
```

---

## 模块设计

### material.py

```python
@dataclass
class MaterialStore:
    materials: list[Material] = field(default_factory=list)

    def add(self, content: str, source: str, round: int = 0) -> None:
        """添加资料，超出 token 上限时截断。"""

    def get_prompt_block(self) -> str:
        """返回注入 system prompt 的格式化文本块。"""
        # 格式：
        # ---
        # ## 背景资料（由主持人提供）
        # {content}
        # ---

    def is_empty(self) -> bool: ...
```

### search.py

```python
class SearchEngine(Protocol):
    def search(self, query: str, max_results: int = 3) -> list[SearchResult]: ...

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str   # description 字段，≤300 tokens

@dataclass
class TavilySearch:
    api_key: str
    def search(self, query, max_results=3) -> list[SearchResult]: ...

@dataclass
class DuckDuckGoSearch:
    """无需 Key，作为 fallback。"""
    def search(self, query, max_results=3) -> list[SearchResult]: ...

def make_search_engine() -> SearchEngine:
    """根据环境变量决定使用哪个引擎。"""
    # TAVILY_API_KEY 存在 → TavilySearch
    # 否则 → DuckDuckGoSearch
    # SEARCH_DISABLED=1 → 返回 None（关闭搜索）
```

### discussion.py 变更

**Function Calling schema**（注入每个人格的 system prompt）：

```python
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
```

**历史人格搜索结果消化 prompt**（追加在搜索结果注入后）：

```
请用你自己的思维框架和语言消化以上信息，
不要直接引用来源或 URL，将其转化为你的论据。
```

**_speak_stream 变更**：
1. 若 search_engine 可用，在 API 调用时传入 `tools=[_SEARCH_TOOL_SCHEMA]`
2. 解析 response：若有 `tool_calls` → yield `SearchEvent` → 执行搜索 → 将结果注入 user message → 再次调用 API 生成最终发言
3. 若无 `tool_calls` → 直接流式输出

**_build_system_prompt 变更**：
- 接受 `material_store: MaterialStore | None` 参数
- 若非空，在 prompt 末尾追加 `material_store.get_prompt_block()`

### renderer.py 新增

```python
def render_search_event(persona_name: str, query: str, done: bool = False) -> None:
    """
    done=False: "[孔子 正在查证：xxx...]"（dim 样式）
    done=True:  "[孔子 查证完毕，来源：3篇]"（dim 样式）
    """
```

### main.py 变更

**开场提问识别逻辑**：

```python
def _parse_opening_input(text: str) -> tuple[str | None, str | None]:
    """
    返回 (opening_statement, material_content)
    - 识别文件路径：以 ./ / C:\ 开头，或以 .txt .md .pdf 结尾
    - 否则全部视为开场观点
    """
```

**中途 Tab 插话扩展**：
- 插话输入框提示文字更新：
  `"你 │ （观点/问题，或粘贴文本，或文件路径如 ./doc.txt）"`
- 识别到文件路径时：读取内容 → `material_store.add()` → 打印"已追加资料，从下一位发言起生效"
- 识别到普通文本时：走现有插话逻辑

---

## 数据流

```
用户输入开场提问
    ↓
_parse_opening_input()
    ├── 文件路径 → 读取 → material_store.add()
    └── 文本 → discussion.opening_statement

争鸣每一轮：
_build_system_prompt(persona, ..., material_store)
    ↓
_speak_stream(persona, tools=[SEARCH_TOOL])
    ├── LLM 返回 tool_calls
    │     ↓
    │   render_search_event(persona, query, done=False)
    │     ↓
    │   search_engine.search(query)
    │     ↓
    │   render_search_event(persona, query, done=True)
    │     ↓
    │   注入搜索结果到 user message → 再次调用 API → 流式输出发言
    └── LLM 直接返回发言 → 流式输出
```

---

## 边界情况

| 情况 | 处理方式 |
|------|---------|
| TAVILY_API_KEY 未设置 | 自动 fallback 到 DuckDuckGo |
| SEARCH_DISABLED=1 | 不传 tools，人格照常发言 |
| 搜索超时（5秒）| 重试1次，仍失败则跳过搜索，静默继续 |
| 连续3次搜索失败 | 自动禁用联网，提示用户 |
| 文件不存在 | 提示"文件不存在"，回退到文本处理 |
| 资料超 2000 tokens | 截断并打印"资料已截断至 2000 tokens" |
| 用户粘贴超长文本 | 同上，按 token 数截断 |

---

## 不做的事

- 搜索结果写入 conversation history（会污染对话流）
- 跨轮次搜索缓存（旧结果复用风险大于收益）
- 资料按人格相关性选择性注入（引入相关性检测复杂度远超收益）
- 搜索结果全文注入（snippet 足够，全文会让人格迷失）
- 多搜索引擎并行（单引擎足够，并行带来协调问题）

---

## 验收标准

1. 用户输入 `./article.txt` → 文件内容被读取并注入所有人格 system prompt
2. 用户输入普通观点 → 走开场提问逻辑，不触发文件读取
3. 争鸣中孔子决定搜索时 → 打印"[孔子 正在查证：xxx]"，发言后消失
4. `SEARCH_DISABLED=1` 启动 → 无任何搜索行为，争鸣正常进行
5. TAVILY_API_KEY 未设置 → 自动用 DuckDuckGo，无报错
6. 搜索服务不可用 → 人格照常发言，不中断争鸣
7. 中途 Tab 输入文件路径 → 追加资料，下一位发言包含该资料
