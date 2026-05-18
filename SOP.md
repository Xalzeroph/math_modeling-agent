# Mathematical Modeling Standard Operating Procedure (SOP)

> This is Claude Code's behavioral guide for mathematical modeling tasks.
> 16 stages, numbered. Audit gates are first-class stages. No stage can be skipped.

---

## Four-Role Architecture

| # | Role | File | Scope |
|---|------|------|-------|
| 1 | 建模手 | `roles/建模手.md` | Problem analysis, model selection, literature, algorithm design |
| 2 | 编程手 | `roles/编程手.md` | Code implementation, visualization, results output |
| 3 | 论文手 | `roles/论文手.md` | Paper writing, formatting, slides/poster |
| 4 | **审稿手** ★ | `roles/审稿手.md` | Independent audit — critique only, never fix |

---

## 16-Stage Workflow

```
S0 ─→ S1 ─→ S2 ─→ S3 ─→ S4 ─→ S5 ─→ S6 ─→ S7 ─→ S8 ─→ S9 ─→ S10 ─→ S11 ─→ S12 ─→ S13 ─→ S14 ─→ S15
启   问题   模型  ⏣审稿  数据   求解   验证  ⏣审稿  灵敏度 ⏣审稿  论文  ⏣审稿   编译   评分   进化   打包
动   分析   选择  ①模型  预处理           ②实现  分析   灵敏度 撰写  ③论文
```

每个 `⏣` 标记的 Stage 是审稿手关卡。和其他 Stage 一样有编号，不可跳过。

---

## Stage 0: Startup & Pre-flight

Lead: **建模手**

**Mandatory**:
1. Session directory created
2. Read `algorithms/index.json`, confirm `selection_rules`
3. Run `evolver.py suggest --problem-type <inferred_type>`
4. Run `python tools/assurance/query_pack.py --problem-type <type>`
5. Confirm assurance level with user: `draft` or `submission`
6. Run `python tools/search/local_knowledge.py "<关键词>"`
7. Read `roles/建模手.md`

**Pre-flight checks** (new):
- [ ] PDF tools: `python -c "import pdfplumber; print('OK')"` — confirm PDF extraction works
- [ ] LaTeX: `xelatex --version` — confirm compiler available
- [ ] Data files: placed in `sessions/{name}/data/`, not in subdirectories
- [ ] Path check: session path contains no spaces/special chars (avoid LaTeX include issues)
- [ ] Figure format check: confirm matplotlib backend supports target format; save as SVG, convert to PDF via svg2pdf.py before compile

**Output**: Session dir created, assurance level written to `assurance/level.txt`

---

## Stage 1: Problem Analysis

Lead: **建模手**

### ⏔ 阅读门禁（必须先完成）

产出文件：`notes/阅读笔记.md`（含规律总结）

**阅读要求**:
1. **本地论文库**: `references/papers/` 按题型子目录阅读 **保底 5 篇**（上不封顶）
   - 每篇记录：模型方法、关键结论、对本题的参考价值
   - **必须产出规律总结**: 方法选择规律、论文章节规律、常见错误
2. **算法文档**: `algorithms/` 拟选方法的完整章节（公式、代码、适用范围）
3. **外部文献**: `python tools/search/paper_search.py --query "<关键词>"` **保底 5 篇**
4. **输出阅读清单**: 在 `notes/ProblemAnalysis.md` 开头附阅读清单表

**门禁规则**: 以上全部完成后才可进入模型分析。S3 审稿手将检查阅读产出——不存在则 **BLOCKED**。

### Main

1. Read problem from PDF
2. Check data files in `data/`
3. Determine problem type
4. Research-lit: multi-source literature search
5. Idea-creator: 3-5 candidate approaches, rank by fit/data/compatibility/cost
6. Design algorithm steps, flowchart, key parameters
7. Build glossary

**Output**: `notes/ProblemAnalysis.md`

**Discuss with user**: Model and literature adequate?

---

## Stage 2: Model Selection & Scaffolding

Lead: **建模手**

**Mandatory**:
1. Confirm model design with user
2. **Proof-checker** (ARIS Module 1.3):
   - All formulas: every symbol defined in glossary
   - Derivation chain: no gaps ("obviously" must be verifiable)
   - AHP: CR < 0.1
   - Optimization: KKT conditions
   - Iterative: convergence proof
   - **Independent variable check (new)**: verify no predictor is an algebraic transformation of the target (e.g. using CO2/GDP to predict CO2 creates circular identity)
3. Build scaffolding per subproblem
4. Determine data requirements

**Handoff** → `notes/交接清单.md`:

| 项目 | 内容 |
|------|------|
| Problem # | 1/2/3/N |
| Algorithm | Name + why chosen |
| Input format | Columns, types, preprocessing |
| Output format | Solutions/predictions/scores/labels |
| Key params | Meaning and range |
| **Unit contract** | CO2(Mt) × GDP(亿元) → factor=100 for t/万元 |
| Verification | Which model type checks apply |
| Visualization | Chart types needed |

---

## Stage 3: ⏣ Model Audit (审稿手 Gate 1)

