# Mathematical Modeling Standard Operating Procedure (SOP)

> This is Claude Code's behavioral guide for mathematical modeling tasks.
> 12 stages + ARIS assurance framework. Progress is driven by your conversation with the user.

---

## Four-Role Architecture

| # | Role | File | Scope |
|---|------|------|-------|
| 1 | 建模手 | `roles/建模手.md` | Problem analysis, model selection, literature, algorithm design |
| 2 | 编程手 | `roles/编程手.md` | Code implementation, visualization, results output |
| 3 | 论文手 | `roles/论文手.md` | Paper writing, formatting, slides/poster |
| 4 | **审稿手** ★ | `roles/审稿手.md` | Independent audit — critique only, never fix |

**审稿手介入点**: After Stage 2 (model audit), Stage 5 (implementation audit), Stage 7 (paper audit).

---

## 12-Stage Workflow

```
Stage 0 ─→ Stage 1 ─→ Stage 2 ─→ [审稿手①] ─→ Stage 3 ─→ Stage 4
          问题分析    模型选择     模型审计        数据预处理   模型求解

    ─→ Stage 5 ─→ [审稿手②] ─→ Stage 6 ─→ [审稿手] ─→ Stage 7 ─→ [审稿手③]
       模型验证    实现审计      灵敏度分析   灵敏度审计    论文撰写     论文审计

    ─→ Stage 8 ─→ Stage 9 ─→ Stage 10 ─→ Stage 11
       构建/展示   门禁评分     进化沉淀      打包提交
```

---

## Stage 0: Startup & Assurance Setup

Lead: **建模手**

**Mandatory**:
1. Session directory created: `sessions/题目名称/{data,notes,solvers,verifications,figures,paper,assurance}`
2. Read `algorithms/index.json`, confirm `selection_rules`
3. Run `evolver.py suggest --problem-type <inferred_type>` to check history
4. **Query pack**: Run `python tools/assurance/query_pack.py --problem-type <type>` to read cross-session knowledge (EVOLUTION anchors + past eval reports)
5. **Assurance level**: Confirm with user — `draft` (default, audits advisory) or `submission` (audits gated)
6. Run `python tools/search/local_knowledge.py "<关键词>"` for local knowledge
7. Read `roles/建模手.md`, ready for modeler role

**Output**: Session dir created, query pack loaded, assurance level written to `sessions/{name}/assurance/level.txt`

---

## Stage 1: Problem Analysis

Lead: **建模手**

**Mandatory**:
1. Read the problem: extract text from PDF or user description
2. Check data: analyze files in `data/`
3. Determine problem type: optimization/prediction/evaluation/classification/ODE/graph/hybrid
4. **Research-lit** (ARIS Module 1.1): Multi-source literature search
   - arXiv API → Semantic Scholar → OpenAlex
   - De-duplicate results, write to literature section in notes/
5. **Idea-creator + Novelty-check** (ARIS Module 1.2): Generate candidate model approaches
   - Generate 3-5 model options
   - Verify novelty/appropriateness against literature
   - Rank by: fit → data compatibility → interpretability → computational cost
   - Write decision rationale to `notes/ProblemAnalysis.md`
6. Follow 3 principles: prefer simple over complex
7. Design algorithm: solving steps, flowchart, key parameters
8. Build glossary: unified definitions for all terms and symbols

**Output**: `notes/ProblemAnalysis.md` (complete analysis with literature references and model selection rationale)

**Discuss with user**: Is the model reasonable? Are the literature references adequate?

---

## Stage 2: Model Selection & Scaffolding

Lead: **建模手**

**Mandatory**:
1. Confirm model design with the user
2. **Proof-checker** (ARIS Module 1.3): Verify formula derivations
   - AHP: consistency ratio CR < 0.1
   - Optimization: KKT conditions satisfied
   - Iterative algorithms: convergence proof
   - All formulas: every symbol defined in glossary
3. Build scaffolding for each subproblem
4. Determine data requirements

