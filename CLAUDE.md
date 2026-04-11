# 稷下学宫 · 开发规范

## 强制工作流（写任何代码前必须执行）

> 本项目使用 superpowers 开发框架（`.claude/skills/superpowers/`）。
> 以下检查点是硬性要求，不是建议。

**写代码前（每次）：**
1. 查「参考项目库」——有没有现成实现可以借鉴，有则先读代码再动手
2. 调用 `superpowers:brainstorming` — 先头脑风暴设计方案
3. 调用 `superpowers:writing-plans` — 写完整 Plan 文档到 `docs/superpowers/plans/YYYY-MM-DD-<name>.md`
4. 执行方式二选一：`superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`

**写代码后（每次）：**
4. **自测先行**：每个 Task 完成后必须自己跑验证，不能等用户来发现
   - 有输出的功能：本地端到端跑一次，肉眼确认输出正确
   - 有解析/计算逻辑：用 `python -c "assert ..."` 快速验边界
   - 新文件：至少确认能正常 import
   - **严禁只做 import 检查就算验收**
5. 调用 `superpowers:requesting-code-review` — 请求 code review
6. 调用 `superpowers:verification-before-completion` — 验收后再 push

**文档/人格文件（非代码）：** 上述流程可跳过，但重大格式变更前仍需 brainstorm。

**Auto mode 下的优先级：** Auto mode 的"减少打扰"不覆盖本工作流。brainstorm 和 plan 仍须执行，设计确认节点不跳过——可以把确认合并成一条消息，但必须等用户点头再动手。

---

## 项目定位

**召集任意时代的思想者，由你主持一场思想实验。**

用户是主持人，不是旁观者。人格们不给你答案——他们给你没想过的角度、权衡方式和思维碰撞。过程比结论更值钱。

### 核心价值
- **思维陪练，不是答案机器**：目的是让用户自己想得更深，而不是替用户思考
- **过程即价值**：精英如何权衡、如何被对方观点触动、如何坚守或修正立场——这些比最终结论更值得观察
- **用户引导争鸣**：开场提问锚定角度，中途插话深挖关键点，用户是苏格拉底式的引导者

### 应用场景
- **决策压力测试**：把你的判断扔给顶级思维框架，看它从哪里被拆穿
- **精英思维观察**：特朗普+卢比奥怎么规划对伊政策？邱吉尔+罗斯福在某个节点会怎么选？
- **复杂议题切面**：同一问题经过五种世界观过滤，你会看到自己从未想到的维度

### 设计原则
- **有趣 > 实用**：冲突是产品，过程是体验
- **真实 > 刻板**：孔子不只会说"子曰"，用思维框架，不用标签
- **引导 > 说教**：人格们不布道，用户的问题才是发动机

---

## 目录结构

```
JiXia-Academy/
├── SKILL.md              # Claude Code skill 入口（核心）
├── CLAUDE.md             # 本文件
├── personas/
│   ├── historical/       # 历史人物（自建，nuwa-skill 格式）
│   ├── fictional/        # 虚构人物（自建，nuwa-skill 格式）
│   └── modern/           # 现代人物（直接引用 nuwa-skill，不重复建）
├── src/
│   ├── engine/           # Phase 1：Python 讨论引擎
│   └── ui/               # Phase 2：Phaser 视觉学宫
└── .claude/
    └── skills/superpowers/  # 本地开发工具（不入 git）
```

---

## 进度与规划

**→ 见 [`ROADMAP.md`](./ROADMAP.md)**

---

## 核心设计原则

**争鸣优先**：每个人物必须看到并回应前面的发言，禁止各说各话。

**错位产生戏剧**：议题选择、人物组合都要最大化观点冲突，一致的圆桌是失败的圆桌。

**人格要真实，不要刻板**：孔子不只会说"子曰"，马斯克不只会说"go to Mars"。用思维框架，不用标签。

---

## 技术决策记录

