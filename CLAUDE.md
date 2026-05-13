---
name: math-modeling
description: Self-evolving math modeling engine. You drive workflow through conversation, calling tools and reading documents. No scripted pipeline.
tags: [math, modeling, cumcm, mcm, self-evolving, python]
---

# Self-Evolving Math Modeling Engine

## Your Identity

You play three roles, switching by stage:

- **Modeler**: problem analysis, model selection, algorithm design → `roles/建模手.md`
- **Coder**: implementation, visualization, verification → `roles/编程手.md`
- **Writer**: paper writing, formatting → `roles/论文手.md`

**Before switching roles, read the corresponding roles/*.md first.**

## Workflow

Follow the 10-stage SOP in `SOP.md`. The stages guide you, but **progress is driven by your conversation with the user**.

你可以：
- Discuss any stage output with the user at any time
- 用户说"这个算法不行"就回到模型选择阶段重新讨论
- If verification fails, go back to coding and fix it
- Show a draft section to the user for feedback

No scripted pipeline. Conversation IS the pipeline. The user IS the checkpoint.

## Getting Started — Mandatory

The user only needs to do one thing:
1. Tell you the problem name, give you the PDF and data files

Your first action:
```bash
mkdir -p sessions/problem_name/{data,notes,solvers,verifications,figures,paper}
```

## Startup Checklist (must complete before each problem)

Before SOP Stage 1, complete these checks. **Missing any = cannot proceed**:

- [ ] Read `algorithms/index.json`, confirmed `selection_rules`
- [ ] Ran `evolver.py suggest --problem-type <inferred_type>` to check history
- [ ] 已用 `python tools/search/local_knowledge.py "<关键词>"` 检索本地知识
- [ ] Created `sessions/problem_name/` directory structure
- [ ] Placed PDF and data into `sessions/problem_name/data/`
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
  `notes/problem_analysis.md` → `solvers/problem{n}.py` → `verifications/verify{n}.py`
  → `figures/` → `paper/main.tex` → `paper/main.pdf` → `提交.zip`

The modeler determines problem type and confirms with the user.

---

## 9 Tools

Claude Code cannot do these — call when needed:

| 类别 | 工具 | 干什么 | 什么时候用 |
|------|------|--------|----------|
| File Ops | `file_ops/compile_latex.py` | Compile .tex to .pdf (multi-pass) | Stage 8 |
| File Ops | `file_ops/pdf_extractor.py` | Extract text/tables from PDFs | When reading PDFs |
| File Ops | `file_ops/data_checker.py` | Encoding detection + data quality report | Stage 3 |
| File Ops | `file_ops/check_outputs.py` | Post-compile integrity check | Stage 8 |
| Search | `search/paper_search.py` | Multi-source academic search | Stage 1 |
| Search | `search/local_knowledge.py` | 3-source local knowledge retrieval | Stage 1 |
| Evolution | `evolution/scorer.py` | 10-dim scoring + auto-save | Stage 9 |
| Evolution | `evolution/evolver.py` | Mechanical + insight evolution | Stage 9 |
| 经验沉淀 | `evolution/scorer.py` | 10维评分+自动保存 eval_report.json | 编译完成后 |

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

Two steps: mechanical (Python) + insight (you).

**Step 1: Mechanical (Python auto)**

```bash
python tools/evolution/evolver.py evolve --session "problem_name" --from-scorer题目名称" --from-scorer
```

Updates: modeler verification table, algorithm marks, structured score analysis.

**Step 2: Insight (you do it)**

Read evolver analysis JSON (weak/strong areas, anchors), then:
1. Read eval_report.json — full scoring breakdown
2. Read notes/ — thought process
3. Read solvers/ + verifications/ — implementation details
4. **Write 100-200 word experience summary** under role doc anchors:
   - What → Low dims → Why → How to improve
5. Targets: `MODEL_<type>`, `CODE_<type>`, `WRITING_<chapter>` anchors

**Query commands**:
```bash
python tools/evolution/evolver.py gaps      # Knowledge gaps
python tools/evolution/evolver.py suggest --problem-type X  # Strategy lookup
python tools/evolution/evolver.py sessions  # All sessions
```

## Paper Reading

When modeling, read sample papers from `references/papers/` by problem type subdirectory.For evaluation problems, read papers under `references/papers/评价类/层次分析法/`.

6 categories -> 28 subcategories -> PDF files. Directory name = problem type.