Lead: **审稿手** — 先读 `roles/审稿手.md`

### 阅读审计 — 门禁（BLOCKED if fail）

| # | 检查 | 通过标准 |
|---|------|---------|
| 1 | `notes/阅读笔记.md` 存在 | 含本地论文笔记 |
| 2 | 规律总结存在 | "规律总结"章节内容合理 |
| 3 | 本地论文 ≥3 篇 | 每篇有模型/结论/借鉴记录；<3篇→BLOCKED；3~4篇→WARN(低于保底5篇) |
| 4 | 算法文档已读 | 对应方法章节 |
| 5 | 外部文献 ≥5 篇 | paper_search 有结果记录 |

**判决**: 本地论文<3篇 或 阅读笔记不存在 → **BLOCKED**（退回 S1 补阅读）。3~4篇 → **WARN**。

### Proof-checker audit

| # | 检查 |
|---|------|
| 1 | 所有公式符号已定义 |
| 2 | 推导链完整 |
| 3 | 自变量独立性检查通过 |
| 4 | AHP/KKT/收敛性（如适用） |

### Idea audit

| # | 检查 |
|---|------|
| 1 | ≥2 种方案对比 |
| 2 | 每方案有文献支撑 |
| 3 | 4 维选择理由 |
| 4 | 满足三原则 |

**Output**: `assurance/proof_audit.json`, `assurance/idea_audit.json`

**Discuss with user**: Audit results. Proceed or revise?

---

## Stage 4: Data Preprocessing

Lead: **编程手** — 先读 `roles/编程手.md`

### ⏔ 阅读门禁（必须先完成）

产出：`notes/交接清单.md` 末尾追加确认

**阅读要求**:
1. `algorithms/` 中 S2 所选方法的代码实现章节
2. 算法源码示例，理解输入输出格式
3. 对照交接清单 Input format + Unit contract，确认量纲一致

**门禁规则**: 确认后 S7 审稿手检查——未确认则 **BLOCKED**。

### Gate Artifact 检查
- [ ] S3 审计产物存在: `assurance/idea_audit.json` + `assurance/proof_audit.json`
- [ ] 判决非 FAIL/BLOCKED（draft 等级除外）

### Main
1. Read raw data — `df.info()` `df.describe()`
2. Model-specific preprocessing
3. Verify format matches S2 scaffolding + unit contract
4. **Never modify `data/` original files**

---

## Stage 5: Model Solving

Lead: **编程手**

1. Read `notes/ProblemAnalysis.md` and scaffolding
2. Implement `solvers/problem{n}.py`
3. **Must execute code** after writing; fix errors in-place
4. **Prohibited**: simplified/alternative versions
5. Generate visualizations → `figures/`

**Output**: `solvers/` + `figures/` + `results/`

---

## Stage 6: Model Verification

Lead: **编程手**

1. Write `verifications/verify_problem{n}.py` for each solver
2. Run verification scripts
3. Code-audit **self-check**（编程手自检，正式审计在 S7）: constraint feasibility, solver consistency, dead code, result provenance
4. Result-to-Claim: build claim-support table
5. Record to `notes/trial_log.md`

**Verification checklist by model type**:

| Model Type | Checks |
|-----------|--------|
| Optimization | [V-OPT-1] Constraint feasibility, [V-OPT-2] Cross-verification, [V-OPT-3] Perturbation test |
| Regression/ML | [V-REG-1] Shapiro-Wilk (p>0.05), [V-REG-2] Breusch-Pagan, [V-REG-3] DW (1.5-2.5), [V-REG-4] 5-fold CV |
| ODE/Dynamics | [V-ODE-1] Conservation, [V-ODE-2] Boundary conditions, [V-ODE-3] Grid convergence |
| Network/Graph | [V-GRF-1] Path legality, [V-GRF-2] Flow conservation, [V-GRF-3] Small-scale brute force |

Each verify script: ≥1 numerical threshold, prints specific values.

---

## Stage 7: ⏣ Implementation Audit (审稿手 Gate 2)

Lead: **审稿手** — 先读 `roles/审稿手.md`

### 阅读审计 — 门禁（BLOCKED if fail）

| # | 检查 | 通过标准 |
|---|------|---------|
| 1 | `notes/交接清单.md` 含编程手确认 | "算法文档已阅读，数据格式已理解" |
| 2 | 可视化类型已规划 | 与算法文档中列出的图表一致 |
| 3 | Unit contract 已验证 | 量纲换算与交接清单一致 |

**判决**: S4 阅读未确认 → **BLOCKED**（退回 S4）

### Code-audit

| # | 检查 |
|---|------|
| 1 | 约束可行性 |
| 2 | 求解器交叉验证 |
| 3 | 死代码检测 |
| 4 | 结果文件溯源 |

### Result-to-Claim

Build claim-support map.

**Output**: `assurance/code_audit.json`, `assurance/claim_map.md`

---

## Stage 8: Sensitivity Analysis

Lead: **建模手**

**Gate Artifact 检查**:
- [ ] S7 审计产物存在: `assurance/code_audit.json` + `assurance/claim_map.md`