**Handoff**: Write to `notes/交接清单.md`:
```markdown
| 项目 | 内容 |
|------|------|
| Problem # | 1/2/3/N |
| Algorithm | Name + why chosen |
| Input format | Columns, types, preprocessing |
| Output format | Solutions/predictions/scores/labels |
| Key params | Meaning and recommended range |
| Verification | Which model type checks apply |
| Visualization | Chart types needed |
```

---

## [审稿手 Gate 1] — Model Audit

Lead: **审稿手** (Switch role — read `roles/审稿手.md`)

**Audit Content**:
- **Proof-checker audit**: Verify all formulas have defined symbols, derivation chain complete, AHP/KKT checks pass
- **Idea audit**: At least 2 approaches compared, each with literature support, selection rationale sufficient

**Output**:
- `sessions/{name}/assurance/proof_audit.json`
- `sessions/{name}/assurance/idea_audit.json`

**Gate rule**: At `assurance: submission`, FAIL → must fix before proceeding. At `assurance: draft`, WARN/FAIL displayed to user.

**Discuss with user**: Audit results. Proceed or revise?

---

## Stage 3: Data Preprocessing

Lead: **编程手** (Switch role — read `roles/编程手.md`)

**Mandatory**:
1. Read raw data — `df.info()` `df.describe()`
2. Model-specific preprocessing (not generic):
   - Optimization: standardize constraint format, unify units
   - Regression/ML: handle missing values, encode categoricals, check multicollinearity
   - Prediction: check stationarity, differencing
   - Evaluation: normalize/reverse indicators
   - Network: build adjacency/distance matrices
3. Verify format matches Stage 2 scaffolding
4. **Never modify `data/` original files**. Preprocessing logic in `solvers/` code

---

## Stage 4: Model Solving

Lead: **编程手**

**Mandatory**:
1. Read `notes/ProblemAnalysis.md` and scaffolding
2. Implement algorithm in `solvers/problem{n}.py`
3. **Must execute code** after writing; fix errors in-place
4. **Prohibited**: Creating simplified/alternative versions
5. Generate visualizations → `figures/` as SVG (vector format)

**Output**: `solvers/problem{n}.py` + `figures/` + `results/`

**Discuss with user**: Are results reasonable? Anomalies?

---

## Stage 5: Model Verification

Lead: **编程手**

**Hard gate — must pass before entering paper stage.**

1. Write `verifications/verify_problem{n}.py` for each solver
2. Run verification scripts directly
3. **Code-audit** (ARIS Module 2.1): Check code integrity
   - Constraint feasibility: every constraint actually satisfied
   - Solver cross-validation: if multiple solvers, results consistent
   - Dead code detection: any defined-but-never-called functions
   - Result file provenance: results/ files actually generated by solver
4. **Result-to-Claim** (ARIS Module 2.2): Map results → claims
   - For each problem: what does the result support? What doesn't it?
   - Build claim-support table
5. Record trial log to `notes/trial_log.md`

**Verification checklist by model type**:

| Model Type | Checks |
|-----------|--------|
| Optimization | [V-OPT-1] Constraint feasibility, [V-OPT-2] Cross-verification, [V-OPT-3] Perturbation test |
| Regression/ML | [V-REG-1] Shapiro-Wilk (p>0.05), [V-REG-2] Breusch-Pagan, [V-REG-3] DW (1.5-2.5), [V-REG-4] 5-fold CV |
| ODE/Dynamics | [V-ODE-1] Conservation, [V-ODE-2] Boundary conditions, [V-ODE-3] Grid convergence |
| Network/Graph | [V-GRF-1] Path legality, [V-GRF-2] Flow conservation, [V-GRF-3] Small-scale brute force |

**Verification quality**:
- Each verify script must have ≥1 concrete numerical threshold (e.g. `r2_score > 0.85`)
- Must print specific values, not just PASS/FAIL

---

## [审稿手 Gate 2] — Implementation Audit

Lead: **审稿手** (Read `roles/审稿手.md`)

