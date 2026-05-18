# Research-Lit — 多源文献检索

**执行角色**: 建模手  
**时机**: SOP Stage 1  
**输入**: 题目类型 + 关键词  
**输出**: `notes/ProblemAnalysis.md` 中的文献章节

---

## 目标

在建模选型之前，检索与题目类型和候选模型相关的学术文献，为选型提供依据。

---

## 检索流程

### Step 1: 确定检索词

从题目中提取：
- 问题类型关键词（如 "线性规划"、"时间序列预测"、"AHP层次分析"）
- 领域关键词（如 "资源调度"、"交通流"、"水质评价"）
- 方法关键词（如 "genetic algorithm optimization"、"grey prediction model"）

### Step 2: 多源检索（按优先级）

#### 源 1: arXiv API（优先）

```
http://export.arxiv.org/api/query?search_query={query}&max_results=10
```

- 优点：学科覆盖全、有完整元数据、开源论文
- 缺点：只覆盖 preprint

#### 源 2: Semantic Scholar API

```
https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=10
```

- 优点：有引用数、发表 venue
- 缺点：主要覆盖 CS 和数学

#### 源 3: OpenAlex API（补充）

```
https://api.openalex.org/works?search={query}&per_page=10
```

- 优点：2.5 亿+ 文献，跨学科
- 缺点：元数据质量不如专用源

#### 源 4: 现有项目资源

```
references/papers/{题型分类}/
algorithms/{题型分类}*.md（算法文档中的关键文献表格）
```

### Step 3: 去重和排序

1. 跨源去重：按 arXiv ID / DOI / 标题相似度合并
2. 排序：引用数 > 发表年份 > 相关性
3. 每篇标注：标题、作者、年份、来源、简短摘要（1-2 句话）

---

## 输出格式

在 `notes/ProblemAnalysis.md` 的文献章节写入：

```markdown
## 文献检索结果

### 检索词
- "linear programming resource allocation"
- "AHP evaluation model"
- "multi-objective optimization"

### 检索结果（去重后）
| # | 论文 | 作者 | 年份 | 来源 | 相关性 |
|---|------|------|------|------|--------|
| 1 | A Survey of Multi-Objective Optimization | Smith et al. | 2024 | arXiv | ★★★ |
| 2 | AHP-based Decision Making | Saaty | 1980 | 经典 | ★★★ |
| 3 | Recent Advances in LP | Chen et al. | 2023 | S2 | ★★ |
| ... | | | | | |
```

---

## 常见检索模板

| 题型 | 推荐检索词 |
|------|-----------|
| 优化 | `"{method}" optimization`、`"{domain}" resource allocation` |
| 预测 | `"{method}" prediction time series`、`"grey prediction model {domain}"` |
| 评价 | `"{method}" multi-criteria decision`、`"AHP application {domain}"` |
| 图论 | `"shortest path {domain}"`、`"network flow optimization"` |

---

## 关键规则

- 先查本地（references/papers/ + algorithms/），再查外部 API
- arXiv API 失败不阻塞——直接用 S2 或本地文献
- 只留真正相关的，不堆数量
- 中文论文优先查 GB/T 7714 格式的来源（知网/万方）  
- 每篇论文标注它和当前题目有什么关系
