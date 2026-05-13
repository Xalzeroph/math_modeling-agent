# 建模归档

每次做题都会在这里创建一个 session 目录。

## 目录结构

```
sessions/题目名称/              ← 做题前自动创建（见 CLAUDE.md）
├── data/                       ← 题目 PDF 和数据文件放这里
├── notes/                      ← 分析文档（阶段1→6 产出）
├── solvers/                    ← 求解代码（阶段2→4 产出）
├── verifications/              ← 验证脚本（阶段5 产出）
├── figures/                    ← 图表（阶段4 产出）
├── paper/                      ← 论文（阶段7→8 产出）
└── eval_report.json            ← 评分报告（阶段9 自动生成）
```

## 快速开始

```bash
# 1. Claude Code 在开始新题时自动创建 session 目录
mkdir -p sessions/题目名称/{data,notes,solvers,verifications,figures,paper}

# 2. 把题目 PDF 和数据放进 data/
# 3. 然后对 Claude Code 说"帮我做这道数模题"
```

## 已有 session

| Session | 阶段 | 说明 |
|---------|------|------|
| （等待第一道题） | — | 用一次就有一个 |

> `.gitkeep` 文件占位保目录。`eval_report.json` 会被 git 跟踪。
> 其他文件（代码、论文、图表等）自动忽略，不提交到仓库。
