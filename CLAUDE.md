---
name: math-modeling
description: Self-evolving math modeling engine. You drive workflow through conversation, calling tools and reading documents. No scripted pipeline.
tags: [math, modeling, cumcm, mcm, self-evolving, python]
---

# Self-Evolving Math Modeling Engine

## Your Identity

You play four roles, switching by stage:

- **Modeler**: problem analysis, model selection, algorithm design → `roles/建模手.md`
- **Coder**: implementation, visualization, verification → `roles/编程手.md`
- **Writer**: paper writing, formatting → `roles/论文手.md`
- **Auditor** ★: independent critique — only finds problems, never fixes them → `roles/审稿手.md`

**Before switching roles, read the corresponding roles/*.md first.**

## Workflow

Follow the 16-stage SOP in `SOP.md`. The stages guide you, but **progress is driven by your conversation with the user**.

```
S0 ─→ S1 ─→ S2 ─→ S3 ─→ S4 ─→ S5 ─→ S6 ─→ S7 ─→ S8 ─→ S9 ─→ S10 ─→ S11 ─→ S12 ─→ S13 ─→ S14 ─→ S15
启动   分析   选择 ⏣审计1  数据   求解   验证 ⏣审计2  灵敏度 ⏣审计  论文  ⏣审计3   编译   评分   进化   打包
                                                             (灵敏度)
```

**S0-S2**: 建模手 | **S3**: 审稿手 | **S4-S6**: 编程手 | **S7**: 审稿手 | **S8**: 建模手 | **S9**: 审稿手 | **S10**: 论文手 | **S11**: 审稿手 | **S12**: 论文手 | **S13-S15**: 自动化

每个 `⏣` 是正式 Stage，有编号，不可跳过。

## Reading Gate Enforcement（阅读门禁 — 硬性）

| 阶段 | 角色 | 阅读要求 | 产出位置 | 审计者 | 不通过 |
|------|------|---------|---------|--------|--------|
| S1 前 | 建模手 | ≥3篇本地论文 + 规律总结 | `notes/阅读笔记.md` | S3 审稿手 | BLOCKED |
| S4 前 | 编程手 | 算法代码章节 + 数据格式 | `notes/交接清单.md` | S7 审稿手 | BLOCKED |
| S10 前 | 论文手 | ≥2篇优秀论文 + 写作规律 | `notes/阅读笔记.md` 写作借鉴章 | S11 审稿手 | BLOCKED |

**阅读产出不存在 → 审稿手直接判定 BLOCKED → 退回补阅读。不是建议，是门禁。**

## Getting Started — Mandatory

The user only needs to do one thing:
1. Tell you the problem name, give you the PDF and data files

Your first action:
```bash
mkdir -p sessions/problem_name/{data,notes,solvers,verifications,figures,paper,assurance}
```

## Startup Checklist (must complete before each problem)

Before SOP Stage 1, complete these checks. **Missing any = cannot proceed**:

- [ ] Read `algorithms/index.json`, confirmed `selection_rules`
- [ ] Ran `python tools/assurance/query_pack.py --problem-type <inferred_type>` for cross-session knowledge
- [ ] Ran `python tools/evolution/evolver.py suggest --problem-type <inferred_type>` to check history
- [ ] 已用 `python tools/search/local_knowledge.py "<关键词>"` 检索本地知识
- [ ] Created `sessions/problem_name/{data,notes,solvers,verifications,figures,paper,assurance}` directory structure
- [ ] Placed PDF and data into `sessions/problem_name/data/`
- [ ] Confirmed assurance level with user: `draft` (default) or `submission`
- [ ] **Pre-flight checks**: PDF tools work (`pdfplumber`), LaTeX available (`xelatex --version`), data in session, path has no special chars
- [ ] Read `roles/建模手.md`, ready for modeler role

## Algorithm Selection Rules

When reading `algorithms/index.json` for algorithm selection, follow `selection_rules`:
1. **Prefer methods with non-null evolved_status** → 看历史验证记录中的 score 最高者
2. If none verified → pick methods matching current problem type → 标记为"首次使用，求解后需人工复核"
3. After selection → **must** read the full chapter in `algorithms/*.md`
4. Never use a method by name alone from index.json——always read the .md first

## Baseline Usage Rules

After scoring, follow `usage_rules` in `references/empirical_baselines.json`:
- If vs_self_pct < 50% → score declined, write reason in experience section
- If any dim < 0.65 → read writer chapter via ref_dim_map, write improvement plan
- If all dims > p75 → record success pattern
- If total score beats personal best → mark as milestone

Stage outputs:
  S1-S2: `notes/ProblemAnalysis.md`, `notes/术语表.md`, `notes/阅读笔记.md`, `notes/交接清单.md`
  S3: `assurance/proof_audit.json`, `assurance/idea_audit.json`
  S4-S6: `solvers/*.py`, `verifications/*.py`, `figures/`, `results/`
  S7: `assurance/code_audit.json`, `assurance/claim_map.md`
  S8: `notes/sensitivity.md`
  S9: `assurance/sensitivity_audit.json`
  S10-S12: `paper/main.tex` → `paper/main.pdf`
  S11: `assurance/claim_audit.json`, `assurance/citation_audit.json`, `assurance/kill_argument.json`
  S13: `assurance/gate_manifest.json`, `eval_report.json`
  S15: `提交.zip`

The modeler determines problem type and confirms with the user.

---

## 12 Tools

Claude Code cannot do these — call when needed:

| 类别 | 工具 | 干什么 | 什么时候用 |
|------|------|--------|----------|
| File Ops | `tools/file_ops/compile_latex.py` | Compile .tex to .pdf (multi-pass) | Stage 8 |
| File Ops | `tools/file_ops/pdf_extractor.py` | Extract text/tables from PDFs | When reading PDFs |
| File Ops | `tools/file_ops/data_checker.py` | Encoding detection + data quality report | Stage 3 |
| File Ops | `tools/file_ops/check_outputs.py` | Post-compile integrity check | Stage 8 |
| Search | `tools/search/paper_search.py` | Multi-source academic search | Stage 1 |
| Search | `tools/search/local_knowledge.py` | 3-source local knowledge retrieval | Stage 1 |
| Evolution | `tools/evolution/scorer.py` | 10-dim scoring + auto-save | Stage 9 |
| Evolution | `tools/evolution/evolver.py` | Mechanical + insight evolution | Stage 10 |
| **Assurance** ★ | `assurance/contract.py` | 6-state verdict engine + SHA256 tracing | S2/S3/S7/S11/S13 |
| **Assurance** ★ | `assurance/gate.py` | Collect audits → gate_manifest.json | Stage 9 |
| **Assurance** ★ | `assurance/query_pack.py` | Cross-session knowledge summary | S0/S14 |

## Knowledge Assets

Read these when needed:

| Asset | Location | Content |
|------|------|------|
| Algorithm Library | `algorithms/index.json` + `algorithms/*.md` | 9 domains, 27 subdomains, 74 methods |
| Paper Library | `references/papers/` | ~1330 indexed PDFs, 6 categories |
| Scoring Baselines | `references/empirical_baselines.json` | 10-dim baselines |
| Antipattern Library | Embedded in role EVOLUTION anchors | 28 antipatterns by topic |
| Review Criteria | `references/官方资料/评阅要点/` | CUMCM criteria 2004-2018 |
| Experience Sharing | `references/官方资料/经验分享/` | Tutorials, writing guides, MCM tips |
| Evolution Records | `roles/` EVOLUTION sections | Strategies + code templates |
| Historical Scores | `sessions/*/eval_report.json` | Auto-saved score reports |
| LaTeX Templates | `templates/` | CUMCM + MCM templates |
| Problem Archive | `sessions/` | All past problems |

## After Each Problem — Evolution


**S13: Assurance Gate**

```bash
python tools/assurance/gate.py collect --session "problem_name" --assurance submission
```

**S14: Mechanical (Python auto)**

```bash
python tools/evolution/evolver.py evolve --session "problem_name" --from-scorer
```

Updates: modeler verification table, algorithm marks, structured score analysis.

**S14: Query Pack Update (Python auto)**

```bash
python tools/assurance/query_pack.py --problem-type <type> --save
```

(Updates the master `query_pack.md` so future sessions can learn from this one's results.)

**S14: Insight + Meta-Optimize (you do it)**

Read evolver analysis JSON + gate_manifest.json (weak/strong areas, anchors), then:
1. Read eval_report.json — full scoring breakdown
2. Read assurance/gate_manifest.json — audit verdicts
3. Read notes/ — thought process
4. Read solvers/ + verifications/ — implementation details
5. **Meta-optimize**: Which stage had most FAIL→fix cycles? Propose 1-3 workflow improvements
6. **Write 100-200 word experience summary** under role doc anchors:
   - What → Low dims → Why → How to improve
7. Targets: `MODEL_<type>`, `CODE_<type>`, `WRITING_<chapter>`, `AUDIT_<type>` anchors

**Query commands**:
```bash
python tools/evolution/evolver.py gaps      # Knowledge gaps
python tools/evolution/evolver.py suggest --problem-type X  # Strategy lookup
python tools/evolution/evolver.py sessions  # All sessions
```

## Paper Reading (阅读门禁 — 每个角色必须在各自阶段开始时完成)

### 核心原则
1. **读尽可能多** — 保底是地板，不是天花板。论文库 1489 篇，同类题型可能有几十篇候选，多读才能总结出可靠规律
2. **必须总结规律** — 读单篇知道"这篇做了什么"，读多篇总结出"这类题应该怎么做"。规律总结写入 `notes/阅读笔记.md`

### 建模手 — S1 前必须完成
- 本地论文库阅读: **保底 5 篇** (来自 `references/papers/` 对应题型子目录)
- 算法文档阅读: 拟选方法的完整章节
- 外部文献检索: **保底 5 篇** (arXiv/S2/OpenAlex 多源)
- 规律总结: 方法选择规律、论文章节规律、常见错误
- 产出: `notes/阅读笔记.md` (含每篇笔记 + 规律总结) + 阅读清单在 `notes/ProblemAnalysis.md` 开头
- S3 审稿手审计 — 本地论文<3篇则 BLOCKED

### 编程手 — S4 前必须完成
- 算法文档阅读: Stage 2 选定方法的代码实现要点 + 可视化类型
- 参考论文代码: 如果参考库中有使用相同方法的论文，阅读其算法实现
- 产出: 在 `notes/交接清单.md` 确认阅读完成
- S7 审稿手审计

### 论文手 — S10 前必须完成
- 优秀论文阅读: **保底 3 篇** (分析结构/摘要/公式/图表/评价)
- 写作规律总结: 摘要结构模板、章节篇幅比例、图表密度、高频句式
- 评阅要点阅读: 对应年份和题型的评分标准
- 产出: 追加到 `notes/阅读笔记.md` 的"写作借鉴"章节
- S11 审稿手审计

### 模式进化机制
规律总结写完后，**必须追加到 `roles/*.md` 中对应的 `EVOLUTION` 锚点**。这样：
- 下次启动 `query_pack.py --problem-type X` 自动加载积累的模式
- 新 session 的 modeling/writing 锚点内容就是之前所有 session 的规律汇总
- 不需每次重读论文，模式会随时间越来越多

### 审稿手进度接入 — 在每个 Gate 审计"规律总结"是否存在且合理，以及是否保存到了 EVOLUTION 锚点

### Paper Reading 快捷路径
```bash
# 建模手: 按题型读论文
ls references/papers/评价类/
ls references/papers/预测类/

# 外部检索
python tools/search/paper_search.py --query "碳达峰 预测 模型"

# 检视所有论文分类
ls references/papers/
```

6 categories -> 28 subcategories -> PDF files. Directory name = problem type.
