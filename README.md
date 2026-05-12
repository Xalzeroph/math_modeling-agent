# Self-Evolving Mathematical Modeling Engine / 自进化数学建模引擎

A complete, conversational mathematical modeling system built on top of Claude Code.
No scripted pipelines — you talk, it works. After each contest, it learns and gets better.

对话即流水线，做完自动变强。

---

## Quick Start / 快速开始

1. Drop this folder into Claude Code / 将此文件夹拖入 Claude Code
2. Say "Help me solve this math modeling problem" (attach the problem PDF) / 说"帮我做这道数模题"
3. Claude follows the 10-stage SOP naturally through conversation / 按对话自然推进 10 个阶段
4. Interrupt, backtrack, discuss at any time — conversation IS the pipeline / 可随时打断、回溯、讨论

When you start a new problem, Claude creates the full session directory upfront:

```bash
mkdir -p sessions/题目名称/{data,notes,solvers,verifications,figures,paper}
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
| Antipattern Library / 反模式库 | `rules/antipatterns.md` | 39 common errors, graded by severity |
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
├── SOP.md                 # 10-stage SOP with verification protocols
├── README.md              # This file
│
├── algorithms/            # Algorithm knowledge base
│   ├── index.json         #   9 domains / 27 subdomains / 74 methods
│   ├── code_index.json    #   MATLAB → Python mapping
│   ├── code/              #   Historical contest code (MATLAB/Jupyter)
│   └── 01~07-*.md         #   Detailed algorithm docs with cross-references
│
├── roles/                 # Role documents (self-evolving)
│   ├── 建模手.md           #   Modeler workflow (~560 lines)
│   ├── 编程手.md           #   Coder workflow (~800 lines)
│   ├── 论文手.md           #   Writer workflow (~1150 lines, includes de-AI guide)
│   └── 路径说明.md         #   Path reference table
│
├── rules/                 # Guardrails
│   └── antipatterns.md    #   39 antipatterns, 4 categories
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
│
├── references/            # Reference materials (gitignored, downloaded from Releases)
│   ├── papers/            #   ~1489 PDFs in 6 categories / 28 subcategories
│   ├── papers_metadata.json  # 1330 papers indexed
│   ├── empirical_baselines.json  # 10-dim scoring baselines
│   └── 官方资料/           #   Official review criteria + experience sharing
│
├── sessions/              # Contest archives (gitignored)
│   └── <problem-name>/    #   One directory per problem
│       ├── data/          #   Raw data files
│       ├── notes/         #   Analysis documents
│       ├── solvers/       #   Solution code
│       ├── verifications/ #   Verification scripts
│       ├── figures/       #   Generated figures
│       ├── paper/         #   main.tex → main.pdf
│       └── eval_report.json  # Auto-saved scorer output
│
└── releases_new/          # GitHub Releases packages (gitignored)
```

---

## Evolution Engine Details / 进化引擎详解

The evolution cycle is split into two parts: **mechanical work** (Python) and **insight work** (Claude Code).

### Mechanical Work (Python — `evolver.py`)

| # | Mechanism / 机制 | Action / 动作 |
|---|-----------------|--------------|
| 1 | Update / 更新 | Update verified algorithms table in `roles/建模手.md` |
| 2 | Mark / 标记 | Tag verified algorithms in `algorithms/*.md` |
| 3 | Dynamic Graph / 动态图谱 | Append usage record `{date, session, type, score}` to `index.json` evolved_status array |
| 4 | Analyze / 分析 | Produce structural score analysis (weak/strong areas, writing anchors) |

### Insight Work (Claude Code)

读 evolver 的 `analysis` JSON → 读 session 代码/笔记/论文 → 在 role 子锚点写 100-200 字经验总结

### Dual Baseline Scoring (scorer.py)

每个维度同时输出两个百分位对比：
- **vs_paper_pct**: vs 319 篇获奖论文统计基线（固定）
- **vs_self_pct**: vs 自身同类型历史 session（动态积累）

baselines.json 含 `usage_rules` 规定评分后的决策分支：退步→写原因、弱项→读论文手章节做改进、超p75→记成功模式。

### Algorithm Selection Constraints (index.json)

`selection_rules` 规定算法选择流程：优先 evolved_status 不为空 → 最高分 → 最近使用。无已验证时标"需复核"。选定后必须通读对应 .md 文档。

### Structured Sub-Anchors (40 total)

**Modeler (9):** MODEL_OPTIMIZATION through MODEL_COMPETITION_DIFFERENCES
**Writer (17):** WRITING_TITLE through WRITING_LESSONS
**Coder (7):** CODE_OPTIMIZATION through CODE_ML
**Plus:** EXPERIENCES, LESSONS, VERIFIED_ALGORITHMS, CODE_TEMPLATES, PITFALLS, PAPER_TEMPLATES, EXPRESSIONS

### Query Commands

