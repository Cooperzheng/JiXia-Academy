# 稷下学宫 · 开发规范

## 项目定位

召唤任意人物组成圆桌，抛出议题，看他们因你而争鸣。
**有趣 > 实用**，冲突是产品，过程是体验。

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

## Phase 1 · 争鸣内核

### 目标

用户在 Claude Code 里一句话触发，看到流式输出的多人格争鸣过程。

### 任务清单

#### 已完成
- [x] `SKILL.md` 核心逻辑（触发、开场、争鸣、散场）
- [x] 三套预设开局（战略局 / 创新局 / 哲思局）
- [x] 人格格式规范（nuwa-skill 兼容，待调研后可能更新）

#### 待完成 Step 0：蒸馏方法调研（先于人格库扩充）

调研以下仓库的蒸馏方法论，找出最适合稷下学宫多场景需求的方案：

| 仓库 | 关注点 |
|------|--------|
| [nuwa-skill](https://github.com/alchaincyf/nuwa-skill) | 6路并行采集、三重验证、心智模型提取 |
| [colleague-skill](https://github.com/titanwings/colleague-skill) | 职场数据源（飞书/Slack）、五层人格模型 |
| [anyone-to-skill](https://github.com/OpenDemon/anyone-to-skill) | 多媒体输入（视频/PDF）、历史人物支持 |

调研问题：
- 三种方案对**历史人物**（无社交媒体、依赖古籍）的处理方式有何不同？
- 三种方案对**虚构人物**（来源是小说/影视）的支持程度？
- 蒸馏出的人格文件，哪种格式更适合"争鸣"场景（需要观点冲突，而非风格模仿）？
- 是否有更好的格式标准可以整合采用？

调研结论写入本文件「人格格式规范」章节，再统一开始扩充人格库。

#### 待完成 Step 1：人格库扩充

调研完成后，目标 **12 个人格**，覆盖三类：

| 类别 | 目标数量 | 待建 |
|------|---------|------|
| 历史人物 | 6 | 孔子、孙子、诸葛亮、庄子、马基雅维利、克劳塞维茨 |
| 虚构人物 | 3 | 福尔摩斯、赫敏·格兰杰、甘道夫 |
| 现代人物 | 3 | 直接引用 nuwa-skill（Munger、Feynman、Naval）|

#### 待完成：Python 引擎（`src/engine/`）
比纯 SKILL.md 多了颜色、停顿、舞台提示的精确控制。

| 文件 | 职责 |
|------|------|
| `persona.py` | 加载 `personas/` 下的 `.md` 文件，解析人物信息 |
| `discussion.py` | 维护对话历史，决定发言顺序，调用 Claude API 生成回应 |
| `renderer.py` | `rich` 库流式输出，每人物一色，停顿，舞台提示 |
| `main.py` | CLI 入口，接收人物 + 议题参数 |

**讨论引擎核心逻辑：**
```
1. 加载选定人格（读取 .md 文件）
2. 输出开场框
3. 循环（4-6轮）：
   a. 决定下一个发言者（首轮按戏剧张力，后续按被点名/被反驳）
   b. 构造 prompt：系统 prompt（人格描述）+ 对话历史 + "现在轮到你回应"
   c. 流式调用 Claude API，实时输出
   d. 追加到对话历史
4. 输出散场框
```

#### 待完成：安装与测试
- [ ] 验证 `SKILL.md` 手动复制安装流程
- [ ] 补充 `requirements.txt`（`anthropic`、`rich`）
- [ ] 录制 demo GIF（跑一次真实争鸣，截图/录屏）
- [ ] 更新 README 中的 demo 为真实输出

---

## Phase 2 · 视觉学宫（计划中）

### 目标

本地启动一个像素风学宫界面，人物在场景中实时发言动画。

### 技术栈

| 组件 | 技术 | 参考 |
|------|------|------|
| 场景渲染 | Phaser.js | Star Office UI |
| 后端服务 | Flask + flask-socketio | Star Office UI |
| 实时推送 | WebSocket | Star Office UI |
| 桌面打包 | Electron（可选）| — |

### 数据流

```
src/engine/（Python）
    ↓ 每生成一句发言，推送结构化事件
Flask 服务器
    ↓ WebSocket
Phaser 前端
    ↓ 触发对应角色动画 + 对话气泡
```

### WebSocket 事件格式

```json
{ "type": "persona_speaking", "name": "孔子", "text": "名不正则言不顺..." }
{ "type": "persona_done",     "name": "孔子" }
{ "type": "stage_direction",  "text": "*孔子沉默片刻*" }
{ "type": "session_end" }
```

---

## Phase 3 · 人格生态（计划中）

- nuwa-skill 人格库直接导入
- 支持用户带入自定义 SKILL.md 人格
- Hermes Agent skill 生态兼容
- 炼丹炉：人格融合（独立项目，互相引用）

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
| 人格格式 | 兼容 nuwa-skill | 直接复用其高质量现代人物人格 |
| 开发框架 | superpowers（本地）| 规划优先，代码审查，仅对本项目生效 |

---

## 参考项目

| 项目 | 学什么 |
|------|--------|
| [nuwa-skill](https://github.com/alchaincyf/nuwa-skill) | 人格格式、蒸馏方法论 |
| [Star Office UI](https://github.com/ringhyacinth/Star-Office-UI) | Phaser + WebSocket 架构 |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | 流式 UI、skill 生态 |
| [edict](https://github.com/cft0808/edict) | Agent 隔离思路 |
| [superpowers](https://github.com/obra/superpowers) | 开发规范（规划→实现→审查）|

---

## 每次开发前检查

- [ ] 改动是否影响 SKILL.md 的核心争鸣逻辑？
- [ ] 新人格是否有真实资料支撑，而非印象拼凑？
- [ ] Phase 2 事件格式是否和 WebSocket 定义一致？
