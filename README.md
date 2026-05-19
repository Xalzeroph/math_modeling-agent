# Self-Evolving Mathematical Modeling Engine / 自进化数学建模引擎

A complete, conversational mathematical modeling system built on top of Claude Code.
No scripted pipelines — you talk, it works. After each contest, it learns and gets better.

对话即流水线，做完自动变强。

---

## Quick Start / 快速开始

1. 将此文件夹拖入 Claude Code
2. 说"帮我做这道数模题"（附上题目 PDF）
3. Claude 按 16 阶段 SOP 自然推进
4. 可随时打断、回溯、讨论 — 对话本身就是流水线

启动时自动创建 session 目录：

```bash
mkdir -p sessions/题目名称/{data,notes,solvers,verifications,figures,paper,assurance}
```

---

## Architecture / 架构

```
L1: Claude Code (大脑) — 推理、决策、代码生成、论文写作
       │
   ┌───┼───┐
   │       │        │
L2: 指引层   L3: 知识层    L4: 工具层
CLAUDE.md   algorithms/   tools/
roles/*.md  references/   assurance/
skills/     sessions/
```

L1 读 L2 知 HOW（权限矩阵、16阶段流程、质量基准）
L1 读 L3 知 WHAT（74算法、~1330论文、评分基线、历史经验）
L1 调 L4 做机械活（编译、搜索、评分、进化标记）

核心原则：**Python 做机械活，Claude Code 做洞见活。给 Claude 更好的信息，不是替 Claude 做决策。**

---

## 16-Stage SOP / 16 阶段流程

```
S0 → S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8 → S9 → S10 → S11 → S12 → S13 → S14 → S15
启动  分析  选择  ⏣审计  数据  求解  验证  ⏣审计  灵敏度 ⏣审计  论文  ⏣审计   编译   评分   进化   打包
```

| # | Stage | Role | Output |
|---|-------|------|--------|
| S0 | Startup & Pre-flight | 建模手 | Session dir + `assurance/level.txt` |
| S1 | Problem Analysis + 阅读门禁 | 建模手 | `notes/ProblemAnalysis.md`, `notes/阅读笔记_建模.md` |
| S2 | Model Selection & Scaffolding | 建模手 | `notes/交接清单.md` |
| S3 | ⏣ Model Audit (Gate 1) | 审稿手 | `assurance/proof_audit.json`, `idea_audit.json` |
| S4 | Data Preprocessing + 阅读门禁 | 编程手 | Preprocessed data |
| S5 | Model Solving | 编程手 | `solvers/*.py`, `figures/`, `results/` |
| S6 | Model Verification | 编程手 | `verifications/*.py`, `notes/trial_log.md` |
| S7 | ⏣ Implementation Audit (Gate 2) | 审稿手 | `assurance/code_audit.json`, `claim_map.md` |
| S8 | Sensitivity Analysis | 建模手 | `notes/sensitivity.md` |
| S9 | ⏣ Sensitivity Audit (Gate 3) | 审稿手 | `assurance/sensitivity_audit.json` |
| S10 | Paper Writing + 阅读门禁 | 论文手 | `paper/main.tex` |
| S11 | ⏣ Paper Audit (Gate 4) | 审稿手 | `assurance/claim_audit.json`, etc. |
| S12 | Final Compilation | 论文手 | `paper/main.pdf` |
| S13 | Assurance Gate & Scoring | 自动 | `gate_manifest.json`, `eval_report.json` |
| S14 | Evolution & Knowledge | 自动+AI | Role doc EVOLUTION anchors updated |
| S15 | Packaging & Submission | — | `提交.zip` |

每个 `⏣` 是硬审计关卡，不可跳过。

### Runtime Rules / 运行时规则

1. **写入权限矩阵**: 每个阶段有明确的目录写/禁写权限
2. **前置依赖**: 进入任何阶段前检查产物文件是否存在
3. **质量分级**: 每个产出按可接受□/良好✅/优秀⭐ 三级评价
4. **致命度分级**: 审稿手用 🔴BLOCKED / 🟡WARN / 🟢PASS 三级判决

### Model Selection Principles / 模型选择三原则

1. 能用初等方法解决的就不用高等方法
2. 能用简单方法解决的就不用复杂方法
3. 能用被更多人看懂理解的方法就不用少数人懂的方法

### Verification Protocols / 验证标准

