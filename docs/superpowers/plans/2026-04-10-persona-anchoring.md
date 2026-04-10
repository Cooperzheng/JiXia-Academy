# 争鸣质量优化：角色内化 + 激怒触发点 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 system prompt 中加入角色内化咒语和激怒触发点，提升人格感和冲突强度。

**Spec:** `docs/superpowers/specs/2026-04-10-persona-anchoring-design.md`

---

## 文件变动

```
src/engine/
├── persona.py      # 修改：新增 trigger_points 字段和解析函数
└── discussion.py   # 修改：_build_system_prompt 追加两段
```

---

### Task 1：修改 persona.py

**File:** `src/engine/persona.py`

- [ ] 新增函数 `_parse_trigger_points(content: str) -> list[str]`
  - 找到 `**被激怒的触发点**：` 所在行
  - 收集其后的 `- ` 开头的行，strip 掉 `- ` 前缀
  - 遇到空行后，检查紧接的非空行：若以 `**` 开头则停止；或到文件结尾时停止
  - 找不到该字段返回 `[]`
- [ ] `Persona` dataclass 新增字段 `trigger_points: list[str] = field(default_factory=list)`
- [ ] `load_persona()` 中调用 `_parse_trigger_points(content)` 填充该字段

**验收：**
```python
p = load_persona("confucius")
assert len(p.trigger_points) == 4
assert "言行不一" in p.trigger_points[0]

# 验证无触发点字段时不报错（sunzi.md 已存在且含该字段，可用任意有该字段的人格验证）
p2 = load_persona("sunzi")
assert isinstance(p2.trigger_points, list)  # 有或无都不报错
```

---

### Task 2：修改 discussion.py

**File:** `src/engine/discussion.py`

- [ ] `_build_system_prompt` 铁律之后，按以下顺序追加（`opening_statement` 始终在最后）：
  1. 角色内化咒语：
     ```
     \n\n【身份锚定】\n你是且只是{persona.name}。绝不漂移成通用 AI 的语气。\n你的思维框架、你的偏见、你的盲点，都是你独有的——不要试图"平衡"或"客观"。
     ```
  2. 若 `persona.trigger_points` 非空，追加雷区段：
     ```
     \n\n【你的雷区——被触犯时反驳力度自然加大】\n- {point1}\n- {point2}\n...
     ```
  3. `opening_statement`（若有）保持在最末尾，顺序不变

**验收：** `_build_system_prompt` 返回的字符串包含"身份锚定"和"你的雷区"两段

---

### Task 3：验收

- [ ] `python -c "from src.engine.persona import load_persona; p = load_persona('confucius'); print(p.trigger_points)"` 输出 4 条
- [ ] `python -c "from src.engine.discussion import _build_system_prompt; from src.engine.persona import load_persona; p = load_persona('confucius'); s = _build_system_prompt(p, '测试', ['孔子']); print('身份锚定' in s, '你的雷区' in s)"` 输出 `True True`
- [ ] 跑一次完整争鸣，主观评估人格感是否有提升