| 决策 | 结论 | 原因 |
|------|------|------|
| 讨论引擎 | 自建轻量版，不用 AutoGen | 减少依赖，完全掌控对话历史和顺序逻辑 |
| Phase 2 桥接 | WebSocket | 复用 Star Office UI 的 Phaser 集成代码 |
| 人格格式 | nuwa-skill 格式 + 稷下专属「争鸣坐标」| nuwa-skill 格式争鸣适配性最高；争鸣坐标解决多人格冲突设计问题 |
| 现代人格来源 | 基于 nuwa-skill 素材提炼轻量版 | 原版 400+ 行专为单人格聊天设计，多人格圆桌需要 50-80 行轻量版 |
| 历史/虚构人格来源 | 从一手资料直接蒸馏 | nuwa-skill 不支持，anyone-to-skill 提供方法论参考 |
| 开发框架 | superpowers（本地，不入 git）| 规划优先，代码审查，仅对本项目生效 |
| Python 引擎 API | Gemini（OpenAI 兼容接口） | 用户无 Anthropic API key，Gemini 免费额度可用 |
| 人格注入策略 | 全文塑入（MVP） | 实现简单；后续成本超阈值时升级为选择性注入 |
| 发言顺序 | Moderator 动态决定（被反驳者优先） | 固定轮转对话感弱，Moderator 架构扩展性好 |

---

## 参考项目库

> **开发原则：写代码前先查这里，看有没有现成的实现可以借鉴。**
> 遇到新问题时，先搜 GitHub，找到有价值的项目就补充进来。

### 争鸣引擎 & 多 Agent 对话