**Mandatory**:
1. Select ≥3 key parameters, perturb ±20%
2. Quantify output change (%)
3. Identify most sensitive parameter
4. Record to `notes/sensitivity.md`

---

## Stage 9: ⏣ Sensitivity Audit (审稿手)

Lead: **审稿手** — 先读 `roles/审稿手.md`

| # | Check | Standard |
|---|-------|---------|
| 1 | Key parameters | ≥3 perturbed |
| 2 | Perturbation range | ±20% baseline |
| 3 | Quantitative output | Must have %, "significant change" not acceptable |
| 4 | Most sensitive parameter | Identified and discussed |
| 5 | Multi-parameter | Bonus, not required |

**Output**: `assurance/sensitivity_audit.json`

---

## Stage 10: Paper Writing

Lead: **论文手** — 先读 `roles/论文手.md`

### ⏔ 阅读门禁（必须先完成）

产出：追加 `notes/阅读笔记.md` 的"写作借鉴"章节

**阅读要求**:
1. **优秀论文**: `references/papers/` 按题型子目录阅读 **保底 3 篇**
   - 重点分析：论文结构、摘要写法、公式排版、图表说明、模型评价
   - **必须产出写作规律总结**: 摘要结构模板、章节篇幅比例、图表密度、高频句式
2. **评阅要点**: 阅读对应年份评分标准，明确得分点

**门禁规则**: S11 审稿手检查——"写作借鉴"章节不存在则 **BLOCKED**。

### Gate Artifact 检查
- [ ] S9 审计产物存在: `assurance/sensitivity_audit.json`

### Main
1. Paper-plan: claim-evidence matrix + section topology + figure plan BEFORE writing
2. Copy LaTeX template → `paper/main.tex`
3. Figures: data plots as vector (PDF for xelatex compatibility)
4. Fill all chapters
5. De-AI-flavor (40+ detection markers)
6. Every figure ≥100 word analysis

**Discuss**: Show each chapter.

---

## Stage 11: ⏣ Paper Audit (审稿手 Gate 3)

Lead: **审稿手** — 先读 `roles/审稿手.md`

### 阅读审计 — 门禁（BLOCKED if fail）

| # | 检查 | 通过标准 |
|---|------|---------|
| 1 | `notes/阅读笔记.md` 含"写作借鉴"章节 | ≥2 篇论文结构分析 |
| 2 | 写作规律总结存在 | 摘要模板+篇幅比例+图表密度 |
| 3 | 评阅要点已读 | 有摘要/记录 |

**判决**: 任一不满足 → **BLOCKED**（退回 S10）

### Paper-claim-audit
Zero-context verification: every number in paper vs raw result files.

### Citation-audit
Three-layer: existence → metadata → context.

### Kill-argument
Dual-thread adversarial: attack → adjudicate.

**Output**: `assurance/claim_audit.json`, `assurance/citation_audit.json`, `assurance/kill_argument.json`

---

## Stage 12: Final Compilation

Lead: **论文手**

**Gate Artifact 检查**:
- [ ] S11 审计产物存在: `assurance/claim_audit.json` + `assurance/citation_audit.json` + `assurance/kill_argument.json`

**Mandatory**:
1. 3-round improvement loop (structure → numbers → AI-flavor)
2. Pre-compile: `python tools/file_ops/svg2pdf.py --session "name"` (SVG->PDF for xelatex)
3. Compile: `python tools/file_ops/compile_latex.py compile --mode cumcm`
4. Check: 8-25 pages, no errors, figure/table numbering continuous

---

## Stage 13: Assurance Gate & Scoring

Lead: — (Automated + user review)

1. Gate collect: `python tools/assurance/gate.py collect --session "name"`
2. Review gate_manifest.json with user
3. Score: `python tools/evolution/scorer.py --session "name" --mode standard`

---

## Stage 14: Evolution & Knowledge Archive

Lead: — (Automated + insight)

**Mechanical**:
```bash
python tools/evolution/evolver.py evolve --session "name" --from-scorer
python tools/assurance/query_pack.py --problem-type <type> --save
```

**Insight** (write experience summary to role EVOLUTION anchors):
1. Read eval_report.json, gate_manifest.json
2. Read notes/, solvers/, verifications/
3. Write 100-200 word summary under role doc anchors

---

## Stage 15: Packaging & Submission

1. Verify all deliverables
2. Package: `zip -r 提交.zip paper/main.pdf solvers/ figures/`
3. Confirm with user

---

## Model Selection: Three Principles

1. Use elementary methods when possible
2. Use simple methods when possible
3. Use methods understood by more people

---

## Absolute Prohibitions

1. Unverified data in paper
2. Silent skip on verification failure
3. Claim "verified" without running code
4. Modify original files in `data/`
5. Create simplified/alternative code versions
6. Modify LaTeX template formatting
7. Post figures without explanation
8. Audit FAIL at `submission` level without fixing
9. **Skip any numbered stage** (S0-S15, every number must be executed)
10. **Start paper writing without completing S10 reading gate**
