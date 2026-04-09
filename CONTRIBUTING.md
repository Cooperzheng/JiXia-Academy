# 贡献指南 · Contributing Guide

欢迎参与稷下学宫的建设！以下是三种最有价值的贡献方式。

---

## 贡献方式一：提交新人格

这是最受欢迎的贡献。按 nuwa-skill 格式编写一个历史/虚构人物的人格文件。

**文件位置**
- 历史人物：`personas/historical/<人物拼音>.md`
- 虚构人物：`personas/fictional/<人物英文名>.md`
- 现代人物：直接引用 nuwa-skill，无需重复建

**格式模板**（参考 `personas/historical/confucius.md`）

```markdown
---
name: 人物姓名
era: 时代（如：春秋时期 / 19世纪 / 虚构）
source: 数据来源（著作、影视作品等）
---

## 心智模型
（3-5个该人物观察世界的核心框架）

## 决策启发式
（5-8条该人物做决定时的思维定势）

## 表达 DNA
（语言风格、标志性句式、常用意象）

## 诚实边界
（该人格无法准确模拟的部分）
```

**质量标准**
- 基于一手资料（原著、可信传记、原始访谈），而非二手印象
- 心智模型要能预测该人物对未知问题的立场
- 不写刻板印象，写真实的思维框架

---

## 贡献方式二：改进讨论引擎

核心逻辑在 `SKILL.md` 和 `src/engine/`。

改进前请先开 Issue 描述你的想法，确认方向再动手，避免白费功夫。

---

## 贡献方式三：反馈真实体验

用过之后觉得哪个人物回应不对、哪种议题效果差、哪里卡壳——直接开 Issue 描述。

真实的体验反馈比代码贡献更稀缺。

---

## 提交 PR 规范

1. Fork 本仓库，在你的分支上修改
2. PR 标题格式：`feat: 新增孙子人格` / `fix: 修复发言顺序逻辑`
3. 描述你的修改解决了什么问题
4. 人格文件需附上你测试过的 1-2 个议题示例输出

---

## 本地开发

```bash
git clone https://github.com/Cooperzheng/JiXia-Academy.git
cd JiXia-Academy

# 把 SKILL.md 安装到 Claude Code 全局
cp -r . ~/.claude/skills/jixia-academy/

# 在 Claude Code 中测试
稷下学宫，召唤孔子和马斯克，议题：AI 会取代人类创造力吗？
```
