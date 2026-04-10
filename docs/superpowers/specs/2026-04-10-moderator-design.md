# Moderator 设计文档

**日期**：2026-04-10
**状态**：已审批，待实现

---

## 问题

当前发言顺序固定轮转（孔子→马基雅维利→孙子→循环），导致：
- 被反驳的人要等 N-1 轮才能还嘴
- 对话感弱，像三个人各自演讲而非真正争鸣

## 目标

引入轻量 Moderator，每轮发言结束后决定"下一个谁说话"，优先让被怼的人接话。用户不可见，只感受到发言顺序自然流动。

## 方案决策

| 方案 | 描述 | 结论 |
|------|------|------|
| A | 纯 prompt 强化，保持固定轮转 | 放弃——对话感有限 |
| B | Moderator 决定顺序，纯调度不发言 | **采用** |
| C | Moderator + 情绪标注 | 后续迭代（方案 B 留钩子） |

---

## 架构

### 数据流

```
Discussion.run()
  → 每轮发言结束后
  → 调用 Moderator.next_speaker(history, personas)
  → 返回下一个 Persona
  → 继续发言循环
```

### Moderator 职责

- 输入：完整对话历史 + 人格列表
- 输出：下一个发言的人格名字（str）
- 不发言、不出现在输出里
- 调用一次轻量 API（prompt 极短，~100 tokens）

### Moderator 决策逻辑（prompt 设计）

```
对话历史：[history]
圆桌成员：[names]

规则：
1. 如果上一轮有人被点名反驳，优先让被反驳的人接话
2. 如果没有明显被怼的人，选择"沉默最久"的人
3. 同等条件下，选择与上一位发言者观点差异最大的人

只返回一个名字，不解释。
```

### 接口设计

```python
# src/engine/moderator.py

@dataclass
class Moderator:
    personas: list[Persona]
    model: str = "gemini-2.0-flash"
    _client: OpenAI  # 复用 Discussion 的 client

    def next_speaker(self, history: list[SpeechEntry]) -> Persona:
        """根据对话历史决定下一个发言者，返回 Persona 对象。"""
        ...
```

`Discussion` 改动：
- 构造时初始化 `Moderator`
- `run()` 的循环从固定轮转改为每轮调用 `moderator.next_speaker()`
- 第一轮仍随机/固定（历史为空，moderator 无依据）

---

## 约束

- Moderator 调用失败时 fallback 到固定轮转，不中断争鸣
- 不引入新依赖
- `Moderator` 复用 `Discussion` 的 OpenAI client，不重复初始化

---

## 未来扩展钩子（方案 C 预留）

`next_speaker()` 返回值可扩展为：

```python
@dataclass
class ModeratorDecision:
    persona: Persona
    emotion: str | None = None  # "激动" / "轻蔑" / "讽刺" / None
```

`Discussion` 把 `emotion` 注入下一条 user prompt，激活人格文件里的"被激怒触发点"字段。

---

## 验收标准

- 孔子被马基雅维利反驳后，孔子是下一个发言者（而非固定轮转的孙子）
- Moderator 调用失败时，争鸣继续（fallback 轮转）
- 用户输出中看不到任何 moderator 痕迹