| Command / 命令 | Purpose / 用途 |
|---------------|---------------|
| `evolver.py suggest --problem-type X` | Returns best strategy + weak dimensions + failure patterns |
| `evolver.py gaps` | Lists uncovered problem types + unverified algorithms |
| `evolver.py sessions` | Lists all past sessions |
| `evolver.py evolve --session "X" --from-scorer` | Run mechanical evolution work |

## Scorer Details / 评分引擎详解

The scorer (`tools/evolution/scorer.py`) evaluates the paper on 10 dimensions:

| Dimension / 维度 | Weight / 权重 | What it checks / 检查内容 |
|-----------------|-------------|-------------------------|
| `abstract_quality` | 0.12 | Abstract length + 5-segment structure + quantitative results |
| `structure_completeness` | 0.10 | Section count + assumptions list + notation table |
| `visual_richness` | 0.10 | Figure count + table count |
| `verification_complete` | 0.20 | Solver-verify pair ratio + indicator diversity (assert/rmse/r2 etc.) |
| `formula_rigor` | 0.10 | Equation count + LaTeX math usage |
| `sensitivity_depth` | 0.10 | Sensitivity analysis section + perturbation range |
| `model_diversity` | 0.08 | Number of distinct model types used |
| `academic_norm` | 0.08 | Reference count + citation format |
| `code_documentation` | 0.06 | README presence + code comments + data checks |
| `ai_flavor_penalty` | 0.06 | AI-writing markers detected (40+ patterns, lower=better) |

Each dimension scored against dual baselines:
- **vs_paper_pct**: vs 319 awarded papers (static, from batch PDF extraction)
- **vs_self_pct**: vs own history of same problem type (dynamic, accumulates)

Problem-type-specific weights adjust scoring. baselines.json `usage_rules` govern post-scoring decisions.

Three speed modes:
- `--mode fast` — Quick scan (no PDF)
- `--mode standard` — Full scan (default)
- `--mode championship` — Full scan + 4-layer feedback

---

## AI Flavor Detection / AI味检测

The scorer detects **40+ AI-writing patterns** grouped by category:

| Category / 类别 | Example Patterns / 示例 |
|----------------|------------------------|
| Over-emphasis on importance / 过度强调重要性 | 标志着, 关键作用, 为...奠定基础 |
| Promotional language / 宣传性语言 | 突破性的, 丰富的理论内涵, 强大的实践价值 |
| Vague attribution / 模糊归因 | 专家认为, 观察者指出 |
| Formulaic challenges / 公式化挑战 | 尽管...面临几个挑战, 挑战与展望 |
| High-frequency AI words / 高频AI词汇 | 此外, 深入探讨, 充分展示, 不仅...而且 |
| Generic positive conclusions / 通用积极结论 | 前景光明, 令人振奋, 迈向卓越 |

---

## License / 许可

- Algorithm docs, LaTeX templates, role documents, and other text content: **CC BY-NC-SA 4.0**
- Code tools (`tools/` directory): **MIT**
- Paper PDFs (`references/` directory): Copyright belongs to original authors. For educational reference only.

---

## Acknowledgments / 致谢

Inspired by the following open-source projects:

- [LLM-MM-Agent](https://github.com/usail-hkust/LLM-MM-Agent) (NeurIPS 2025) — HMML 3-level algorithm knowledge base design
- [MetaGPT](https://github.com/geekan/MetaGPT) — Multi-role collaboration and SOP-as-Code philosophy
- [LangGraph](https://github.com/langchain-ai/langgraph) — Stateful graph workflow patterns
- [AutoGen](https://github.com/microsoft/autogen) — Event-driven agent architecture and Agent-as-Tool pattern
- [SuperAGI](https://github.com/TransformerOptimus/SuperAGI) — Vector database integration and performance telemetry
- [mathmodel-skill](https://github.com/handsomeZR-netizen/mathmodel-skill) — 91-paper scoring baselines and antipatterns
- [AutoMCM-Pro](https://github.com/RealSeaberry/AutoMCM-Pro) — Mandatory self-verification protocol
- [dick20/MCM-ICM](https://github.com/dick20/MCM-ICM) — 2004-2025 MCM/ICM Outstanding papers
- [personqianduixue/Math_Model](https://github.com/personqianduixue/Math_Model) — Math modeling resource library
- [haitanghuaweimianTom/math-model](https://github.com/haitanghuaweimianTom/math-model) — CUMCM/GMCM papers by model type
- [HuangCongQing/Algorithms_MathModels](https://github.com/HuangCongQing/Algorithms_MathModels) — Algorithm MATLAB implementations
- [hacheyz/PMMAA](https://github.com/hacheyz/PMMAA) — Python mathematical modeling algorithms
- [Giyn/MathematicalModelingAlgorithm](https://github.com/Giyn/MathematicalModelingAlgorithm) — Importable Python algorithm modules
