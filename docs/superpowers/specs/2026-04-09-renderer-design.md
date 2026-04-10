# renderer.py 设计文档

**日期**：2026-04-09
**阶段**：Phase 1 v1.1 — rich 彩色输出

---

## 目标

将 `discussion.run()` 的纯文本输出升级为 rich 彩色终端输出：
- 每个人格一种颜色，发言时名字和文本都带色
- 开场/散场框用 rich Rule 渲染，视觉清晰
- 舞台提示（`*...*` 格式）用斜体灰色渲染
- `main.py` 只需把 `print(line)` 替换为 `render(...)` 调用

---

## 设计

### 颜色分配

最多支持 5 人，从固定调色板按顺序分配：

```python
_PALETTE = ["cyan", "yellow", "magenta", "green", "red"]
```

### 输出行解析规则

`discussion.run()` yield 的每种行：

| 行格式 | 渲染方式 |
|--------|---------|
| 以 `━` 开头 | `rich.rule` 或直接 `console.print` 加 bold |
| `{name}\t│ {text}` | 名字 bold+色，`│` 白色，文字带色 |
| `*...*` | dim italic（舞台提示）|
| 空字符串 | 空行 |

### 接口

```python
def render(lines: Generator[str, None, None], color_map: dict[str, str]) -> None

def make_color_map(personas: list[Persona]) -> dict[str, str]
```

### main.py 改动

```python
# 改前
for line in discussion.run():
    print(line)

# 改后
from .renderer import render, make_color_map
color_map = make_color_map(personas)
render(discussion.run(), color_map)
```

---

## 文件

```
src/engine/
├── renderer.py    # 新建
└── main.py        # 修改：用 render() 替换 print loop
requirements.txt   # 追加 rich
```
