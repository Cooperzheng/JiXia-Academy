# 稷下学宫 Python 引擎 · 设计文档

**日期**：2026-04-09  
**阶段**：Phase 1 — 争鸣内核

---

## 目标

用 Python 实现稷下学宫的核心争鸣循环，作为 `src/engine/` 模块。
SKILL.md 已经可以在 Claude Code 内手动跑通争鸣；Python 引擎的目标是让这个过程可编程、可自动化、后续可接 Phase 2 视觉学宫的 WebSocket 事件流。

---

## 范围（MVP）

**包含：**
- `persona.py`：加载 `personas/` 下的 `.md` 人格文件
- `discussion.py`：维护对话历史，驱动争鸣循环，调用 Claude API
- `main.py`：示例/测试入口（非 CLI）

**不包含（后续迭代）：**
- `renderer.py`（rich 彩色流式输出）
- CLI 命令行接口
- WebSocket 事件推送

---

## 模块设计

### `persona.py`

```python
@dataclass
class Persona:
    name: str           # 显示名，如"孔子"
    content: str        # .md 文件全文，直接作为 system prompt 的一部分

def load_persona(name: str) -> Persona:
    """
    按名字在 personas/ 下模糊匹配 .md 文件。
    搜索顺序：historical/ → fictional/ → modern/
    匹配规则：文件名 slug 包含 name 的拼音/中文/英文
    """
```

**人格注入策略（当前方案）：全文塑入**

将完整 `.md` 文件内容作为每次 API 调用的 system prompt 前缀。优点是实现简单、最大化保留人格细节。缺点是 token 消耗较高（每轮约 400-800 token/人格）。

> **技术决策记录**：选择"全文塑入"而非"结构化解析"，原因是 MVP 阶段优先跑通逻辑。后续可能的优化方向：
> 1. 只提取"心智模型"+"表达DNA"节（节省 ~50% token）
> 2. 首轮提取完整人格，后续轮次只用简短摘要
> 3. 研究向量化缓存方案（若轮次增多后 context 成本显著）
> 
> 何时迭代：当单次争鸣成本 > $0.05 或延迟 > 30s 时评估。

---

### `discussion.py`

```python
class Discussion:
    def __init__(
        self,
        personas: List[Persona],
        topic: str,
        rounds: int = 5,      # 总发言轮次
        model: str = "claude-opus-4-5"
    ):
        self.personas = personas
        self.topic = topic
        self.rounds = rounds
        self.history: List[dict] = []  # {"name": str, "text": str}

    def run(self) -> Generator[str, None, None]:
        """
        主争鸣循环。固定轮转（A→B→C→A→...）。
        yield 每行输出，供调用方打印或推送事件。
        """
```

**Prompt 结构（每轮）：**

```
system:
  {人物.md 全文}

  你是稷下学宫的参与者。今日议题：「{topic}」
  圆桌成员：{人物1} · {人物2} · ...
  规则：你必须直接回应前面的发言，不能各说各话。

user:
  {格式化的对话历史}

  现在轮到你（{当前人物}）发言。
  100字以内，直接表达立场，不必自报家门，不必客套。
  若前面有你认为错误的观点，直接指出并反驳。
```

**对话历史格式：**
```
孔子    │ 学而不思则罔……
马基雅维利│ 恕我直言，仁义在权力面前……
孙子    │ 兵无常势，此论过于绝对……
```

**发言顺序：固定轮转**

按 `personas` 列表顺序循环，总共跑 `rounds` 轮。
简单可预测，便于调试。后续若需要"被反驳者优先"逻辑，可在此基础上扩展。

---

### `main.py`

示例入口，验证整个链路：

```python
from engine.persona import load_persona
from engine.discussion import Discussion

def main():
    personas = [
        load_persona("confucius"),
        load_persona("machiavelli"),
        load_persona("sunzi"),
    ]
    discussion = Discussion(
        personas=personas,
        topic="乱世中，应该讲道德还是讲实力？",
        rounds=6
    )
    for line in discussion.run():
        print(line)

if __name__ == "__main__":
    main()
```

---

## 文件结构

```
JiXia-Academy/
├── src/
│   └── engine/
│       ├── __init__.py
│       ├── persona.py
│       ├── discussion.py
│       └── main.py
└── requirements.txt       # anthropic
```

---

## 错误处理

- 找不到人格文件：抛出 `PersonaNotFoundError`，列出可用人格
- API 调用失败：重试一次，再失败则跳过该轮次并 yield 提示
- 环境变量 `ANTHROPIC_API_KEY` 未设置：启动时检查，立即报错

---

## 验收标准

1. `python src/engine/main.py` 能跑出 3 人、6 轮争鸣
2. 每轮发言明显回应了上一轮内容（非各说各话）
3. 总运行时间 < 60s（正常网络）
4. 无硬编码 API key

---

## 后续迭代

| 迭代 | 内容 | 触发条件 |
|------|------|---------|
| v1.1 | renderer.py（rich 彩色流式输出） | MVP 验收通过后 |
| v1.2 | token 优化（选择性注入） | 成本 > $0.05/次 |
| v2.0 | WebSocket 事件推送接 Phase 2 | Phase 2 启动时 |
