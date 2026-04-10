# 用户入局 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现用户开场提问 + Tab 中途插话，用户成为争鸣的主持人而非旁观者。

**Spec:** `docs/superpowers/specs/2026-04-10-user-participation-design.md`

**Tech Stack:** Python 3.13、msvcrt（Windows）/ select（Unix）、openai SDK（已有）

---

## 文件变动

```
src/engine/
├── interruptor.py     # 新建
├── moderator.py       # 新建
├── discussion.py      # 修改
├── renderer.py        # 修改
└── main.py            # 修改
```

---

### Task 1：新建 interruptor.py

**File:** `src/engine/interruptor.py`

- [ ] 定义 `Interruptor` dataclass，字段：`interrupt_flag: threading.Event`、`_thread: threading.Thread`
- [ ] 实现 `start()`：启动后台守护线程，循环检测键盘输入
  - Windows：`msvcrt.kbhit()` + `msvcrt.getwch()`，检测到 `\t` 则 `interrupt_flag.set()`
  - Unix：`select.select([sys.stdin], [], [], 0.05)`，读到 `\t` 则 set
- [ ] 实现 `stop()`：设置停止标志，join 线程
- [ ] 实现 `clear()`：`interrupt_flag.clear()`
- [ ] 轮询间隔 50ms，不占满 CPU

**验收：** 单独测试，终端跑起来后按 Tab，flag 被 set；按其他键无反应

---

### Task 2：新建 moderator.py

**File:** `src/engine/moderator.py`

- [ ] 定义 `Moderator` dataclass，字段：`personas`、`model`、`_client`
- [ ] 实现 `next_speakers_for_user(history, user_text, named) -> list[Persona]`
  - `named` 非空：直接返回对应人格（在 personas 里模糊匹配名字）
  - `named` 为空：构建 prompt，调用 API，返回 1-2 个人格
  - API 失败：fallback 返回 `[personas[0]]`
- [ ] Moderator prompt：
  ```
  用户刚才说：「{user_text}」
  圆桌成员：{names}
  最近对话（最多3条）：{recent_history}

  谁最应该回应这句话？选1-2人，只返回名字，逗号分隔，不含其他文字。
  ```
- [ ] 解析返回值：split(',') → strip → 模糊匹配 personas

**验收：** 传入"孔子，你怎么看" → 返回 `[孔子]`；传入"这站得住脚吗" → 返回 1-2 个人格

---

### Task 3：修改 discussion.py

**File:** `src/engine/discussion.py`

- [ ] `SpeechEntry` 新增 `role: Literal["persona", "user"]` 字段，默认 `"persona"`
- [ ] `Discussion` 新增字段 `opening_statement: str | None = None`
- [ ] `_build_system_prompt` 末尾追加开场提问段（仅当 `opening_statement` 非空）：
  ```
  【主持人开场】
  {opening_statement}
  请在整场争鸣中，始终围绕主持人提出的这个切入点展开。
  ```
- [ ] 新增 `inject_user_speech(text: str)`：追加 `role="user"` 的 SpeechEntry
- [ ] 新增 `_build_user_response_prompt(persona, user_text, history)`：在普通 user prompt 基础上，开头加：
  ```
  【主持人直接向你提问/发言】「{user_text}」
  必须先直接回应主持人，100字以内，再继续你的论点。
  ```
- [ ] 新增 `respond_to_user(user_text, moderator) -> Generator[SpeechStream]`：
  1. 解析 user_text 中的点名（遍历 personas 名字，检查是否出现在 text 中）
  2. 调用 `moderator.next_speakers_for_user()`
  3. 对每个回应人格调用 `_speak_stream()`（使用 user_response_prompt）
  4. yield SpeechStream

**验收：** `inject_user_speech` 后 history 最后一条 role == "user"；`respond_to_user` 能正确 yield SpeechStream

---

### Task 4：修改 renderer.py

**File:** `src/engine/renderer.py`

- [ ] 新增 `_render_user_speech(text: str)`：
  ```python
  t = Text()
  t.append("你", style="bold white")
  t.append("  │  ", style="white dim")
  t.append(text, style="white")
  _console.print(t)
  ```
- [ ] `_render_speech_stream` 新增 `interruptor: Interruptor | None = None` 参数
- [ ] chunk 输出循环内，每次 `out.flush()` 后检查 `interruptor.interrupt_flag.is_set()`，若 set 则 break（当前 chunk 输出完，停止继续读流）
- [ ] `render()` 函数签名新增 `interruptor` 和 `on_interrupt` 回调参数：
  ```python
  def render(
      lines: Generator,
      color_map: dict[str, str],
      interruptor: Interruptor | None = None,
      on_interrupt: Callable[[], None] | None = None,
  ) -> None
  ```
- [ ] 检测到 interrupt 后：换行，调用 `on_interrupt()`

**验收：** 流式输出中 set flag，输出在当前 chunk 后停止；调用 on_interrupt 回调

---

### Task 5：修改 main.py

**File:** `src/engine/main.py`

- [ ] 开场：打印议题和入席信息后，提示用户输入开场提问：
  ```
  你有什么想法想带入今天的争鸣？（直接回车跳过）
  你 │ _
  ```
- [ ] 用户输入存入 `discussion.opening_statement`（空字符串视为 None）
- [ ] 打印操作提示：`按 Tab 可随时插话`
- [ ] 初始化 `Interruptor` 和 `Moderator`
- [ ] 定义 `on_interrupt` 回调：
  1. `interruptor.clear()`
  2. `sys.stdout.write("\n你  │  ")` + `sys.stdout.flush()`
  3. `user_text = input()`
  4. 若空则直接返回
  5. `discussion.inject_user_speech(user_text)`
  6. `renderer` 渲染用户发言
  7. `for speech in discussion.respond_to_user(user_text, moderator): render_speech_stream(speech)`
- [ ] `render()` 调用时传入 `interruptor` 和 `on_interrupt`
- [ ] 争鸣结束后 `interruptor.stop()`

**验收：** 完整跑通：开场提问→争鸣→Tab 插话→回应→继续争鸣→散场

---

### Task 6：更新 __init__.py

- [ ] 导出 `Interruptor`、`Moderator`

---

### Task 7：端到端验收

- [ ] 开场输入"我认为道德是一种长期实力" → 人格发言围绕此切入点
- [ ] 争鸣中按 Tab → 输出暂停，出现 `你 │ ` 提示
- [ ] 输入"孔子，你说的民心具体指什么" → 只有孔子回应
- [ ] 输入"这逻辑站得住脚吗"（不点名）→ Moderator 选 1-2 人回应
- [ ] 回应后争鸣接续，history 完整无断裂
- [ ] Moderator API 故障时 fallback 正常，争鸣不中断
