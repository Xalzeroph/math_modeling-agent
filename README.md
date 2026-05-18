# Self-Evolving Mathematical Modeling Engine / 自进化数学建模引擎

A complete, conversational mathematical modeling system built on top of Claude Code.
No scripted pipelines — you talk, it works. After each contest, it learns and gets better.

对话即流水线，做完自动变强。

---

## Quick Start / 快速开始

1. Drop this folder into Claude Code / 将此文件夹拖入 Claude Code
2. Say "Help me solve this math modeling problem" (attach the problem PDF) / 说"帮我做这道数模题"
3. Claude follows the 12-stage SOP naturally through conversation / 按对话自然推进 12 个阶段
4. Interrupt, backtrack, discuss at any time — conversation IS the pipeline / 可随时打断、回溯、讨论

When you start a new problem, Claude creates the full session directory upfront:

```bash
mkdir -p sessions/题目名称/{data,notes,solvers,verifications,figures,paper,assurance}
```

---

## Architecture / 架构

```
L1: Claude Code (大脑)
   推理、决策、代码生成、论文写作、对话上下文
       │
   ┌───┼───┐
   │       │       │
L2: 指引层  L3: 知识层   L4: 工具层
(行为规范)  (结构化数据)  (确定性操作)
   │       │       │
SOP.md     algorithms/  file_ops/
CLAUDE.md  references/  search/
roles/*.md sessions/    evolution/
```

L1 reads L2 to know HOW to act (SOP, role specs, checklists, constraints).
L1 reads L3 to know WHAT is available (algorithms, papers, baselines, past experience).
L1 calls L4 to do what it CANNOT (compile, search APIs, score, evolve markers).
L4 writes back to L3 (eval_report.json, evolved_status, verified algorithms).

Core principle: **Python = mechanical work (deterministic, Claude cannot do). Claude Code = insight work (understanding, judgment, writing). Give Claude better information, don't code Claude's decisions.**

核心原则：**Python 做机械活（确定性的，Claude 做不到的）。Claude Code 做洞见活（理解、判断、写作）。给 Claude 更好的信息，而不是替 Claude 做决策。

## 10-Stage SOP / 10 阶段流程

```
Problem Analysis → Model Selection & Scaffolding → Data Preprocessing 
→ Model Solving → Verification → Sensitivity Analysis → Paper Writing 
→ Final Compilation → Scoring & Evolution → Packaging & Submission
```

| # | Stage / 阶段 | Lead Role / 主导 | Output / 产出 | Tool Used / 工具 |
|---|-------------|-----------------|---------------|-----------------|
| 1 | Problem Analysis / 问题分析 | Modeler / 建模手 | `notes/题目分析.md` | `local_knowledge.py`, `paper_search.py`, `evolver.py suggest` |
| 2 | Model Selection & Scaffolding / 模型选择与构建 | Modeler→Coder | `solvers/problem{n}.py` skeleton / 骨架 | — |
| 3 | Data Preprocessing / 数据预处理 | Coder / 编程手 | Cleaned data / 规范化数据 | `data_checker.py` |
| 4 | Model Solving / 模型求解 | Coder / 编程手 | `solvers/*.py` + `figures/` | — |
| 5 | Verification / 模型验证 | Coder / 编程手 | `verifications/verify{n}.py` | — (Claude runs directly) |
| 6 | Sensitivity Analysis / 灵敏度分析 | Modeler / 建模手 | `notes/sensitivity.md` | — |
| 7 | Paper Writing / 论文撰写 | Writer / 论文手 | `paper/main.tex` | — (copy template first, fill without modifying format) |
| 8 | Final Compilation / 最终编译 | Writer / 论文手 | `paper/main.pdf` | `compile_latex.py`, `check_outputs.py` |
| 9 | Scoring & Evolution / 评分进化 | — | Score report + evolved roles / 评分报告+进化 | `scorer.py`, `evolver.py --from-scorer` |
| 10 | Packaging & Submission / 打包提交 | — | `提交.zip` | — |

### Hard Gates / 硬门禁

1. Verification must ALL PASS before entering paper stage / 验证全部 PASS 才进论文
2. LaTeX template format MUST NOT be modified — only fill content inside `\begin{document}...\end{document}` / 禁止修改模板格式
3. Every figure must have ≥100 words of analysis — no naked figures / 每张图 ≥100 字分析
4. Never modify raw data files in `data/` / 禁止修改原始数据文件
5. Never create simplified/alternative code to dodge problems / 禁止创建简化版代码
6. Never skip verification and silently proceed / 禁止跳过验证
7. Never claim code is "verified" without actually running it / 禁止未运行就声称已验证