**Audit Content**:
- **Code-audit**: Constraint satisfaction, solver consistency, dead code, result provenance
- **Result-to-Claim**: Claim support mapping — what's supported, what's not, what's missing

**Output**:
- `sessions/{name}/assurance/code_audit.json`
- `sessions/{name}/assurance/claim_map.md` (coder drafts content, auditor reviews and validates)

**Gate rule**: Same as Gate 1. FAIL → fix before Stage 6.

---

## Stage 6: Sensitivity Analysis

Lead: **建模手**

**Mandatory**:
1. Select ≥3 key parameters, perturb ±20%
2. Quantify output change magnitude
3. Identify most sensitive parameter
4. Record to `notes/sensitivity.md`

**Handoff (→ Writer)**: Append to `notes/交接清单.md`:
```markdown
| 项目 | 内容 |
|------|------|
| 求解结果摘要 | Key values per problem |
| 图表清单 | figures/ file list with problem mapping |
| 验证通过证明 | Each verify script PASS/FAIL status |
| 关键发现 | Important insights from data |
| 模型对比 | If multiple models used, which is best and why |
```

---

## [审稿手] Sensitivity Check

Lead: **审稿手** (Read `roles/审稿手.md`)

**Sensitivity-audit** (ARIS Module 2.3): Run AFTER Stage 6 produces `notes/sensitivity.md`:

| # | Check | Standard |
|---|-------|---------|
| 1 | Key parameters | ≥3 perturbed |
| 2 | Perturbation range | ±20% baseline |
| 3 | Quantitative output | Must have % values, "significant change" not acceptable |
| 4 | Most sensitive parameter | Identified and discussed |
| 5 | Multi-parameter analysis | Bonus, not required |

**Output**: `sessions/{name}/assurance/sensitivity_audit.json`

**Gate rule**: FAIL → fix sensitivity analysis before Stage 7.

---

## Stage 7: Paper Writing

Lead: **论文手** (Read `roles/论文手.md`)

**Mandatory**:
1. **Paper-plan** (ARIS Module 3.1): Build claim-evidence matrix + section topology + figure plan BEFORE writing
2. Copy LaTeX template (`templates/latex_template.tex` or `mcm_template.tex` → `paper/main.tex`)
3. **Figures** (ARIS Module 4.1-4.2):
   - `figure-spec`: Deterministic JSON→SVG for algorithm flowcharts/architecture diagrams
   - `paper-illustration`: AI-generated method concept illustrations
   - Data plots: by coder as SVG
4. Fill chapters: Abstract → Restatement → Assumptions + Notation → Model → Solution → Results → Sensitivity → Evaluation → References
5. **Style-ref** (ARIS Module 5.4, optional): If user specifies a reference paper, mimic structural style only (section order, formula density, sentence cadence) — never copy prose or claims
6. De-AI-flavor (see `roles/论文手.md` 40+ detection markers)
7. Every figure ≥100 word analysis

**Discuss**: Show each chapter for review.

---

## [审稿手 Gate 3] — Paper Audit

Lead: **审稿手** (Read `roles/审稿手.md`)

**Audit Content**:
- **Paper-claim-audit** (ARIS Module 5.1): Zero-context verification — every number in paper vs raw result files. Rounding errors, best-seed cherry-picking, range overclaims all exposed.
- **Citation-audit** (ARIS Module 5.2): Three-layer verification (arXiv→CrossRef→S2) for each reference: existence, metadata correctness, context appropriateness.
- **Kill-argument** (ARIS Module 5.3): Dual-thread adversarial review — one thread attacks the model evaluation section, the other adjudicates point by point.

**Output**:
- `sessions/{name}/assurance/claim_audit.json`
- `sessions/{name}/assurance/citation_audit.json`
- `sessions/{name}/assurance/kill_argument.json`

**Gate rule**: FAIL → fix and re-audit before Stage 8.

---

## Stage 8: Final Compilation & Improvement

Lead: **论文手**

