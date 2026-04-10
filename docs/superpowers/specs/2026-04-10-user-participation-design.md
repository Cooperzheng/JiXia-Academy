# 用户入局设计文档

**日期**：2026-04-10
**状态**：待审批

---

## 目标

用户从旁观者变为主持人：
1. **开场提问**：带着自己的切入点和初步判断进入争鸣
2. **中途插话**：Tab 键随时打断，点名回应或 Moderator 决定

---

## 设计决策

| 问题 | 决策 |
|------|------|
| 插话触发方式 | Tab 键（Windows 终端兼容好，不会被 stdout 占用）|
| 点名回应 | 用户输入中含人名则定向回应，否则 Moderator 选 1-2 人 |
| 用户显示样式 | 独立样式 `你  │  [内容]`，白色加粗（视觉专项优化后置）|
| 上下文连续性 | 用户发言作为 SpeechEntry 追加进同一 history，不丢失任何上下文 |
| Moderator 实现 | 在本功能里一并实现，用户不点名时调用决定回应人数（1-2人）|

---

## 架构

### 文件变动

```
src/engine/
├── interruptor.py     # 新建：Tab 键监听线程（Windows msvcrt）
├── moderator.py       # 新建：决定用户插话后谁回应
├── discussion.py      # 修改：支持开场提问、用户发言注入、SpeechEntry 新增 role 字段
├── renderer.py        # 修改：新增用户发言渲染样式
└── main.py            # 修改：开场提问交互入口
```

### 数据结构变更

```python
# 新增 role 字段，区分人格发言和用户发言
class SpeechEntry(TypedDict):
    name: str
    text: str
    role: Literal["persona", "user"]  # 新增，默认 "persona"
```

---

## 模块设计

### 1. interruptor.py — Tab 键监听

```python
@dataclass
class Interruptor:
    """后台线程监听 Tab 键，设置 interrupt_flag。"""
    interrupt_flag: threading.Event = field(default_factory=threading.Event)
    _thread: threading.Thread = field(init=False)

    def start(self) -> None: ...   # 启动监听线程
    def stop(self) -> None: ...    # 停止监听线程
    def clear(self) -> None: ...   # 清除 flag（插话处理完后调用）
```

**Windows 实现**：用 `msvcrt.kbhit()` + `msvcrt.getwch()` 轮询，检测到 Tab（`\t`）时 set flag。
**Unix 备用**：用 `select.select([sys.stdin], ...)` 检测输入，检测到 Tab 时 set flag。

renderer 每输出一个 chunk 后检查 flag，发现被举起则暂停输出，进入插话流程。

---

### 2. moderator.py — 回应人选择

```python
@dataclass
class Moderator:
    personas: list[Persona]
    model: str
    _client: OpenAI

    def next_speakers_for_user(
        self,
        history: list[SpeechEntry],
        user_text: str,
        named: list[str],          # 用户点名的人（可能为空）
    ) -> list[Persona]:
        """
        返回应回应用户的人格列表（1-2人）。
        - 有点名：返回被点名人格
        - 无点名：调用 API，选出最该接话的 1-2 人
        """
```

**Moderator prompt（无点名时）**：
```
用户刚才说：「{user_text}」
圆桌成员：{names}
对话历史（最近3条）：{recent_history}

谁最应该回应这句话？选 1-2 人，只返回名字，用逗号分隔。
```

---

### 3. discussion.py — 核心变更

#### 3.1 开场提问

`Discussion` 新增 `opening_statement: str | None` 字段：

```python
@dataclass
class Discussion:
    ...
    opening_statement: str | None = None  # 用户开场提问
```

注入方式：在 `_build_system_prompt` 里追加一段：

```
【主持人开场】
{opening_statement}
请在整场争鸣中，始终围绕主持人提出的这个切入点展开。
```

#### 3.2 用户插话注入

新增方法：

```python
def inject_user_speech(self, text: str) -> None:
    """将用户发言追加进 history。"""
    self.history.append({"name": "你", "text": text, "role": "user"})
```

新增方法：

```python
def respond_to_user(
    self,
    user_text: str,
    moderator: Moderator,
) -> Generator[SpeechStream, None, None]:
    """
    决定回应人选，逐个 yield SpeechStream。
    被点名的人使用专属 prompt（强调"用户刚才直接问了你"）。
    """
```

#### 3.3 用户回应专属 prompt

用户点名时，user prompt 里额外注入：

```
【主持人直接向你提问】
「{user_text}」

你必须先直接回应主持人的问题，再继续你的论点。100字以内。
```

---

### 4. renderer.py — 用户发言样式

```python
def _render_user_speech(text: str) -> None:
    """渲染用户插话：白色加粗姓名，白色正文。"""
    t = Text()
    t.append("你", style="bold white")
    t.append("  │  ", style="white dim")
    t.append(text, style="white")
    _console.print(t)
```

renderer 的主循环新增对 `role == "user"` 的处理分支。

---

### 5. main.py — 开场提问交互

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  稷 下 学 宫 · 今 日 议 题
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

你有什么想法想带入今天的争鸣？（直接回车跳过）
你 │ _

```

用户输入后存入 `discussion.opening_statement`，跳过则为 `None`。

---

## 争鸣中的插话流程

```
主线程：流式输出中...
    ↓ 每个 chunk 输出后检查 interrupt_flag
用户按 Tab → interrupt_flag.set()
    ↓ 主线程发现 flag，当前 chunk 输出完后暂停
    ↓ 换行，显示提示：
      "\n你 │ "（等待输入）
用户输入内容 + 回车
    ↓ discussion.inject_user_speech(text)
    ↓ 解析是否有点名（在 text 中查找 personas 名字）
    ↓ moderator.next_speakers_for_user(history, text, named)
    ↓ 对每个回应人格：yield SpeechStream（renderer 流式渲染）
    ↓ interruptor.clear()
    ↓ 继续原来的争鸣轮次
```

---

## 边界情况

| 情况 | 处理方式 |
|------|---------|
| 用户跳过开场提问 | opening_statement = None，system prompt 不注入该段 |
| 用户输入空内容后回车 | 忽略，清除 flag，继续争鸣 |
| 用户点名多人 | 全部回应（上限 3 人）|
| Moderator API 失败 | fallback：选上一位发言者的"天然对手"（从争鸣坐标读取），找不到则选 personas[0] |
| 用户在散场后按 Tab | 忽略，争鸣已结束 |

---

## 验收标准

1. 开场输入"我认为道德是一种长期实力"→ 所有人格的发言都在回应这个切入点
2. 争鸣进行中按 Tab → 输出在当前 chunk 结束后暂停，出现 `你 │ ` 提示
3. 输入"孔子，你说的民心具体指什么" → 只有孔子回应，其他人不回应
4. 输入"这个逻辑站得住脚吗"（不点名）→ Moderator 选 1-2 人回应
5. 回应完毕后争鸣接续，history 完整包含用户发言和人格回应
6. 整场争鸣结束，打印完整 history，用户发言和人格发言交替出现，无断裂