| Model Type | Checks |
|-----------|--------|
| Optimization | [V-OPT] Constraint feasibility, Cross-verification, Perturbation test |
| Regression/ML | [V-REG] Shapiro-Wilk, Breusch-Pagan, Durbin-Watson, 5-fold CV |
| ODE/Dynamics | [V-ODE] Conservation, Boundary conditions, Grid convergence |
| Network/Graph | [V-GRF] Path legality, Flow conservation, Small-scale brute force |

---

## 12 Tools / 工具

Python = 机械活, Claude Code = 洞见活

| Category | Tool | Purpose | Stage |
|----------|------|---------|-------|
| File Ops | `compile_latex.py` | Compile .tex to .pdf (multi-pass) | S12 |
| | `pdf_extractor.py` | Extract text/tables from PDFs | S1 |
| | `data_checker.py` | Encoding detection + data quality | S4 |
| | `check_outputs.py` | Post-compile integrity check | S12 |
| Search | `paper_search.py` | Multi-source academic search | S1 |
| | `local_knowledge.py` | 3-source local knowledge retrieval | S0-S1 |
| Evolution | `scorer.py` | 10-dim scoring + auto-save | S13 |
| | `evolver.py` | Mechanical + insight evolution | S14 |
| Assurance | `contract.py` | 6-state verdict engine + SHA256 tracing | S2-S13 |
| | `gate.py` | Collect audits → gate_manifest.json | S13 |
| | `query_pack.py` | Cross-session knowledge summary | S0/S14 |

---

## Knowledge Assets / 知识资产

| Asset | Location | Content |
|-------|---------|---------|
| Algorithm Library | `algorithms/index.json` + `algorithms/*.md` | 9 domains, 27 subdomains, 74 methods |
| Paper Library | `references/papers/` | ~1330 indexed PDFs, 6 categories / 28 subcategories |
| Scoring Baselines | `references/empirical_baselines.json` | 10-dim p25/p50/p75 |
| Antipattern Library | Embedded in role EVOLUTION anchors | 28 antipatterns |
| Review Criteria | `references/官方资料/评阅要点/` | CUMCM 2004-2018 |
| Experience Sharing | `references/官方资料/经验分享/` | Tutorials, writing guides |
| LaTeX Templates | `templates/` | CUMCM + MCM templates |
| Evolution Records | `roles/` EVOLUTION sections | Accumulated experience |

---

## Directory Structure / 目录结构

```
E:\math_modeling\
├── CLAUDE.md                  # 入口 — 权限矩阵 + 16阶段流程 + 工具索引
├── README.md                  # 本文件（人类文档）
│
├── algorithms/                # 算法知识库
│   ├── index.json             #   9 domains / 27 subdomains / 74 methods
│   └── 01~07-*.md             #   详细算法文档
│
├── roles/                     # 角色文档（自进化）
│   ├── 建模手.md               #   Modeler: 写入权限 + 质量基准 + 执行流程 + EVOLUTION
│   ├── 编程手.md               #   Coder: 同上结构
│   ├── 论文手.md               #   Writer: 同上结构
│   ├── 审稿手.md               #   Auditor ★: 只审不修 + 致命度分级
│   └── 路径说明.md             #   Path reference
│
├── skills/                    # 执行指令（按需调用）
│   ├── audit/ (7 files)
│   ├── modeling/ (2 files)
│   └── writing/ (6 files)
│
├── templates/                 # LaTeX 模板
│   ├── latex_template.tex     #   CUMCM (国赛)
│   └── mcm_template.tex       #   MCM/ICM (美赛)
│
├── tools/                     # Python CLI 工具
│   ├── assurance/ (contract.py, gate.py, query_pack.py)
│   ├── evolution/ (evolver.py, scorer.py)
│   ├── file_ops/ (compile, extract, check, svg2pdf, data)
│   └── search/ (paper_search.py, local_knowledge.py)
│
├── references/
│   ├── papers/                #   6 类 ~1330 篇论文 (PDF gitignored)
│   ├── papers_metadata.json
│   ├── empirical_baselines.json
│   ├── patterns/              #   反模式库
│   └── 官方资料/              #   评阅要点 + 经验分享
│
└── sessions/                  # 问题存档
    └── 问题名/                 #   每题的完整记录
```

---

## Self-Evolution / 自进化

每个问题完成后 (S14), evolver 更新:

| File | What is updated |
|------|----------------|
| `roles/建模手.md` | Experience section + Verified algorithms table |
| `roles/编程手.md` | Code templates + Pitfalls |
| `roles/论文手.md` | Paper case studies + Writing lessons |

下次问题启动时自动加载:
```bash
evolver.py suggest --problem-type optimization   → best strategy
evolver.py gaps                                  → uncovered types
query_pack.py --problem-type X                   → cross-session knowledge
```