**Mandatory**:
1. **Improvement-loop** (ARIS Module 6.1): 3-round review
   - Round 1: Structural review (logic flow, section allocation)
   - Round 2: Number review (cross-reference with claim_audit)
   - Round 3: AI-flavor review (scan for 40+ markers)
   - Each round produces suggested changes (user decides which to accept)
2. Compile: `python tools/file_ops/compile_latex.py compile --mode cumcm`
3. Check output: page count (8-25), no compile errors, figure/table numbering continuous
4. **Slides** (ARIS Module 7.1, optional): Beamer LaTeX + PPTX + speaker notes
5. **Poster** (ARIS Module 7.2, optional): A0/A1 PDF + editable PPTX + SVG
6. **Slides-polish** (ARIS Module 7.3): Per-page layout review (only when slides generated)

---

## Stage 9: Assurance Gate & Scoring

Lead: — (Automated + user review)

**Mandatory**:
1. **Assurance Gate** (ARIS Module 6.2):
   ```bash
   python tools/assurance/gate.py collect --session "题目名称" --assurance submission
   ```
   This collects all audit artifacts, validates against contract schema, checks for stale inputs, and produces `sessions/{name}/assurance/gate_manifest.json`.

2. Review gate_manifest.json with user. Overall verdict: PASS/WARN/FAIL.

3. **Scorer** (backup baseline comparison):
   ```bash
   python tools/evolution/scorer.py --session "题目名称" --mode standard
   ```
   10-dim empirical baseline comparison. Saved to `eval_report.json`.

**Discuss with user**: Gate verdict, scorer report, weak areas.

---

## Stage 10: Evolution & Knowledge Archive

Lead: — (Automated + insight)

**Mechanical (Python auto)**:
```bash
python tools/evolution/evolver.py evolve --session "题目名称" --from-scorer
```

**Query Pack update** (ARIS Module 7.5):
```bash
python tools/assurance/query_pack.py --problem-type <type> --save
```

**Meta-optimize** (ARIS Module 7.4): Analyze this run:
- Which stage consumed most iterations?
- Which audit had the most FAIL→fix cycles?
- Propose 1-3 workflow improvements → update role EVOLUTION anchors

**Insight (Claude Code完成)**:
1. Read `eval_report.json` — full scoring breakdown
2. Read `notes/` — thought process
3. Read `solvers/` + `verifications/` — implementation details
4. Read `assurance/gate_manifest.json` — audit results
5. **Write 100-200 word experience summary** under role doc EVOLUTION anchors

---

## Stage 11: Packaging & Submission

1. Read official submission requirements
2. Verify all deliverables: `paper/main.pdf`, `solvers/`, `figures/`, supporting materials
3. Package:
   ```bash
   cd sessions/题目名称/
   zip -r 提交.zip paper/main.pdf solvers/ figures/ 支撑材料/
   ```
4. Final file list confirmation with user

---

## Model Selection: Three Principles

1. Use elementary methods when possible — skip advanced when simple works
2. Use simple methods when possible — skip complex when simple works
3. Use methods understood by more people — skip niche methods understood by few

---

## Absolute Prohibitions

1. Unverified data in paper
2. Silent skip on verification failure
3. Claim "verified" without running code
4. Modify original files in `data/`
5. Create simplified/alternative code versions
6. Modify LaTeX template formatting
7. Post figures without explanation (<100 words each)
8. **Audit FAIL at `submission` level without fixing**

---

## Tool Logging

Append a JSON line to `notes/tool_log.md` after each critical tool call:

```json
{"time": "2026-05-18 14:30", "tool": "compile_latex.py", "session": "xxx", "exit": 0}
```

Key tools to log: `compile_latex.py`, `scorer.py`, `evolver.py`, `gate.py`, `query_pack.py`.

Failed tool processing:
1. Check `tool_log.md` for same-tool failure history
2. If same error → reuse previous fix
3. If new error → diagnose → fix → log
4. Same error ≥3 times → permanently fix root cause
