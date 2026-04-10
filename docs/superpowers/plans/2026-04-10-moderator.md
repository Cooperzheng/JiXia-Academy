# Moderator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `src/engine/moderator.py`，让 Discussion 的发言顺序从固定轮转改为由 Moderator 动态决定，优先让被反驳的人接话。

**Spec:** `docs/superpowers/specs/2026-04-10-moderator-design.md`

**Tech Stack:** Python 3.10+、openai SDK（已有）、gemini-2.0-flash

---

## 文件变动

```
src/engine/
├── moderator.py     # 新建
├── discussion.py    # 修改：集成 Moderator，去掉固定轮转
└── __init__.py      # 修改：导出 Moderator
```

---

### Task 1：新建 moderator.py

**File:** `src/engine/moderator.py`

- [ ] 定义 `Moderator` dataclass，字段：`personas: list[Persona]`、`model: str`、`_client: OpenAI`
- [ ] 实现 `next_speaker(history: list[SpeechEntry]) -> Persona`
  - 历史为空时：返回 `personas[0]`
  - 历史非空时：构建 moderator prompt，调用 API，返回名字对应的 Persona
  - API 失败时：fallback 到 `personas[(last_index + 1) % len(personas)]`
- [ ] Moderator prompt 内容：
  ```
  以下是圆桌争鸣的对话记录：
  [history 最后 3 条]

  圆桌成员：[names]

  决定下一个发言者，规则：
  1. 若上一轮有人被点名反驳，优先让被反驳者接话
  2. 若无明显被怼者，选沉默最久的人
  3. 同等条件下，选与上一位发言者观点差异最大的人

  只返回一个名字，不含任何其他文字。
  ```
- [ ] 解析返回值：strip 后做模糊匹配（复用 `persona.py` 的匹配逻辑），找不到则 fallback

**验收：** `Moderator.next_speaker()` 单独调用能返回合法 Persona

---

### Task 2：修改 discussion.py

**File:** `src/engine/discussion.py`

- [ ] `Discussion.__post_init__` 中初始化 `self._moderator = Moderator(personas=self.personas, model=self.model, _client=self._client)`
- [ ] `run()` 循环改为：
  ```python
  next_persona = self.personas[0]  # 第一轮固定
  for i in range(self.rounds):
      persona = next_persona
      speech = self._speak_stream(persona)
      yield speech
      self.history.append(...)
      yield ""
      # 决定下一轮发言者
      next_persona = self._moderator.next_speaker(self.history)
  ```
- [ ] 去掉旧的 `i % len(self.personas)` 固定轮转逻辑

**验收：** 运行 `python -m src.engine.main`，观察孔子被反驳后是否优先接话

---

### Task 3：更新 __init__.py

**File:** `src/engine/__init__.py`

- [ ] 导出 `Moderator`

---

### Task 4：验收测试

- [ ] 跑一次完整争鸣，确认发言顺序不再是严格 A→B→C→A→B→C
- [ ] 手动让 Moderator client 抛异常，确认 fallback 轮转正常工作，争鸣不中断
- [ ] 用户输出中无任何 moderator 痕迹
