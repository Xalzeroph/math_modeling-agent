# Paper-Illustration — AI 生成论文概念图

**执行角色**: 论文手  
**时机**: 论文撰写时（SOP Stage 7，**可选**）  
**输入**: 概念描述  
**输出**: SVG 到 figures/

---

## 定位

与 figure-spec（算法流程图/架构图）互补：

| 类型 | 用什么 | 何时用 |
|------|--------|--------|
| 算法流程图/架构图 | figure-spec（确定性 JSON→SVG，零依赖） | 默认 |
| 方法概念示意图 | paper-illustration（AI 生图，需 API key） | 仅当有 API key 时 |
| 数据可视化图 | 编程手生成（matplotlib SVG） | 数据结果展示 |

**没有 API key → 跳过此步骤。不影响论文。**

---

## 使用方式

### Step 1: 检查可行性

```
若有 GEMINI_API_KEY 环境变量或类似可用图片生成 API → 继续
若无 → 输出 "无 API key，跳过 paper-illustration" 并结束
```

### Step 2: 描述需求

```markdown
## 概念图需求

**标题**: 多目标优化 Pareto 前沿示意图
**用途**: 展示两目标优化中 Pareto 最优解集和支配关系
**核心元素**:
- 坐标轴: x=目标1（成本），y=目标2（效率）
- Pareto 前沿曲线（右下凹）
- 标注: "Pareto 前沿"、"支配区域"、"不可行区域"
- 配色: 蓝色主调
**风格**: 学术论文插图，简洁，无背景装饰
```

### Step 3: 生成和审查

1. 用 AI 图生成工具生成（如 Gemini API）
2. 论文手审查：是否符合描述？是否过度装饰？文字是否可读？
3. 不满意 → 修改描述重新生成
4. OK → 导出 SVG 到 figures/

---

## 约束

- **不复制论文内容**: 不能和参考论文的图雷同
- **风格一致**: 配色蓝色主调
- **不替代编程手**: 数据可视化必须是 matplotlib SVG，不能用 AI 图代替
- **不替代 figure-spec**: 精确流程图用 figure-spec，概念图才用 AI
- **无 API key 时静默跳过**: 论文质量不受影响

---

## 输出

SVG 保存到 `figures/`，在 main.tex 中引用：

```latex
\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{figures/concept_pareto.svg}
    \caption{多目标优化 Pareto 前沿示意图}
    \label{fig:concept_pareto}
\end{figure}
```