### Verification Protocols / 验证标准

**Optimization Models (LP/QP/MIP/NLP):**
- [V-OPT-1] Constraint feasibility — all constraints strictly satisfied
- [V-OPT-2] Cross-validation with alternative solver
- [V-OPT-3] Perturbation testing
- [V-OPT-4] Quick sensitivity check

**Regression/ML Models:**
- [V-REG-1] Residual normality — Shapiro-Wilk test (p > 0.05)
- [V-REG-2] Heteroscedasticity — Breusch-Pagan test
- [V-REG-3] Autocorrelation — Durbin-Watson (1.5 < DW < 2.5)
- [V-REG-4] 5-fold cross-validation
- [V-REG-5] Bootstrap stability

**ODE/Dynamics Models:**
- [V-ODE-1] Conservation law verification
- [V-ODE-2] Boundary condition check
- [V-ODE-3] Grid convergence
- [V-ODE-4] Known analytical solution comparison

**Graph/Network Models:**
- [V-GRF-1] Path validity
- [V-GRF-2] Flow conservation
- [V-GRF-3] Small-scale brute-force verification

### Model Selection Principles / 模型选择三原则

1. Use elementary methods when they suffice — don't reach for advanced ones
2. Use simple methods when they work — don't reach for complex ones
3. Use methods more people can understand — don't reach for obscure ones

---

## 9 Tools / 9 个工具

Python = 机械活 (确定性的，Claude 做不到), Claude Code = 洞见活 (需要理解和判断)

| Category / 类别 | Tool / 工具 | Purpose / 用途 | When / 时机 |
|----------------|------------|---------------|------------|
| **File Ops** | `file_ops/compile_latex.py` | Compile .tex to .pdf (xelatex/pdflatex multi-pass) | Stage 8 |
| | `file_ops/pdf_extractor.py` | Extract text and tables from PDFs | Reading problem PDFs |
| | `file_ops/data_checker.py` | Deterministic encoding detection + data quality report | Stage 3 |
| | `file_ops/check_outputs.py` | Post-compile integrity (encoding, figure refs, solver-verify pairs, pages) | Stage 8 |
| | `file_ops/batch_extract.py` | Batch PDF stats extraction (pages, chars, figures, tables, equations) | Paper library analysis |
| **Search** | `search/paper_search.py` | Multi-source academic search (arXiv + OpenAlex + Semantic Scholar) | Stage 1 |
| | `search/local_knowledge.py` | Synonym-mapped local search (algorithms + papers + evolution) | Stage 1 |
| **Evolution** | `evolution/scorer.py` | 10-dim percentile scoring, auto-saves to `eval_report.json` | Stage 9 |
| | `evolution/evolver.py` | Mechanical work: update verified algorithm tables, mark index.json, produce structural score analysis. Claude Code writes experiential insights to role docs. | Stage 9 |

### Tool Usage Flow / 工具调用流

```
Stage 1:  local_knowledge.py "关键词"              → algorithms + papers + past scores
          paper_search.py --query "..."            → external academic papers
          evolver.py suggest --problem-type X      → best strategy + weak_dimensions

Stage 3:  data_checker.py info --file ...          → deterministic encoding/format report

Stage 8:  compile_latex.py compile --mode cumcm
          check_outputs.py --session "..."         → integrity checks

Stage 9:  scorer.py --session "..." --mode standard  → scoring + auto-save eval_report.json
          evolver.py evolve --session "..." --from-scorer  → mechanical work + analysis JSON
          (then Claude Code reads analysis + session files, writes experience to role doc anchors)
```

---

## Knowledge Assets / 知识资产

