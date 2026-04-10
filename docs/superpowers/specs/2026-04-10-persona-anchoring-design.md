# 争鸣质量优化：角色内化 + 激怒触发点设计文档

**日期**：2026-04-10
**状态**：待审核

---

## 问题

当前争鸣两个症状：
1. **人格漂移**：多轮后人格语气趋同，孔子和马基雅维利开始说相似的话
2. **冲突表面化**：人格知道自己该反驳，但力度不够，缺少真实的情绪张力

---

## 参考

- CAMEL：role inception prompt，"Never forget you are X"，防止人格漂移
- generative_agents：议题关联记忆，发言前注入"我对此议题的具体立场"
- 稷下人格文件：`争鸣坐标.被激怒触发点` 字段已有，但目前未被引擎读取

---

## 方案

### 改动 1：角色内化咒语（`discussion.py`）

在 `_build_system_prompt` 的铁律之后追加：

```
【身份锚定】
你是且只是{name}。绝不漂移成通用 AI 的语气。
你的思维框架、你的偏见、你的盲点，都是你独有的——不要试图"平衡"或"客观"。
```

### 改动 2：激怒触发点激活（`persona.py` + `discussion.py`）

**步骤一**：`persona.py` 新增 `_parse_trigger_points(content: str) -> list[str]` 函数，从人格文件 markdown 中解析「被激怒的触发点」列表。

解析规则：找到 `**被激怒的触发点**：` 之后的 `-` 列表项；遇到空行后若紧接的非空行以 `**` 开头则停止，或到文件结尾停止。

**步骤二**：`Persona` dataclass 新增 `trigger_points: list[str]` 字段，加载时自动解析。

**步骤三**：`_build_system_prompt` 末尾追加：

```
【你的雷区——被触犯时反驳力度加大】
{trigger_points 列表，每条一行，- 开头}
```

无需检测历史是否已触发——直接告知模型这些是你的雷区，让它在感知到相关观点时自然加大力度。简单、稳定、可预测。

---

## 文件变动

```
src/engine/
├── persona.py      # 修改：新增 trigger_points 字段和解析函数
└── discussion.py   # 修改：_build_system_prompt 追加两段
```

---

## 不做的事

- 不动态检测"当前对话是否触发了雷区"——增加复杂度，模型自己能感知
- 不改 history 格式、不改 SpeechEntry——此次只动 prompt

---

## 验收标准

1. `load_persona("confucius").trigger_points` 返回 4 条非空字符串
2. 人格文件无「被激怒的触发点」字段时，`trigger_points` 为空列表，不报错
3. system prompt 包含「身份锚定」和「你的雷区」两段
4. 主观评估：运行一次争鸣，孔子被马基雅维利触犯"以利代义"时，反驳力度明显强于之前
