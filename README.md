# 稷下学宫 · JiXia Academy

> 召唤任意人物，组成你的圆桌。抛出一个议题——看他们因你而争鸣。

战国时期，齐国稷下汇聚百家之学，儒道法墨，争鸣不休。今日重开学宫：你来选人，你来出题，然后坐在帘后，看他们为你而争。

不给你答案。给你没想到过的角度。

---

## 演示

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  稷 下 学 宫 · 今 日 议 题
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  「开放世界游戏给玩家无限自由，是好的设计吗？」
  入席：宫本茂 · 乔布斯 · 马基雅维利 · 庄子
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

宫本茂      │ 自由本身不是目的。玩家要的不是无限，是有意义的选择。
            │ 给一个人无限画布，他画不出东西。给他一张有边界的纸，他才开始思考。

乔布斯      │ 宫本，你说的是设计，我说的是体验。
            │ 真正的自由不是选项多，是每个选项都让人觉得"对"。
            │ 大多数开放世界失败，不是因为太自由——是因为自由得太廉价。

*马基雅维利冷眼看着两人，缓缓开口*

马基雅维利  │ 你们都在讨论玩家想要什么。错了。
            │ 问题是：设计者想让玩家去哪里。
            │ 优秀的开放世界是一座迷宫——玩家以为自己在选择，实则走在你铺好的路上。

庄子        │ ……有意思。你们三个都在"设计自由"。
            │ 但鱼在水中，从不思考水的边界。
            │ 也许最好的开放世界，是让玩家忘记自己在被设计。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  今日学宫，就此散场。你怎么看？
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 快速开始

**方式一：Claude Code Skill（推荐）**

```bash
# 全局安装
npx skills add Cooperzheng/JiXia-Academy

# 触发
稷下学宫，召唤孔子、马斯克、巴菲特、诸葛亮，议题：我应该辞职创业吗？
```

**方式二：直接复制 SKILL.md**

将 `SKILL.md` 放入你的项目 `.claude/skills/jixia-academy/` 目录，重启 Claude Code 即可。

---

## 特性

- **任意人物**：历史人物、现代人物、虚构角色，均可入席
- **真实回应**：每位人物看到并回应前面的发言，而非各说各话
- **流式输出**：逐字流式，对话实时展开，过程即体验
- **舞台提示**：偶发场景描写，把对话变成剧场
- **开箱即用**：三套预设开局，零配置即可体验
- **冲突优先**：不追求共识，追求真实的思想碰撞

---

## 预设开局

| 开局 | 入席人物 | 适合议题 |
|------|---------|---------|
| 🗡️ 战略局 | 孙子、诸葛亮、马基雅维利、克劳塞维茨 | 竞争、决策、博弈 |
| 💡 创新局 | 乔布斯、特斯拉、达芬奇、黄仁勋 | 产品、技术、设计 |
| 🌀 哲思局 | 庄子、苏格拉底、尼采、加缪 | 意义、价值、存在 |

---

## 路线图

**v0.1 · 争鸣内核**（当前）
- [x] Claude Code Skill 核心逻辑
- [x] 流式对话引擎，人物互相回应
- [x] 三套预设开局
- [ ] 预制人格库（对接 [anyone-to-skill](https://github.com/OpenDemon/anyone-to-skill)）

**v0.2 · 视觉学宫**
- [ ] 像素风学宫场景（Phaser.js）
- [ ] 角色实时动画，对话气泡渲染
- [ ] 参考：[Star Office UI](https://github.com/ringhyacinth/Star-Office-UI)

**v0.3 · 人格生态**
- [ ] 支持导入自定义 SKILL.md 人格
- [ ] 兼容 [Hermes Agent](https://github.com/NousResearch/hermes-agent) skill 生态
- [ ] 炼丹炉：人格融合模块（独立项目）

---

## 参考项目

| 项目 | 用途 |
|------|------|
| [nuwa-skill](https://github.com/alchaincyf/nuwa-skill) | 现代人格库（心智模型 + 决策启发式）|
| [Microsoft AutoGen](https://github.com/microsoft/autogen) | 多 Agent 讨论引擎 |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | 流式 UI、skill 生态 |
| [edict 三省六部](https://github.com/cft0808/edict) | Agent 隔离思路 |
| [Star Office UI](https://github.com/ringhyacinth/Star-Office-UI) | 像素风 Agent 可视化（Phase 2）|
| [soul.md](https://github.com/aaronjmars/soul.md) | 人格格式规范 |

---

## Contributing

欢迎提交新的预设人格、改进讨论引擎、或参与 v0.2 视觉学宫的开发。

详见 [CONTRIBUTING.md](CONTRIBUTING.md)（即将添加）

---

## License

MIT © [Cooperzheng](https://github.com/Cooperzheng)