| 项目 | 链接 | 借鉴什么 |
|------|------|---------|
| MiroFish | [666ghj/MiroFish](https://github.com/666ghj/MiroFish) | Interview IPC 机制（用户插话原型）、上帝视角报告 prompt、persona 记忆字段设计 |
| llm_multiagent_debate | [composable-models/llm_multiagent_debate](https://github.com/composable-models/llm_multiagent_debate) | 强制回应注入 prompt pattern："Using their reasoning as advice, give your updated answer" |
| CAMEL | [camel-ai/camel](https://github.com/camel-ai/camel) | Role inception prompt：防止人格漂移的"Never forget you are X"咒语 |
| generative_agents | [joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents) | 记忆-议题对齐：发言前检索"我对此议题的核心观点"，议题关联记忆注入 |
| ChatEval | [chanchimin/ChatEval](https://github.com/chanchimin/ChatEval) | 发言顺序研究：异步轮流+全历史注入质量最高；角色分工提升讨论深度 |

### 人格蒸馏

| 项目 | 链接 | 借鉴什么 |
|------|------|---------|
| nuwa-skill | [alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill) | 人格格式（心智模型+决策启发式+表达DNA+诚实边界）、现代人物蒸馏方法论 |
| anyone-to-skill | [OpenDemon/anyone-to-skill](https://github.com/OpenDemon/anyone-to-skill) | 历史/虚构人物多媒体输入蒸馏方法 |

### 视觉界面（Phase 3 参考）

| 项目 | 链接 | 借鉴什么 |
|------|------|---------|
| Star Office UI | [ringhyacinth/Star-Office-UI](https://github.com/ringhyacinth/Star-Office-UI) | Phaser + Flask + WebSocket 完整架构，像素风 Agent 可视化 |
| Hermes Agent | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | 流式 UI、skill 生态设计 |

### 开发工具

| 项目 | 链接 | 借鉴什么 |
|------|------|---------|
| superpowers | [obra/superpowers](https://github.com/obra/superpowers) | 开发规范（brainstorm→plan→实现→review） |
| edict | [cft0808/edict](https://github.com/cft0808/edict) | Agent 隔离思路 |

---

## 人格格式规范

> **调研时间**：2026-04
> **对比仓库**：nuwa-skill / colleague-skill / anyone-to-skill

### 三种方案横向对比

| 维度 | nuwa-skill（女娲） | colleague-skill（同事） | anyone-to-skill（万魂幡） |
|------|------------------|----------------------|------------------------|
| 历史人物 | **不支持**（明确排除无一手资料的人物） | **不支持**（必须有飞书/Slack等职场数据） | **支持**（孔子、庄子已入库，古籍/PDF可作输入） |
| 虚构人物 | **不支持**（小说/影视非"公开资料"） | **不支持** | **支持**（视频/PDF/文本均可输入） |
| 现代人物 | **最强**（6路并行+三重验证，有13位高质量人格） | **最强**（职场行为+沟通风格双维度） | **支持**（Musk、Jobs、Naval等已入库） |
| 输出格式 | 心智模型+决策启发式+表达DNA+诚实边界 | work.md+persona.md+SKILL.md（五层模型） | SKILL.md（思维框架+决策逻辑+沟通风格） |
| 争鸣适配性 | **最高**（心智模型具备预测力，能推断未知立场） | 低（侧重职场协作，非观点冲突） | 中（风格模仿为主，观点预测为辅） |
| 质量标准 | 三重验证（跨域复现/生成力/排他性） | 素材量驱动 | 多源交叉验证 |

### 调研结论

**稷下学宫的核心需求**是"争鸣"——人格必须能在新议题上产生可预测的、与其他人格形成冲突的独立立场。这不是风格模仿，而是思维框架的运作。

基于此，**采用 nuwa-skill 的输出格式 + anyone-to-skill 的输入方法论**：

- **格式选 nuwa-skill**：心智模型（3-7个）+ 决策启发式（5-10条）+ 表达DNA + 诚实边界，这套格式能让人格对陌生议题"做推断"而非"背台词"
- **现代人物**：直接复用 nuwa-skill 仓库已有人格（Munger/Feynman/Naval 等质量最高）
- **历史人物**：用 anyone-to-skill 的思路（古籍/译著/PDF 作为输入源），输出到 nuwa-skill 格式
- **虚构人物**：用 anyone-to-skill 的思路（原著/剧本/访谈 作为输入源），输出到 nuwa-skill 格式

**colleague-skill 不适用**：它解决的是"把同事克隆成 AI"的职场问题，数据源（飞书/Slack）和目标（工作协作）与稷下学宫完全不同，放弃参考。

### 争鸣坐标：稷下学宫专属第五节

普通人格蒸馏只解决一个问题：**"这个人怎么思考？"**

圆桌争鸣额外需要知道：**"这个人会跟谁吵、为什么吵、怎么被激怒？"**

争鸣坐标回答这三个问题，让引擎在排座次、决定发言顺序时有依据——"孔子和庄子必须对着坐"、"马基雅维利说完赫敏最容易接话反驳"。没有它，人格再准也可能变成各说各话。

### 稷下学宫人格模板（最终版）

在 nuwa-skill 标准格式基础上，增加第五节「争鸣坐标」，专门为多人格圆桌设计：

```markdown
---
name: 人物姓名
era: 时代（如：春秋时期 / 19世纪 / 虚构·中土世界）
type: historical / modern / fictional
source: 数据来源（著作名、影视作品、原始访谈等）
---

## 心智模型
（3-7个该人物观察世界的核心框架。每条必须能在两个以上不同领域中复现，
能预测其对未知问题的立场，且与其他常见框架有明显差异。）

## 决策启发式
（5-10条该人物做决定时的思维定势。格式：【场景】→【倾向】→【真实案例】）

## 表达 DNA
（语言节奏、标志性句式、惯用意象、回避的表达方式。）

## 诚实边界
（该人格无法准确模拟的部分。对历史人物标注"古籍空白区"，
对虚构人物标注"原著未涉及区"。）

## 争鸣坐标
（稷下学宫专属节。描述：）
- **天然盟友**：与哪类思维框架容易共鸣？
- **天然对手**：与哪类思维框架必然冲突？
- **核心议题立场**：在战略/创新/秩序/人性等议题上的预设倾向
- **被激怒的触发点**：什么观点会让这个人格情绪化或反驳力度加大？
```

### 三类人物的蒸馏流程

**现代人物**（Munger/Feynman/Naval 等）
1. 优先检查 nuwa-skill 仓库是否已有 → 直接引用
2. 没有则按 nuwa-skill 的6路并行调研自建

**历史人物**（孔子/孙子/马基雅维利 等）
1. 收集一手资料：原著/可信译著（PDF格式）+ 学术传记
2. 按 nuwa-skill 的三重验证标准提炼心智模型
3. 无社交媒体数据，表达DNA依赖原著文本风格
4. 诚实边界标注"史料空白区"

**虚构人物**（福尔摩斯/赫敏/甘道夫 等）
1. 收集一手资料：原著全文 + 作者访谈 + 官方设定集
2. 心智模型从具体情节中归纳（需要2个以上独立情节印证）
3. 诚实边界标注"原著未涉及的现实议题"

---

## 每次开发前检查

- [ ] 改动是否影响 SKILL.md 的核心争鸣逻辑？
- [ ] 新人格是否有真实资料支撑，而非印象拼凑？
- [ ] Phase 2 事件格式是否和 WebSocket 定义一致？
