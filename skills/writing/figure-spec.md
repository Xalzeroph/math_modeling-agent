# Figure-Spec — 确定性 JSON→SVG 算法流程图

**执行角色**: 论文手  
**时机**: 论文撰写时（SOP Stage 7）  
**输入**: 流程图的节点和边的描述  
**输出**: SVG 文件到 figures/

---

## 目标

用 JSON 描述流程图/架构图/算法步骤图的结构，再用 Python 确定性渲染为 SVG。同一张 spec 永远生成同样的 SVG——可复现、可版本控制、不依赖外部 API。

---

## 使用方式

### Step 1: 定义 JSON spec

```json
{
  "nodes": [
    {"id": "input", "label": "原始数据", "shape": "rectangle", "x": 50, "y": 50},
    {"id": "prep", "label": "数据预处理", "shape": "rectangle", "x": 50, "y": 140},
    {"id": "ahp", "label": "AHP 层次分析", "shape": "rectangle", "x": 50, "y": 230},
    {"id": "output", "label": "评价结果", "shape": "rounded", "x": 50, "y": 320}
  ],
  "edges": [
    {"from": "input", "to": "prep", "label": ""},
    {"from": "prep", "to": "ahp", "label": "判断矩阵"},
    {"from": "ahp", "to": "output", "label": "权重向量"}
  ]
}
```

### Step 2: 渲染为 SVG

```python
# 使用确定性渲染器（见下方模板代码）
# 不依赖外部 API，纯 Python stdlib + xml.etree
```

### Step 3: 调整布局

- 重排节点位置以优化视觉
- 确认标签不重叠
- 保存到 figures/ 为 SVG

---

## 常用图表模板

### 算法流程图
- 纵向流程：节点垂直排列
- 箭头连接
- 菱形表示判断节点

### 模型架构图
- 分层布局：输入层 → 处理层 → 输出层
- 方框表示组件
- 层级之间用分组框

### AHP 层次图
- 三层金字塔：目标层 → 准则层 → 方案层
- 连线表示权重关系

### 审计级联图
- 多列布局：code → result → claim → citation
- 箭头表示数据流
- 标注 audit gate

---

## SVG 渲染模板

```python
import xml.etree.ElementTree as ET
from pathlib import Path

def render_svg(spec: dict, output_path: str):
    """确定性 JSON→SVG 渲染器"""
    ns = "http://www.w3.org/2000/svg"
    svg = ET.Element("svg", {
        "xmlns": ns,
        "viewBox": "0 0 800 600",
        "width": "800",
        "height": "600"
    })
    
    # 画边
    for edge in spec.get("edges", []):
        # 查找起止节点坐标
        fnode = next(n for n in spec["nodes"] if n["id"] == edge["from"])
        tnode = next(n for n in spec["nodes"] if n["id"] == edge["to"])
        line = ET.SubElement(svg, "line", {
            "x1": str(fnode["x"] + 60), "y1": str(fnode["y"] + 25),
            "x2": str(tnode["x"] + 60), "y2": str(tnode["y"]),
            "stroke": "#555", "stroke-width": "2",
            "marker-end": "url(#arrow)"
        })
    
    # 画节点
    for node in spec["nodes"]:
        # 方框
        rect = ET.SubElement(svg, "rect", {
            "x": str(node["x"]), "y": str(node["y"]),
            "width": "120", "height": "40",
            "rx": "5" if node.get("shape") == "rounded" else "0",
            "fill": "#E3F2FD", "stroke": "#1565C0", "stroke-width": "2"
        })
        # 标签
        text = ET.SubElement(svg, "text", {
            "x": str(node["x"] + 60), "y": str(node["y"] + 25),
            "text-anchor": "middle", "dominant-baseline": "central",
            "font-family": "SimHei, Microsoft YaHei, sans-serif",
            "font-size": "12", "fill": "#333"
        })
        text.text = node["label"]
    
    # 箭头标记
    defs = ET.SubElement(svg, "defs")
    marker = ET.SubElement(defs, "marker", {
        "id": "arrow", "markerWidth": "10", "markerHeight": "10",
        "refX": "9", "refY": "3", "orient": "auto"
    })
    ET.SubElement(marker, "path", {
        "d": "M0,0 L0,6 L9,3 z", "fill": "#555"
    })
    
    tree = ET.ElementTree(svg)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
```

---

## 关键规则

- 同一 spec → 同一 SVG（确定性，可复现）
- 不依赖外部 API 或 AI 生图（paper-illustration 是补充，不是替代）
- CJK 字体指定多备选：SimHei → Microsoft YaHei → sans-serif
- 保存为 SVG 到 `figures/`，LaTeX 直接引用
