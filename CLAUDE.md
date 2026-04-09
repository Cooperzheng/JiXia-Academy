# 稷下学宫 · 开发规范

## 项目定位

召唤任意人物组成圆桌，抛出议题，看他们因你而争鸣。
**有趣 > 实用**，冲突是产品，过程是体验。

## 目录结构

```
JiXia-Academy/
├── SKILL.md              # Claude Code skill 入口（核心）
├── CLAUDE.md             # 本文件
├── personas/
│   ├── historical/       # 历史人物人格文件
│   ├── fictional/        # 虚构人物人格文件
│   └── modern/           # 现代人物（引用 nuwa-skill，不重复建）
└── src/
    ├── engine/           # Phase 1：Python 讨论引擎
    └── ui/               # Phase 2：Phaser 视觉学宫
```

## 开发阶段

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1 | SKILL.md 争鸣内核 + 人格库 | 🚧 进行中 |
| Phase 2 | Flask + WebSocket + Phaser 视觉学宫 | 💡 计划中 |
| Phase 3 | nuwa-skill 生态接入 + Hermes 兼容 | 💡 计划中 |

## 核心设计原则

**争鸣优先**：每个人物必须看到并回应前面的发言，禁止各说各话。

**错位产生戏剧**：议题选择、人物组合都要最大化观点冲突，一致的圆桌是失败的圆桌。

**人格要真实，不要刻板**：孔子不只会说"子曰"，马斯克不只会说"go to Mars"。用思维框架，不用标签。

## 技术决策记录

| 决策 | 结论 | 原因 |
|------|------|------|
| 讨论引擎 | 自建轻量版，不用 AutoGen | 减少依赖，完全掌控对话历史和顺序逻辑 |
| Phase 2 桥接 | WebSocket | 复用 Star Office UI 的 Phaser 集成代码 |
| 人格格式 | 兼容 nuwa-skill | 直接复用其 13 个高质量现代人物人格 |

## 参考项目

| 项目 | 学什么 |
|------|--------|
| [nuwa-skill](https://github.com/alchaincyf/nuwa-skill) | 人格格式、蒸馏方法论 |
| [Star Office UI](https://github.com/ringhyacinth/Star-Office-UI) | Phaser + WebSocket 架构 |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | 流式 UI、skill 生态 |
| [edict](https://github.com/cft0808/edict) | Agent 隔离思路 |

## 新增人格的规范

参见 `CONTRIBUTING.md`。核心：基于一手资料，提取心智模型，不写刻板印象。

## 每次开发前检查

- [ ] 改动是否影响 SKILL.md 的核心争鸣逻辑？
- [ ] 新人格是否有真实资料支撑，而非印象拼凑？
- [ ] Phase 2 的改动是否与 WebSocket 事件格式保持一致？