| Asset / 资产 | Location / 位置 | Content / 内容 |
|-------------|----------------|----------------|
| Algorithm Library / 算法库 | `algorithms/index.json` + `algorithms/*.md` | 9 domains, 27 subdomains, 74 methods with 46 cross-references + MATLAB→Python mapping |
| Paper Library / 论文库 | `references/papers/` | **~1330 indexed PDFs** in 6 categories / 28 subcategories |
| Scoring Baselines / 评分基线 | `references/empirical_baselines.json` | 10-dimension p25/p50/p75 distributions with confidence levels |
| Antipattern Library / 反模式库 | Embedded in role EVOLUTION anchors | 28 antipatterns distributed by topic (abstract/assumptions/model/code/verification/sensitivity) |
| Official Review Criteria / 评阅要点 | `references/官方资料/评阅要点/` | 2004-2018 CUMCM official review criteria |
| Experience Sharing / 经验分享 | `references/官方资料/经验分享/` | Modeling tutorials, paper writing guides, MCM tips |
| Historical Scores / 历史评分 | `sessions/*/eval_report.json` | Auto-saved score reports, queried by evolver for strategy suggestions |
| LaTeX Templates / LaTeX模板 | `templates/` | CUMCM (国赛) + MCM/ICM (美赛) + MCM memo template |
| Evolution Records / 进化记录 | `roles/建模手.md`, `编程手.md`, `论文手.md` evolution sections | Accumulated experience in each role doc |
| Paper Metadata Index / 论文元数据 | `references/papers_metadata.json` | 1330 papers with year, contest, problem, award, team_id |

### Paper Library Structure / 论文库结构

| Category / 大类 | Subcategories / 子类 | Papers / 篇数 |
|----------------|---------------------|--------------|
| Optimization / 优化类 | Linear Programming, Genetic Algorithm, Dynamic Programming | 142 |
| Evaluation / 评价类 | AHP, TOPSIS, Fuzzy Comprehensive Evaluation | 112 |
| Prediction / 预测类 | Time Series, Grey Prediction, Grey Relational | 70 |
| Statistics / 统计类 | Regression, Clustering, PCA, SVM, Interpolation, Logistic, Factor, Variance, CCA | 609 |
| Graph & Network / 图论网络类 | Shortest Path, Cellular Automata, Decision Tree | 91 |
| Simulation & Comprehensive / 仿真综合类 | Simulated Annealing, ACO, PSO, Neural Networks, Queuing, Monte Carlo, Markov, etc. | 221 |
| **Total / 总计** | **28 subcategories** | **~1330** |

---

## Self-Evolution / 自进化

After each problem (Stage 9), the evolver writes to **4 files**:

| File / 文件 | What is updated / 更新内容 |
|------------|--------------------------|
| `roles/建模手.md` | Experience section (success) / Lesson section (failure) / Verified algorithms table |
| `roles/编程手.md` | Code templates (latest working solver) / Pitfalls (failed attempts) |
| `roles/论文手.md` | Paper case studies (abstract + section structure) / Writing lessons |
| `algorithms/xx.md` | `<!-- EVOLVED: verified ... -->` tag on matching algorithm headers |

Before the next problem, Claude reads these to get smarter:
```bash
evolver.py suggest --problem-type optimization  → best strategy + failure patterns
evolver.py gaps                                 → uncovered problem types + unverified algorithms
```

---

## Directory Structure / 目录结构

```
E:\math_modeling\
├── CLAUDE.md              # Entry point — identity + modeling flow + tool reference
├── SOP.md                 # 12-stage SOP + ARIS assurance framework
├── README.md              # This file
│
├── algorithms/            # Algorithm knowledge base
│   ├── index.json         #   9 domains / 27 subdomains / 74 methods
│   ├── code_index.json    #   MATLAB → Python mapping
│   ├── code/              #   Historical contest code (MATLAB/Jupyter)
│   └── 01~07-*.md         #   Detailed algorithm docs with cross-references
│
├── roles/                 # Role documents (self-evolving)
│   ├── 建模手.md           #   Modeler
│   ├── 编程手.md           #   Coder
│   ├── 论文手.md           #   Writer
│   ├── 审稿手.md           #   Auditor ★ (ARIS assurance)
│   └── 路径说明.md         #   Path reference table
│
├── skills/                # Executable skill instructions (ARIS)
│   ├── audit/             #   6 auditor skills
│   ├── modeling/          #   2 modeler skills
│   └── writing/           #   7 writer skills
│
├── templates/             # LaTeX templates
│   ├── latex_template.tex #   CUMCM (国赛)
│   ├── mcm_template.tex   #   MCM/ICM (美赛)
│   └── mcm_memo_template.tex
│
├── tools/                 # Python CLI tools (what Claude cannot do)
│   ├── file_ops/          #   Deterministic file operations
│   │   ├── compile_latex.py
│   │   ├── pdf_extractor.py
│   │   ├── data_checker.py
│   │   └── check_outputs.py
│   ├── search/            #   Information retrieval
│   │   ├── paper_search.py
│   │   └── local_knowledge.py
│   └── evolution/         #   Experience accumulation
│       ├── scorer.py
│       └── evolver.py
