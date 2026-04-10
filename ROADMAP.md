# 稷下学宫 · 路线图

> 进度地图。开发规范见 `CLAUDE.md`，设计文档见 `docs/superpowers/`。
>
> 状态：✅ 完成 · 🚧 进行中 · ⬜ 待做 · 💡 想法

---

## Phase 1 · 争鸣内核

**目标**：用户一句话触发，看到流式输出的多人格争鸣过程。

### 基础建设
- ✅ `SKILL.md` 核心逻辑（触发、开场、争鸣、散场）
- ✅ 三套预设开局（战略局 / 创新局 / 哲思局）
- ✅ 人格格式规范（nuwa-skill 格式 + 争鸣坐标）
- ✅ 蒸馏方法调研（nuwa-skill / colleague-skill / anyone-to-skill 横向对比）

### 人格库（12 个）
- ✅ 历史人物（6）：孔子、孙子、诸葛亮、庄子、马基雅维利、克劳塞维茨
- ✅ 虚构人物（3）：福尔摩斯、赫敏·格兰杰、甘道夫
- ✅ 现代人物（3）：芒格、费曼、Naval

### Python 引擎（`src/engine/`）
- ✅ `persona.py`：加载人格文件，模糊匹配
- ✅ `discussion.py`：对话历史管理，调用 Gemini API
- ✅ `renderer.py`：rich 彩色输出，流式渲染
- ✅ `main.py`：示例入口

### 引擎优化（本批次）
- ✅ 流式输出（stream=True，告别等待）
- ✅ 修复 max_tokens 截断（1200→2000）
- ✅ 切换 gemini-2.0-flash（去掉 thinking，降低 TTFT）
- ✅ chunk 直写 stdout（绕过 rich markup 解析，真正实时）
- ✅ Prompt 强化（上一条发言单独摘出，强制先回应再立场）

### 争鸣质量优化（规划中）

#### 第一优先：对话感
- 🚧 **Moderator 动态发言顺序**（被反驳者优先接话）
  - Spec: `docs/superpowers/specs/2026-04-10-moderator-design.md`
  - Plan: `docs/superpowers/plans/2026-04-10-moderator.md`

#### 第二优先：人格感
- ⬜ **角色内化咒语**：在 system prompt 加 "Never forget you are X，keep insisting on your perspectives"，防止多轮后人格漂移

#### 第三优先：冲突感
- ⬜ **激怒触发点激活**：读取人格文件「争鸣坐标·被激怒触发点」字段，注入 prompt 情绪状态（Antagonist Injection）
- ⬜ **三步发言结构**：每次发言拆成 ①回应对方具体论点 ②亮立场 ③抛问题给下一个人

#### 后续迭代
- ⬜ 选择性历史注入（人多时 token 优化，触发条件：成本 > $0.05/次）

### 收尾
- ⬜ 端到端跑通验收
- ⬜ 录制 demo GIF
- ⬜ 更新 README

---

## Phase 2 · 视觉学宫

**目标**：本地启动像素风学宫界面，人物在场景中实时发言动画。

**前置条件**：Phase 1 争鸣质量优化完成

### 技术栈
| 组件 | 技术 |
|------|------|
| 场景渲染 | Phaser.js |
| 后端服务 | Flask + flask-socketio |
| 实时推送 | WebSocket |
| 桌面打包 | Electron（可选）|

### 任务
- ⬜ Flask 服务器 + WebSocket 桥接引擎输出
- ⬜ Phaser 场景基础搭建（学宫背景、人物占位）
- ⬜ 对话气泡动画（逐字显示，对应流式输出）
- ⬜ 人物说话动画
- ⬜ 开场/散场演出

---

## Phase 3 · 人格生态

**目标**：开放人格生态，支持外部导入和融合。

- 💡 nuwa-skill 人格库直接导入
- 💡 支持用户带入自定义 SKILL.md 人格
- 💡 Hermes Agent skill 生态兼容
- 💡 炼丹炉：人格融合（独立项目，互相引用）
