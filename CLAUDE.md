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

## 16-Stage Workflow

```
S0 ─→ S1 ─→ S2 ─→ S3 ─→ S4 ─→ S5 ─→ S6 ─→ S7 ─→ S8 ─→ S9 ─→ S10 ─→ S11 ─→ S12 ─→ S13 ─→ S14 ─→ S15
启动   分析   选择 ⏣审计1  数据   求解   验证 ⏣审计2  灵敏度 ⏣审计  论文  ⏣审计3   编译   评分   进化   打包
                                                             (灵敏度)
```

**S0-S2**: 建模手 | **S3**: 审稿手 | **S4-S6**: 编程手 | **S7**: 审稿手 | **S8**: 建模手 | **S9**: 审稿手 | **S10**: 论文手 | **S11**: 审稿手 | **S12**: 论文手 | **S13-S15**: 自动化

每个 `⏣` 是正式 Stage，有编号，不可跳过。**进度由你与用户的对话驱动，不是自动流水线。**

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━
## 第 0 章  运行时规则（进入任何 Stage 前必须先检查）
## ━━━━━━━━━━━━━━━━━━━━━━━━━━

### 0.1  行为协议（无条件优先的七条规则）

| # | 规则 | 说明 |
|---|------|------|
| 1 | **Write 前查权限** | 每次 Write/Create 操作前，对照 §0.2 权限矩阵确认当前 Stage 是否允许写该目录。禁止→立即停止。**路径范围检查**: 所有 session 产出必须写入 `sessions/{name}/` 下，禁止直接写入根目录下的同名目录（如 `paper/` → 必须写成 `sessions/{name}/paper/`）。系统级目录（`roles/` `algorithms/` `tools/` `templates/` `references/`）不受此限。|
| 2 | **进 Stage 前自检** | 每次进入新 Stage，先执行该 Stage 的"🔒 入口自检"，全部 PASS 才能执行 |
| 3 | **不确定则停止** | 不清楚当前 Stage、不清楚权限、不清楚是否可继续 → 停止并确认，不要猜 |
| 4 | **✦ 通读全文 ✦** | 每次"读 roles/*.md" 和读 `CLAUDE.md` 自身，必须从 `#` 到最后一个字符全部读完，停止于读到文档末尾的所有 EVOLUTION 锚点。禁止读到中途就认为"够了"。入口自检时列出该文档的大章节标题作为"已通读"证明。（结构验证）|
| 5 | **✦ 学习证据 ✦** | 入口自检 PASS 后，必须先对每份读过的文档产出**3 句话理解摘要**：读到了什么关键约束、有哪些陷阱需要避免、和前面读到的东西有什么关联。摘要写出来，用户确认理解无误后，才能进入执行步骤。（理解验证）|
| 6 | **✦ 认知自检 ✦** | 学习步骤末尾，输出一段自我对话：**"本 Stage 的核心任务是什么？最容易出错的一步是什么？之前的反模式/教训里有没有类似情况？"** 回答不出来 → 退回重读。回答有道理 → 进入执行。（综合验证）|
| 7 | **✦ 图表原则 ✦** | 默认单图绘制。两张图\emph{强相关}（如同一实验的对比、同一模型的不同参数）时允许用 `subplots(1,2)` 拼为一张，但**最多两张**，禁止三张及以上拼接。需多图时优先分多张 `.pdf`。|
| 8 | **✦ 公式完整原则 ✦** | ProblemAnalysis.md 必须包含**完整的数学公式**，不可省略。标准如下：<br>**(a) 适用所有题型** — 优化题写目标函数+约束、评价题写权重公式+得分公式、预测题写模型方程+误差公式、仿真题写微分/状态方程+离散化公式、图论题写路径/流/目标公式。不管什么题型，**每个子问题至少 3 个编号公式**。<br>**(b) 符号前置定义** — 所有公式中用到的符号必须在术语表中有条目，或紧邻公式上下方定义。禁止出现未定义的符号。<br>**(c) 推导链完整** — 从假设→中间推导→最终公式，每一步可追踪。禁止"显然可得""易知"等跳步表述。推导跳步 → S3 审稿手判 FAIL。<br>**(d) 公式编号** — 所有公式必须连续编号 `(1)(2)...`，论文引用时使用编号而非"如上式所示"。<br>**(e) 门禁** — S2 入口检查 ProblemAnalysis.md 是否有 `$$` 公式块且数量 ≥ 子问题数×3；S3 审稿手检查推导链完整性。不满足 → BLOCKED。|

### 0.2  写入权限矩阵

**查表方法**: 找到当前 Stage → 看对应列 → 找到目标目录 → 确认权限。禁止写入的目录不要碰。

| 目录 | S0 | S1 | S2 | S3 | S4 | S5-S6 | S7 | S8 | S9 | S10 | S11 | S12 | S13-S15 |
|------|:--:|:--:|:--:|:--:|:--:|:-----:|:--:|:--:|:--:|:---:|:---:|:---:|:------:|
| `notes/` | — | 写 | 写 | 读 | 读 | 读 | 读 | 写 | 读 | 读 | 读 | 读 | 读 |
| `solvers/` | — | 禁 | 禁 | 读 | 写 | 写 | 读 | 读 | 读 | 读 | 读 | 读 | 读 |
| `verifications/` | — | 禁 | 禁 | 读 | 写 | 写 | 读 | 读 | 读 | 读 | 读 | 读 | 读 |
| `figures/` | — | 禁 | 禁 | 读 | 写 | 写 | 读 | 读 | 读 | 读 | 读 | 读 | 读 |
| `results/` | — | 禁 | 禁 | 读 | 写 | 写 | 读 | 读 | 读 | 读 | 读 | 读 | 读 |
| `paper/` | — | 禁 | 禁 | 禁 | 禁 | 禁 | 禁 | 禁 | 禁 | 写 | 读 | 写 | 读 |
| `assurance/` | 写 | 读 | 读 | 写 | 读 | 读 | 写 | 读 | 写 | 读 | 写 | 读 | 写 |
| `data/` | 读 | 读 | 读 | 读 | 读 | 读 | 读 | 读 | 读 | 读 | 读 | 读 | 读 |

**违反处理**: 在禁写目录执行了 Write → 立即停止当前操作，不删除已写入内容，回退到权限允许的 Stage，确认后再继续。

```
角色权限速查:
  建模手 (S0-S2, S8): 写 notes/           禁写 solvers/ figures/ paper/
  编程手 (S4-S6):    写 solvers/ figures/  禁写 paper/ notes/(除交接确认)
  论文手 (S10, S12): 写 paper/             禁写 solvers/ figures/
  审稿手 (S3,7,9,11): 写 assurance/       禁写 solvers/ notes/ paper/
```

### 0.3  质量分级（全文统一）

每阶段产出不只判断"完成/未完成"，按三级评价：

| 等级 | 标记 | 论文影响 | 进入下一阶段 |
|------|------|---------|------------|
| 可接受 | □ | 及格线，评委可能扣分 | 可进，该产出的 S3/S7/S11 审计标记为 WARN |
| 良好 | ✅ | 中上水平，评委认可 | 可进 |
| 优秀 | ⭐ | 高分亮点 | 可进，必须追加经验到 EVOLUTION 锚点 |

每个 Stage 末尾给出该阶段的三级标准。提交等级为 `submission` 时，所有 WARN 和 ⭐ 产出需在论文定稿前处理。

### 0.4  产物依赖总表（文件级路由）

**用法**: 进任意 Stage，看该表"消费于"列——如果该 Stage 是消费者，检查"文件"列是否存在。不存在 → 不能进入。

| # | 文件 | 产于 | 消费于 | 缺失时的后果 |
|---|------|------|--------|------------|
| 1 | `assurance/level.txt` | S0 | S13 | S13 FAIL |
| 2a | `notes/阅读笔记_建模.md` | S1 | S3 | **S3 入口 BLOCKED** — 建模手未完成阅读门禁 |
| 2b | `notes/阅读笔记_编程.md` | S4 | S7 | **S7 入口 BLOCKED** — 编程手未完成阅读门禁 |
| 2c | `notes/阅读笔记_论文.md` | S10 | S11 | **S11 入口 BLOCKED** — 论文手未完成阅读门禁 |
| 2d | `notes/阅读笔记_审稿.md` | S3/S7/S9/S11 | S13 | S13 WARN — 审稿手未记录反模式 |
| 3 | `notes/ProblemAnalysis.md` | S1 | S2, S5 | S2 入口 BLOCKED, S5 入口 BLOCKED |
| 4 | `notes/术语表.md` | S1 | S2, S10 | S2 WARN, S10 WARN |
| 5 | `notes/交接清单.md` | S2 | S4, S7 | **S4 入口 BLOCKED**, S7 入口 BLOCKED |
| 6 | `assurance/proof_audit.json` | S3 | S13 | S13 FAIL |
| 7 | `assurance/idea_audit.json` | S3 | S13 | S13 FAIL |
| 8 | `solvers/*.py` | S5 | S6, S7, S12 | S6 入口 BLOCKED |
| 9 | `verifications/*.py` | S6 | S7, S12 | S7 入口 BLOCKED |
| 10 | `figures/*` | S5-S6 | S10, S12 | S10 入口 BLOCKED |
| 11 | `results/*` | S5-S6 | S10, S11 | S11 入口 BLOCKED |
| 12 | `assurance/code_audit.json` | S7 | S13 | S13 FAIL |
| 13 | `assurance/claim_map.md` | S7 | S10, S11 | S10 WARN, S11 WARN |
| 14 | `notes/sensitivity.md` | S8 | S9, S10 | S9 入口 BLOCKED |
| 15 | `assurance/sensitivity_audit.json` | S9 | S13 | S13 FAIL |
| 16 | `paper/main.tex` | S10-S12 | S12, S15 | S12 入口 BLOCKED, S15 BLOCKED |
| 17 | `assurance/claim_audit.json` | S11 | S13 | S13 FAIL |
| 18 | `assurance/citation_audit.json` | S11 | S13 | S13 FAIL |
| 19 | `assurance/kill_argument.json` | S11 | S13 | S13 FAIL |
| 20 | `assurance/gate_manifest.json` | S13 | S14 | S14 FAIL |
| 21 | `eval_report.json` | S13 | S14 | S14 FAIL |
| 22 | `提交.zip` | S15 | — | 提交物缺失 |

### 0.5  绝对禁止

| # | 规则 |
|---|------|
| 1 | 未验证的数据写入论文 |
| 2 | 验证失败但不处理，沉默跳过 |
| 3 | 未运行代码声称"已验证" |
| 4 | 修改 `data/` 原始文件 |
| 5 | 创建简化/替代版本的代码 |
| 6 | 修改 LaTeX 模板格式 |
| 7 | 论文贴图不加分析文字 |
| 8 | `submission` 等级 audit FAIL 不修复 |
| 9 | 跳过任何编号 Stage (S0-S15) |
| 10 | 未完成对应角色阅读门禁开始执行该角色的 Stage |
| 11 | Write 前未对照 §0.2 权限矩阵 |
| 12 | 进入新 Stage 未执行入口自检 |
| 13 | 将 session 产出写入根目录而非 `sessions/{name}/` 下 |
| 13 | 跳过 §0.1 规则 4/5/6（通读全文 / 学习证据 / 认知自检）直接执行 |
| 14 | 用户说"继续" ≠ 可以跳过学习步骤。进入新 Stage 必须从头运行入口自检 + 学习步骤

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━
## 第 1 章  各阶段详解
## ━━━━━━━━━━━━━━━━━━━━━━━━━━

每个 Stage 有一个统一模板（顺序不可变）：

```
┌─ 🔒 入口自检 ───────────────────────┐
│  逐条验证前置文件存在。第 0 行强制确认      │
│  角色文档和 CLAUDE.md 已通读。（§0.1规则4）│
│  全部 PASS 才能进下一步。          ──────┘
│
├─ ✦ 学习步骤（硬门禁）────────────────┐
│  1. 列出角色文档的大章节标题  (规则4 结构验证)│
│  2. 列出 skills/*.md 的关键执行指令       │
│  3. 读上一阶段产出 → 写 3 句理解摘要 (规则5 理解验证)│
│  4. 认知自检: "本Stage核心任务/最易错点/反模式警示" (规则6 综合验证)│
│  全部完成 → 进入执行。缺任一项 → 卡住。──┘
│
├─ ✅ 执行步骤 ────────────────────────┐
│  该 Stage 要完成的实际工作              │
│  (代码/论文/审计……)                ────┘
│
├─ 📊 质量基准 (□/✅/⭐) ──────────────┐
├─ 📤 产出 ───────────────────────────┐
└─ ⏭ 下一阶段 ────────────────────────┘
```

- 🔒 **入口自检**: 逐条验证前置文件存在，全部 PASS 才能继续。**第 0 行**强制确认角色文档和 `CLAUDE.md` 自身已通读到末尾 EVOLUTION 锚点。
- ✦ **学习步骤**: 入口自检 PASS 后必须完成。产出理解摘要 + 认知自检，作为进入执行的通行证。缺任一项 → 退回避补。
- 📁 **可写目录**: 当前 Stage 允许写的目录
- ✅ **执行步骤**: 该 Stage 要完成的内容
- 📊 **质量基准**: 三级标准（可接受/良好/优秀）
- 📤 **产出**: 本 Stage 产生的文件
- ⏭ **下一阶段**: 导向

---

### Stage 0: Startup & Pre-flight

**角色**: 建模手

#### 🔒 入口自检（全新问题无前置，全部从零开始）

| # | 检查 | PASS? |
|---|------|-------|
| 0 | 🔖 `roles/建模手.md` 已通读(列出章节标题，确认读到末尾 EVOLUTION 锚点) | □ |
| 1 | 用户已提供题目 PDF + 数据文件 | □ |
| 2 | 可在脑中推断 problem type | □ |

#### 📁 可写目录: `sessions/{name}/`

#### ✅ 执行步骤

1. 创建 session 目录:
```bash
mkdir -p sessions/problem_name/{data,notes,solvers,verifications,figures,paper,assurance}
```
2. 将 PDF 和数据文件放入 `data/`
3. 与用户确认 assurance level: `draft`（默认）或 `submission`
4. 写入 `assurance/level.txt`（内容为 `draft` 或 `submission`）
5. 读 `algorithms/index.json`，确认 `selection_rules`
6. 运行跨 session 知识查询:
```bash
python tools/assurance/query_pack.py --problem-type <inferred_type>
python tools/evolution/evolver.py suggest --problem-type <inferred_type>
python tools/search/local_knowledge.py "<关键词>"
```
7. 读 `roles/建模手.md`

#### 📊 Pre-flight 检查

- [ ] PDF 工具: `python -c "import pdfplumber; print('OK')"` — 确认可用
- [ ] LaTeX: `xelatex --version` — 确认编译器可用
- [ ] 数据文件: 已放入 `sessions/{name}/data/`，不在子目录
- [ ] 路径检查: session path 不含空格/特殊字符（避免 LaTeX include 问题）
- [ ] 图形格式: SVG 优先，编译前用 svg2pdf.py 转 PDF

#### 📤 产出
- `sessions/{name}/{data,notes,solvers,verifications,figures,paper,assurance}/`
- `assurance/level.txt`

#### ⏭ 下一阶段: S1 — 入口自检见下方

---

### Stage 1: Problem Analysis

**角色**: 建模手

#### 🔒 入口自检

| # | 检查 | 文件/操作 | PASS? |
|---|------|----------|-------|
| 0 | 🔖 `roles/建模手.md` 已通读(列出章节标题，确认读到 EVOLUTION 锚点) | 末尾有 `EVOLUTION:MODEL_OPTIMIZATION` 等 | □ |
| 1 | Session 目录存在 | `sessions/{name}/` | □ |
| 2 | `algorithms/index.json` 已读 | `selection_rules` 已确认 | □ |
| 3 | S0 知识检索已完成 | query_pack + evolver + local_knowledge | □ |
| 4 | ⏔ 阅读门禁: `notes/阅读笔记_建模.md` 不存在？→ 先执行阅读门禁再进 S1 | — | □ |

#### 📁 可写目录: `notes/`

#### ⏔ 阅读门禁（必须先完成 — S3 审稿手审计，不通过 BLOCKED）

**产出**: `notes/阅读笔记_建模.md`（含规律总结）

**阅读要求**:
1. **本地论文库**: `references/papers/` 按题型子目录阅读 **保底 5 篇**（上不封顶）
   - 每篇记录：模型方法、关键结论、对本题的参考价值
   - **必须产出规律总结**: 方法选择规律、论文章节规律、常见错误
2. **算法文档**: `algorithms/` 拟选方法的完整章节（公式、代码、适用范围）
3. **外部文献**: `python tools/search/paper_search.py --query "<关键词>"` **保底 5 篇**
4. **输出阅读清单**: 在 `notes/ProblemAnalysis.md` 开头附阅读清单表
5. **规律总结追加 EVOLUTION 锚点**: 读完论文后，将关键规律追加到 `roles/建模手.md` 底部 EVOLUTION 锚点

**门禁标准**: 本地论文<3篇 → S3 审稿手判决 BLOCKED；3~4篇 → WARN。以上全部完成后才可进入模型分析。

**论文快捷路径**:
```bash
ls references/papers/评价类/     # 按题型读论文
ls references/papers/预测类/
python tools/search/paper_search.py --query "碳达峰 预测 模型"   # 外部检索
```

#### ✅ 执行步骤

1. 从 PDF 阅读题目（使用 pdfplumber）
2. 检查 `data/` 中的数据文件
3. 确定题目类型（优化/预测/评价/分类等）
4. 多源文献检索（arXiv → Semantic Scholar → OpenAlex）
5. 生成 3-5 个候选模型方案，按四维排序: 拟合度 + 数据兼容性 + 可解释性 + 计算成本
6. **✱ 写出完整数学模型**（核心产出，不可省略）:
   - 每个子问题的**目标函数**（LaTeX 公式，带编号）
   - 每个子问题的**约束条件**（等式/不等式，逐一编号）
   - **所有变量的符号定义**（与 `notes/术语表.md` 交叉引用）
   - 至少包含：决策变量定义域、目标函数表达式、容量/匹配/逻辑约束
   - 写法标准：变量→目标函数→约束条件→求解方法，四段式。参照 `references/papers/` 中优秀论文的模型章节格式
7. 设计算法步骤、流程图、关键参数
8. 建立术语表
9. 在 `notes/ProblemAnalysis.md` 开头附阅读清单

#### 📊 质量基准

| 等级 | 标准 |
|------|------|
| 可接受 □ | 问题类型判断正确，≥2 个候选方案，阅读清单 ≥3 篇本地论文，**ProblemAnalysis.md 含每个子问题的目标函数和约束公式** |
| 良好 ✅ | ≥3 个候选（跨家族），四维排序有分析，阅读 ≥5 篇本地 + ≥5 篇外部，**每个子问题独立数学建模，符号与术语表交叉引用** |
| 优秀 ⭐ | 阅读独立总结出题型规律（方法选择/章节结构/常见错误），候选方案有文献数据支撑，**公式编号完整、推导链可追溯** |

#### 📤 产出
- `notes/ProblemAnalysis.md`（开头附阅读清单表）
- `notes/阅读笔记_建模.md`（含每篇笔记 + 规律总结章节）
- `notes/术语表.md`

#### ⏭ 下一阶段: S2

---

### Stage 2: Model Selection & Scaffolding

**角色**: 建模手

#### 🔒 入口自检

| # | 检查 | 文件 | PASS? |
|---|------|------|-------|
| 0 | 🔖 `roles/建模手.md` 已通读(列出章节标题，确认读到 EVOLUTION 锚点) | 末尾有 `EVOLUTION:MODEL_OPTIMIZATION` 等 | □ |
| 1 | ProblemAnalysis.md 存在 | `notes/ProblemAnalysis.md` | □ |
| 2 | **ProblemAnalysis.md 含 §数学模型 章节** — 至少包含目标函数和约束方程的 LaTeX 公式 | `notes/ProblemAnalysis.md` | □ |
| 3 | 阅读笔记存在且含规律总结 | `notes/阅读笔记_建模.md` | □ |
| 4 | 术语表存在 | `notes/术语表.md` | □ |
| 5 | 阅读笔记含规律总结章节 | `notes/阅读笔记_建模.md` §规律总结 | □ |

#### 📁 可写目录: `notes/`

#### ✅ 执行步骤

1. 与用户确认模型设计
2. **模型递进硬规则**: 必须使用≥2种方案对比，至少跨不同算法家族（例: LP + GA，不是 LP 的两种变体）
3. **Proof-checker 自检**（ARIS Module 1.3）:
   - 所有公式符号已在术语表中定义
   - 推导链完整——"显然可得"必须可验证
   - AHP 如用 → CR < 0.1
   - 优化模型 → 检查 KKT 条件
   - 迭代算法 → 收敛性论证
   - **自变量独立性检查**: 验证无预测变量是目标变量的代数变换（例: 用 CO2/GDP 预测 CO2 构成循环恒等式）
4. 按子问题搭模型脚手架
5. 确定数据需求

#### 模型选择三原则

```
1. 能用初等方法解决的就不用高等方法
2. 能用简单方法解决的就不用复杂方法
3. 能用被更多人看懂理解的就不用少数人看懂理解的方法
```

#### 交接清单产出 → `notes/交接清单.md`

| 项目 | 内容 |
|------|------|
| Problem # | 1/2/3/N |
| Algorithm | Name + why chosen |
| Input format | Columns, types, preprocessing |
| Output format | Solutions/predictions/scores/labels |
| Key params | Meaning and range |
| **Unit contract** | 量纲换算（例: CO2(Mt) × GDP(亿元) → factor=100 for t/万元） |
| Verification | 适用哪种模型类型检验 |
| Visualization | Chart types needed |

#### 算法选择规则

读 `algorithms/index.json` 选算法时:
1. 优先选 `evolved_status` 非 null 的方法 → 看历史验证最高分
2. 无已验证方法 → 选匹配题型的方法 → 标记为"首次使用，求解后需人工复核"
3. 选定后 → **必须**读 `algorithms/*.md` 中该方法的完整章节
4. 禁止只凭 index.json 中的名称选方法——必须读 .md 确认

#### 📊 质量基准

| 等级 | 标准 |
|------|------|
| 可接受 □ | ≥2 方案对比，选型有理由，交接清单含 7 项 |
| 良好 ✅ | 跨家族对比（≥2 个不同家族），Unit contract 明确量纲，Proof-checker 自检通过 |
| 优秀 ⭐ | 递进链设计（简单→复杂→情景），有文献数据支撑选型 |

#### 📤 产出
- `notes/交接清单.md`

#### ⏭ 下一阶段: S3 (审稿手 Gate 1)

---

### Stage 3: ⏣ Model Audit (审稿手 Gate 1)

**角色**: 审稿手 — 读 `roles/审稿手.md`

#### 🔒 入口自检

| # | 检查 | 文件 | PASS? |
|---|------|------|-------|
| 0 | 🔖 `roles/审稿手.md` 已通读(列出章节标题，确认读到末尾 EVOLUTION 锚点) | 末尾有 `EVOLUTION:AUDIT_*` | □ |
| 1 | 交接清单存在 | `notes/交接清单.md` | □ |
| 2 | ProblemAnalysis.md 存在 | `notes/ProblemAnalysis.md` | □ |

#### 📁 可写目录: `assurance/`

#### 阅读审计 — 门禁（BLOCKED if fail）

| # | 致命度 | 检查 | 通过标准 |
|---|--------|------|---------|
| 1 | 🔴 | `notes/阅读笔记_建模.md` 存在且含本地论文笔记 | 建模手独立阅读产出，笔记章节非空 |
| 2 | 🔴 | 规律总结章节存在（方法选择/章节结构/常见错误） | 规律总结章节内容合理 |
| 3 | 🔴 | 本地论文 ≥3 篇（建模类） | 每篇有模型/结论/借鉴记录；<3篇→BLOCKED；3~4篇→WARN(低于保底5篇) |
| 4 | 🔴 | **ProblemAnalysis.md 含完整的数学模型** — 每个子问题有目标函数公式和约束方程 | 至少有 `\min`, `\sum`, 约束编号等 LaTeX 结构 |
| 5 | 🟡 | 算法文档已读 | 对应方法章节 |
| 6 | 🟡 | 外部文献 ≥5 篇 | paper_search 有结果记录 |

**判决**: 本地论文<3篇 或 阅读笔记_建模.md 不存在 → **BLOCKED**（退回 S1 补阅读）。3~4篇 → **WARN**。

#### Proof-checker 审计

| # | 致命度 | 检查 | 通过标准 |
|---|--------|------|---------|
| 1 | 🔴 | **公式存在性** — ProblemAnalysis.md 是否包含所有子问题的数学公式 | 每个子问题至少 3 个编号公式，含目标/约束/推导（按 §0.1 规则 8 的题型清单） |
| 2 | 🔴 | **符号完整性** — 所有公式符号是否已定义 | 100% 符号可在术语表或公式上下文找到定义 |
| 3 | 🔴 | **推导链完整性** — 公式间是否有跳步 | 不存在"显然可得""易知""不难推出"等无推导说明的跳步；每个 `=` 的上一步→下一步需有文字解释 |
| 4 | 🟡 | 自变量独立性检查通过 | 无预测变量是目标变量的代数变换 |
| 5 | 🟡 | AHP/KKT/收敛性（如适用） | 按题型检查对应条件 |

#### Idea 审计

| # | 致命度 | 检查 |
|---|--------|------|
| 1 | 🔴 | ≥2 种方案对比 |
| 2 | 🟡 | 每方案有文献支撑 |
| 3 | 🟡 | 4 维选择理由 |
| 4 | 🟡 | 满足三原则 |

#### 致命度分级说明

| 级别 | 标记 | 含义 | 处理 |
|------|------|------|------|
| BLOCKED | 🔴 | 不可继续 | 退回重修，修复后重新审计 |
| WARN | 🟡 | 可继续但论文扣分 | 论文定稿前修复 |
| PASS | 🟢 | 通过 | 继续 |

#### 📤 产出
- `assurance/proof_audit.json`
- `assurance/idea_audit.json`

#### ⏭ 下一阶段: S4 — 入口自检需 S3 产物存在

---

### Stage 4: Data Preprocessing

**角色**: 编程手 — 读 `roles/编程手.md`

#### 🔒 入口自检

| # | 检查 | 文件 | PASS? |
|---|------|------|-------|
#### 🔒 入口自检

| # | 检查 | 文件 | PASS? |
|---|------|------|-------|
| 0 | 🔖 `roles/编程手.md` 已通读(列出章节标题，确认读到 EVOLUTION 锚点) | 末尾有 `EVOLUTION:CODE_*` 等 | □ |
| 1 | S3 审计产物存在 | `assurance/idea_audit.json` + `assurance/proof_audit.json` | □ |
| 2 | S3 判决非 BLOCKED（draft 等级除外） | — | □ |
| 3 | 交接清单已读 | `notes/交接清单.md` | □ |
| 4 | ⏔ 阅读门禁: `notes/阅读笔记_编程.md` 不存在？→ 先执行阅读门禁再进 S4 | — | □ |

#### 📁 可写目录: `solvers/`, `verifications/`, `figures/`, `results/`

#### ⏔ 阅读门禁（必须先完成 — S7 审稿手审计，未确认 BLOCKED）

**产出**: `notes/阅读笔记_编程.md`（含算法文档 + 代码模式规律总结）

**阅读要求**:
1. `algorithms/` 中 S2 所选方法的代码实现章节
2. 算法源码示例，理解输入输出格式
3. 对照交接清单 Input format + Unit contract，确认量纲一致
4. **必须产出规律总结**: 从算法文档和本地论文的代码示例中，总结代码组织/可视化/可复现性规律
5. 规律总结追加到 `notes/阅读笔记_编程.md`，写入"规律总结"章节

#### ✅ 执行步骤

1. 读原始数据 — `df.info()` `df.describe()`
2. 按模型特定需求做预处理
3. **✱ 运行前自检**（格式检查→通过后才准跑）:
   - 核对 load 函数的输出列名/类型与交接清单 Input format 一致
   - 核对 Unit contract（量纲换算、归一化）在代码中的实现与交接清单一致
   - 核对 `build_slot_index` 的货位数量/分区/层高区间与模型一致
4. 验证格式与 S2 脚手架 + Unit contract 一致
5. **绝不修改 `data/` 原始文件**

#### 📊 质量基准

| 等级 | 标准 |
|------|------|
| 可接受 □ | 数据已加载，格式与交接清单一致 |
| 良好 ✅ | 量纲验证通过，unit contract 已确认，缺失值/异常值已处理 |
| 优秀 ⭐ | 数据质量报告完整（分布/缺失/异常），预处理可复现 |

---

### Stage 5: Model Solving

**角色**: 编程手

#### 🔒 入口自检

| # | 检查 | 文件 | PASS? |
|---|------|------|-------|
| 0 | 🔖 `roles/编程手.md` 已通读(列出章节标题) | — | □ |
| 1 | 交接清单含编程手确认 | `notes/交接清单.md` 含"算法文档已阅读" | □ |
| 2 | ProblemAnalysis.md 已读 | `notes/ProblemAnalysis.md` | □ |

#### 📁 可写目录: `solvers/`, `figures/`, `results/`

#### ✅ 执行步骤

1. 读 `notes/ProblemAnalysis.md` 和脚手架
2. 实现 `solvers/p{n}_*.py`
3. **✱ 运行前自检**（代码写完→立即做→通过后才准运行）:
   - **(a) 公式-代码逐行对照**: 把 ProblemAnalysis.md 中该子问题的所有编号公式抄到 `notes/trial_log.md`，每个公式旁边写下它在代码中的行号。找不到对应行的公式 → 代码缺了，补完再继续。
   - **(b) 参数值核对**: 代码中的每个物理参数/算法参数与模型文档声明的值一一比对。不一致 → 修正代码。
   - **(c) 逻辑走向检查**: 算法的"主循环→分支→输出"路径是否与模型设计的流程图一致。有 `break`/`continue`/`return` 的地方逐行注释说明其目的。
   - 自检全部通过 → 记录到 `notes/trial_log.md`。
4. **必须执行代码**写完后立即运行；有错当场修
5. **禁止**创建简化/替代版本
6. 生成可视化 → `figures/`

#### 📊 质量基准

| 等级 | 标准 |
|------|------|
| 可接受 □ | 代码运行通过，输出与预期一致 |
| 良好 ✅ | 代码无 dead code，有注释说明关键步骤，**每图单张绘制(无 subplot 拼接)**，图表清晰 |
| 优秀 ⭐ | 结果可复现（seed 固定），数值精度已验证，所有关键决策点有输出日志 |

#### 📤 产出
- `solvers/*.py`
- `figures/*`
- `results/*`

#### ⏭ 下一阶段: S6

---

### Stage 6: Model Verification

**角色**: 编程手

#### 🔒 入口自检

| # | 检查 | 文件 | PASS? |
|---|------|------|-------|
| 0 | 🔖 `roles/编程手.md` 已通读(列出章节标题) | — | □ |
| 1 | solvers 已存在且运行通过 | `solvers/*.py` | □ |
| 2 | results 目录有输出 | `results/*` | □ |

#### ✅ 执行步骤

1. 为每个 solver 写 `verifications/verify_p{n}.py`
2. 运行验证脚本
3. **编程手自检**（正式审计在 S7）:
   - **代码-模型一致性**（最重要）：逐公式核对 ProblemAnalysis.md 的每个编号公式是否在代码中有对应实现
   - **参数一致性**：代码中的 v_h/v_v/a/T_load 等是否与模型文档一致
   - 约束可行性
   - 求解器一致性
   - 死代码检查
   - 结果文件溯源
4. 构建 claim-support 表
5. 记录到 `notes/trial_log.md`

#### 按模型类型的验证清单

| Model Type | Checks |
|-----------|--------|
| Optimization | [V-OPT-1] Constraint feasibility, [V-OPT-2] Cross-verification, [V-OPT-3] Perturbation test |
| Regression/ML | [V-REG-1] Shapiro-Wilk (p>0.05), [V-REG-2] Breusch-Pagan, [V-REG-3] DW (1.5-2.5), [V-REG-4] 5-fold CV |
| ODE/Dynamics | [V-ODE-1] Conservation, [V-ODE-2] Boundary conditions, [V-ODE-3] Grid convergence |
| Network/Graph | [V-GRF-1] Path legality, [V-GRF-2] Flow conservation, [V-GRF-3] Small-scale brute force |

每个验证脚本: ≥1 数值阈值，打印具体值。

#### 📊 质量基准

| 等级 | 标准 |
|------|------|
| 可接受 □ | 每 solver 有验证脚本，≥1 数值阈值通过 |
| 良好 ✅ | 全部模型类型对应检查通过，约束可行性确认 |
| 优秀 ⭐ | 交叉验证通过（不同方法结果一致），扰动测试稳定 |

#### 📤 产出
- `verifications/*.py`
- `notes/trial_log.md`

#### ⏭ 下一阶段: S7 (审稿手 Gate 2)

---

### Stage 7: ⏣ Implementation Audit (审稿手 Gate 2)

**角色**: 审稿手 — 读 `roles/审稿手.md`

#### 🔒 入口自检

| # | 检查 | 文件 | PASS? |
|---|------|------|-------|
| 0 | 🔖 `roles/审稿手.md` 已通读(列出章节标题) | — | □ |
| 1 | solvers 存在 | `solvers/*.py` | □ |
| 2 | verifications 存在 | `verifications/*.py` | □ |
| 3 | 交接清单可读 | `notes/交接清单.md` | □ |

#### 📁 可写目录: `assurance/`

#### 阅读审计 — 门禁（BLOCKED if fail）

| # | 致命度 | 检查 | 通过标准 |
|---|--------|------|---------|
| 1 | 🔴 | `notes/阅读笔记_编程.md` 存在 | 编程手独立阅读产出，含规律总结 |
| 2 | 🔴 | `notes/交接清单.md` 含编程手确认 | "算法文档已阅读，数据格式已理解" |
| 3 | 🔴 | 可视化类型已规划 | 与算法文档中列出的图表一致 |
| 4 | 🟡 | Unit contract 已验证 | 量纲换算与交接清单一致 |

**判决**: 阅读笔记_编程.md 不存在或 交接清单未确认 → **BLOCKED**（退回 S4）

#### Code 审计

| # | 致命度 | 检查 | 通过标准 |
|---|--------|------|---------|
| 1 | 🔴 | **代码-模型一致性** ★ | 遍历 ProblemAnalysis.md 中所有编号公式，逐个在 solvers/ 代码中找到对应实现行。公式→代码的映射写入 audit 记录。公式在代码中缺失、或被改写为不同逻辑 → FAIL |
| 2 | 🔴 | **参数一致性** | 代码中的物理参数/算法参数值与 ProblemAnalysis.md 和交接清单中声明的值一致。容忍 ±0（精确匹配） |
| 3 | 🔴 | 约束可行性 | 优化/仿真结果满足模型中的所有约束条件 |
| 4 | 🟡 | 求解器交叉验证 | 不同 solver/不同 seed 结果一致（误差 < 1%） |
| 5 | 🟡 | 死代码检测 | 无定义但未调用的函数，无 unreachable code |
| 6 | 🟡 | 结果文件溯源 | results/ 中每个文件可由对应 solver 重新生成 |

#### Result-to-Claim

构建 claim-support 对照表。

#### 📤 产出
- `assurance/code_audit.json`
- `assurance/claim_map.md`

#### ⏭ 下一阶段: S8

---

### Stage 8: Sensitivity Analysis

**角色**: 建模手

#### 🔒 入口自检

| # | 检查 | 文件 | PASS? |
|---|------|------|-------|
| 0 | 🔖 `roles/建模手.md` 已通读(列出章节标题) | — | □ |
| 1 | S7 审计产物存在 | `assurance/code_audit.json` + `assurance/claim_map.md` | □ |
| 2 | 代码验证已通过 | S7 code audit 非 BLOCKED | □ |

#### 📁 可写目录: `notes/`

#### ✅ 执行步骤

1. 选取 ≥3 个关键参数，扰动 ±20%
2. 量化输出变化（%），不能只说"显著变化"
3. 识别最敏感参数
4. 多参数联合扰动（加分项）
5. 记录到 `notes/sensitivity.md`

#### 📊 质量基准

| 等级 | 标准 |
|------|------|
| 可接受 □ | ≥3 参数 ±20% 扰动，有百分比数字 |
| 良好 ✅ | 最敏感参数已识别并讨论原因，图表清晰 |
| 优秀 ⭐ | 多参数联合扰动分析，灵敏度与物理/经济机理关联 |

#### 📤 产出
- `notes/sensitivity.md`

#### ⏭ 下一阶段: S9 (审稿手 Gate 3)

---

### Stage 9: ⏣ Sensitivity Audit (审稿手 Gate 3)

**角色**: 审稿手 — 读 `roles/审稿手.md`

#### 🔒 入口自检

| # | 检查 | 文件 | PASS? |
|---|------|------|-------|
| 0 | 🔖 `roles/审稿手.md` 已通读(列出章节标题) | — | □ |
| 1 | 灵敏度分析完成 | `notes/sensitivity.md` | □ |

#### 📁 可写目录: `assurance/`

| # | 致命度 | 检查 | 通过标准 |
|---|--------|------|---------|
| 1 | 🔴 | 关键参数 | ≥3 个被扰动 |
| 2 | 🔴 | 扰动范围 | ±20% baseline |
| 3 | 🔴 | 定量输出 | 必须有 %，"显著变化"不合格 |
| 4 | 🟡 | 最敏感参数 | 已识别并讨论 |
| 5 | 🟡 | 多参数联合 | 加分项，非必须 |

#### 📤 产出
- `assurance/sensitivity_audit.json`

#### ⏭ 下一阶段: S10

---

### Stage 10: Paper Writing

**角色**: 论文手 — 读 `roles/论文手.md`

#### 🔒 入口自检

| # | 检查 | 文件 | PASS? |
|---|------|------|-------|
| 0 | 🔖 `roles/论文手.md` 已通读(列出章节标题，确认读到 EVOLUTION 锚点) | 末尾有 `EVOLUTION:WRITING_*` | □ |
| 1 | S9 审计产物存在 | `assurance/sensitivity_audit.json` | □ |
| 2 | 全部 results/figures 存在 | `results/*`, `figures/*` | □ |
| 3 | 灵敏度分析完成 | `notes/sensitivity.md` | □ |
| 4 | ⏔ 阅读门禁: `notes/阅读笔记_论文.md` 不存在？→ 先执行阅读门禁再进 S10 | — | □ |

#### 📁 可写目录: `paper/`

#### ⏔ 阅读门禁（必须先完成 — S11 审稿手审计，不通过 BLOCKED）

**产出**: `notes/阅读笔记_论文.md`（论文手独立阅读，含写作规律总结）

**阅读要求**:
1. **优秀论文**: `references/papers/` 按题型子目录阅读 **保底 3 篇**
   - 重点分析：论文结构、摘要写法、公式排版、图表说明、模型评价
   - **必须产出写作规律总结**: 摘要结构模板、章节篇幅比例、图表密度、高频句式
2. **评阅要点**: 阅读 `references/官方资料/评阅要点/` 对应年份评分标准，明确得分点

**门禁规则**: S11 审稿手检查—`阅读笔记_论文.md` 不存在或不含写作规律总结 → **BLOCKED**（退回 S10）。

#### ✅ 执行步骤

1. **✦ 阅读门禁（第一步，不可跳过）**: 读 ≥3 篇优秀论文 + 评阅要点 → 产 `notes/阅读笔记_论文.md` + 写作规律总结。未完成 → 不准动笔。
2. Paper-plan: claim-evidence 矩阵 + 章节拓扑 + 图表计划（写代码前先规划）
3. 复制 LaTeX 模板 → `paper/main.tex`
4. 图表: 数据图用矢量格式（PDF for xelatex 兼容）
5. 填充所有章节
6. 去 AI 味（40+ 检测标记）
7. 每张图 ≥100 字分析

**每节完成后与用户讨论**。

#### 📊 质量基准

| 等级 | 标准 |
|------|------|
| 可接受 □ | 所有章节已填，论文可编译，图有标题，**22-25页**（≥22页且≤25页），每子问题≥6个编号公式 |
| 良好 ✅ | 摘要满足标准结构(背景1+问题2+方法2+结果1)，模型评价含 Strengths & Weaknesses(≥4条优势+≥4条局限)，每图≥100字分析，**含算法伪代码/流程图，含数据预处理节，含复杂度分析** |
| 优秀 ⭐ | 自创指标/命名变体，模型递进链清晰，灵敏度与机理关联，无 AI 味标记，**页数达最优目标**，结论节≥5条编号总结，每个公式有完整推导链说明 |

**页数硬约束（国赛 vs 美赛不同）**：

| 竞赛 | 页数范围 | 最优目标 | 含什么 | 不含什么 |
|------|---------|---------|--------|---------|
| **国赛 (CUMCM)** | 正文 **25-30页** | 27-28页 | 从问题重述→结论+参考文献；附录无限制 | 摘要页、目录(不要目录)、AI使用报告 |
| **美赛 (MCM/ICM)** | 全文 **22-25页** | 24-25页 | 所有内容（需要目录，不要附录） | AI使用报告 |

**国赛页面结构**：第1页=承诺书(不管)，第2页=编号页，第3页=摘要，第4页起=正文(含参考文献)，最后=AI使用报告(不算正文)。**国赛正文不要目录**。

**美赛页面结构**：第1页=摘要，后跟目录，然后正文，最后是AI使用报告(不算入25页)。美赛需要目录，不要附录。

**各子问题内容密度标准**（每个子问题的节必须覆盖以下全部）：
1. 数学模型：符号定义表 + 目标函数 + ≥2条约束/条件 + 推导步骤说明
2. 求解方法：算法思路 + 伪代码或编号步骤列表(≥4步) + 复杂度分析(O记号)
3. 结果分析：数值结果 + 图表(≥1张) + ≥100字图表分析 + 与前问/前模型的对比讨论

**论文格式规范（强制，S11审计检查）**：

| # | 规则 | 说明 | 示例 |
|---|------|------|------|
| 1 | **摘要独立成页** | 国赛第3页为摘要页，只含标题+摘要+关键词，不含竞赛信息（承诺书/编号在1-2页） | ✅ `\maketitle`→`\newpage`→标题+摘要+关键词 ❌ 摘要放在`\makesheet`内→摘要页上有"高教社杯""参赛编号" |
| 2 | **摘要标题在上** | 摘要页顶部为论文标题（三号黑体居中），然后"摘要"二字，然后摘要正文 | ✅ `{\heiti\sanhao 论文标题}\par {\heiti\xiaosanhao\textbf{摘\quad 要}}` ❌ 只有"摘要"没有标题 |
| 3 | **摘要首行缩进** | 2em（两个汉字宽度），`\parindent=2em` | ✅ `\setlength{\parindent}{2em} 本文...` ❌ 首行顶格，像英文格式 |
| 4 | **摘要关键词加粗** | **加粗对象**：自创指标名(货位热度)、模型名(整数规划模型、复合作业模型)、方法名(贪心启发式、遗传算法)、核心数值(19.32s, 23.8%, 11.23%)；**不加粗**："针对问题X"、连接词、普通描述 | ✅ `\textbf{``货位热度''指标}` ❌ `\textbf{针对问题一}` |
| 5 | **摘要最后一句话是总结** | 不以灵敏度分析或某个子问题结尾，最后一句概括全部工作和核心结论 | ✅ "综合五个问题的递进求解...形成了完整决策闭环" ❌ "灵敏度分析表明v_v是最敏感参数..." |
| 6 | **问题重述不分小节** | 无 `\subsection`，连续段落。首段背景+数据参数，次段五问题各一句话概述。不用 `\begin{enumerate}` 列问题 | ✅ 两段连续文字 ❌ `\subsection{问题背景}`+`\subsection{要解决的具体问题}` |
| 7 | **模型假设不写依据** | 只列5条核心假设，直接写结论。**禁止**：引导句"为使模型具有可操作性..."、`\textit{依据：}`、括号注释如"(问题一至三使用...)"。不写不重要假设（如"系统连续运行""不考虑故障"） | ✅ `\begin{assumption}堆垛机水平与垂直运动独立驱动。\end{assumption}` ❌ 写"为使模型具有可操作性..."+"\textit{依据：}" |
| 8 | **图表浮动控制** | 关键图表用 `[ht]` 靠近插入点；普通图表用 `[htbp]` 放权浮动；大节前 `\clearpage` 清浮。禁止全局 `[H]`（除符号表） | ✅ 符号表不用float，结果表`[ht]`，大图`[htbp]`，节前`\clearpage` ❌ 全`[H]`→空白，全`[htbp]`→符号表飘走 |
| 11 | **图表后必有分析** | 每张图/表之后紧跟 ≥100字分析文字（图→分析，不是分析→图）。禁止两张图/表之间无分析文字直接相连 | ✅ `\end{figure}`→分析文字→`\begin{figure}` ❌ 分析文字在`\begin{figure}`之前，或两图背靠背 |
| 9 | **公式间距不设负值** | `\belowdisplayskip` ≥ 0，避免公式后文字重叠 | ✅ `3pt plus 1pt` ❌ `-8pt`→文字与公式重叠 |
| 10 | **行距统一** | `\setstretch{1.5}`，不在局部修改 | ✅ 全局统一 ❌ 某节局部改行距 |

**国赛论文各节页数规划**（国赛标准结构：8节，目标正文27-28页）：

| 节 | 建议页数 | 说明 |
|----|---------|------|
| 一、问题重述 | 0.5-1页 | 简要，不复制原题 |
| 二、问题分析 | 1-1.5页 | 每题一小段，点明数学本质和求解思路 |
| 三、模型假设 | 0.5页 | 5条左右核心假设 |
| 四、符号说明 | 0.5页 | 表格 |
| 五、模型的建立与求解 | 20-22页 | 主体，五个子问题 |
| — 数据预处理 | 1页 | 统计表+箱型分布 |
| — 问题一 | 4-5页 | 数学模型1页+算法1.5页+结果1.5页 |
| — 问题二 | 3-4页 | 模型1页+策略/死锁1页+结果1页 |
| — 问题三 | 3-4页 | DC推导1页+入库策略0.5页+结果1页 |
| — 问题四 | 3-4页 | 运动学推导1.5页+对比1页+讨论0.5页 |
| — 问题五 | 2-3页 | 模型1页+仿真0.5页+策略建议0.5页 |
| 六、灵敏度分析 | 2-3页 | 单参数表+联合表+机理分析+工程启示（含模型检验作为子节） |
| 七、模型评价与推广 | 2-3页 | 模型讨论+模型检验+4+4条优缺点+3推广场景 |
| 八、结论 | 1页 | ≥5条编号总结，含数值汇总表 |

注：国赛论文只有这8个一级节。"模型对比与讨论""模型检验"不单独成节——放在灵敏度分析或模型评价里作为子节。

#### 📤 产出
- `notes/阅读笔记_论文.md`
- `paper/main.tex`

#### ⏭ 下一阶段: S11 (审稿手 Gate 4)

---

### Stage 11: ⏣ Paper Audit (审稿手 Gate 4)

**角色**: 审稿手 — 读 `roles/审稿手.md`

#### 🔒 入口自检

| # | 检查 | 文件 | PASS? |
|---|------|------|-------|
| 0 | 🔖 `roles/审稿手.md` 已通读(列出章节标题) | — | □ |
| 1 | paper/main.tex 存在 | `paper/main.tex` | □ |
| 2 | results 目录有数据 | `results/*` | □ |

#### 📁 可写目录: `assurance/`

#### 阅读审计 — 门禁（BLOCKED if fail）

| # | 致命度 | 检查 | 通过标准 |
|---|--------|------|---------|
| 1 | 🔴 | `notes/阅读笔记_论文.md` 存在且含写作规律总结 | ≥2 篇论文结构分析 + 摘要模板 + 篇幅比例 + 图表密度 |
| 2 | 🔴 | 论文手独立阅读产出（非复用建模手笔记） | 文件中有写作相关的独立分析内容 |
| 3 | 🔴 | 页数在竞赛要求范围内 | 国赛：正文25-30页(不含摘要/附录/AI报告)；美赛：全文22-25页(含目录，不含AI报告)；不在范围→BLOCKED |
| 4 | 🟡 | 每子问题节 ≥6 个编号公式 | grep `\begin{equation}` 统计 |
| 5 | 🟡 | 每子问题节有算法伪代码 | ≥4步的 enumerate |
| 6 | 🟡 | 评阅要点已读 | 有摘要/记录 |

**判决**: 任一不满足 → **BLOCKED**（退回 S10）

#### Paper-claim 审计

零上下文验证: 论文中每个数字与 result 文件对比，必须一致。

#### Citation 审计

三层验证: 存在性 → 元数据 → 上下文匹配。

#### Kill-argument

双线程对抗: 攻击 → 裁决。论文能否经受住最严厉的评审批评？

#### 📤 产出
- `assurance/claim_audit.json`
- `assurance/citation_audit.json`
- `assurance/kill_argument.json`

#### ⏭ 下一阶段: S12

---

### Stage 12: Final Compilation

**角色**: 论文手

#### 🔒 入口自检

| # | 检查 | 文件 | PASS? |
|---|------|------|-------|
| 0 | 🔖 `roles/论文手.md` 已通读(列出章节标题) | — | □ |
| 1 | S11 审计产物存在 | `assurance/claim_audit.json` + `citation_audit.json` + `kill_argument.json` | □ |
| 2 | 论文已定稿 | `paper/main.tex` | □ |

#### 📁 可写目录: `paper/`

#### ✅ 执行步骤

1. 三轮改进循环（结构 → 数字 → AI 味）
2. 预编译: `python tools/file_ops/svg2pdf.py --session "name"` (SVG→PDF for xelatex)
3. 编译: `python tools/file_ops/compile_latex.py compile --mode cumcm`
4. 检查: **国赛正文 25-30页**（含参考文献，不含摘要/附录/AI报告），**美赛全文 22-25页**（含目录，不含附录/AI报告），无编译错误，图/表编号连续，公式数≥子问题数×6
5. **页数不在范围 → 退回 S10 补/删内容**；<下限→补充推导细节/伪代码/分析文字；>上限→精简冗余描述
6. 编译后完整性检查: `python tools/file_ops/check_outputs.py`

#### 📊 质量基准

| 等级 | 标准 |
|------|------|
| 可接受 □ | 编译通过，8-25页，图表编号连续 |
| 良好 ✅ | 三轮改进完成，零编译 warning (xelatex) |
| 优秀 ⭐ | 排版优美（无孤行/overflow），引用格式统一，section 比例符合规律总结 |

#### 📤 产出
- `paper/main.pdf`

#### ⏭ 下一阶段: S13

---

### Stage 13: Assurance Gate & Scoring

**角色**: 自动化 + 用户审核

#### 📁 可写目录: `assurance/`

#### ✅ 执行步骤

1. Gate collect:
```bash
python tools/assurance/gate.py collect --session "name" --assurance submission
```
2. 与用户一起审查 `assurance/gate_manifest.json`
3. 评分:
```bash
python tools/evolution/scorer.py --session "name" --mode standard
```

#### Baseline Usage Rules

评分后，对照 `references/empirical_baselines.json` 的 `usage_rules`:
- `vs_self_pct < 50%` → 分数下降，在经验章节写原因
- `any dim < 0.65` → 读对应 writer chapter (ref_dim_map)，写改进计划
- `all dims > p75` → 记录成功模式
- `total score beats personal best` → 标记为里程碑

#### 📤 产出
- `assurance/gate_manifest.json`
- `eval_report.json`

#### ⏭ 下一阶段: S14

---

### Stage 14: Evolution & Knowledge Archive

**角色**: 自动化 + AI insight

#### 📁 可写目录: `roles/` (追加 EVOLUTION 锚点)

#### Mechanical (Python auto)

```bash
python tools/evolution/evolver.py evolve --session "name" --from-scorer
# Updates: modeler verification table, algorithm marks, structured score analysis.

python tools/assurance/query_pack.py --problem-type <type> --save
# Updates master query_pack.md so future sessions can learn from this run.
```

#### Insight + Meta-Optimize (you do it)

读 evolver analysis JSON + gate_manifest.json (weak/strong areas, anchors), then:

1. 读 `eval_report.json` — 完整评分分解
2. 读 `assurance/gate_manifest.json` — 审计判决
3. 读 `notes/` — 思维过程
4. 读 `solvers/` + `verifications/` — 实现细节
5. **Meta-optimize**: 哪个阶段 FAIL→fix 循环次数最多？提出 1-3 个流程改进建议
6. **写 100-200 字经验总结**追加到角色文档的 EVOLUTION 锚点:
   - What → Low dims → Why → How to improve
7. 目标锚点: `MODEL_<type>`, `CODE_<type>`, `WRITING_<chapter>`, `AUDIT_<type>`

**查询命令**:
```bash
python tools/evolution/evolver.py gaps      # 知识缺口
python tools/evolution/evolver.py suggest --problem-type X  # 策略查找
python tools/evolution/evolver.py sessions  # 所有 session 记录
```

#### 📤 产出
- 角色文档 EVOLUTION 锚点更新
- `query_pack.md` 更新

#### ⏭ 下一阶段: S15

---

### Stage 15: Packaging & Submission

#### ✅ 执行步骤

1. 验证所有交付物齐全
2. 打包:
```bash
zip -r 提交.zip paper/main.pdf solvers/ figures/
```
3. 与用户确认

#### 📤 产出
- `提交.zip`

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━
## 第 2 章  参考
## ━━━━━━━━━━━━━━━━━━━━━━━━━━

### 2.1  角色切换

进入 Stage 前，先读对应角色文档:
- **建模手** (S0-S2, S8): `roles/建模手.md`
- **编程手** (S4-S6): `roles/编程手.md`
- **论文手** (S10, S12): `roles/论文手.md`
- **审稿手** (S3, S7, S9, S11): `roles/审稿手.md`

### 2.2  12 Tools

需要时调用:

| 类别 | 工具 | 干什么 | 什么时候用 |
|------|------|--------|----------|
| File Ops | `tools/file_ops/compile_latex.py` | Compile .tex to .pdf (multi-pass) | Stage 12 |
| File Ops | `tools/file_ops/pdf_extractor.py` | Extract text/tables from PDFs | Stage 1 (读PDF) |
| File Ops | `tools/file_ops/data_checker.py` | Encoding detection + data quality report | Stage 4 |
| File Ops | `tools/file_ops/check_outputs.py` | Post-compile integrity check | Stage 12 |
| Search | `tools/search/paper_search.py` | Multi-source academic search | Stage 1 |
| Search | `tools/search/local_knowledge.py` | 3-source local knowledge retrieval | Stage 0-1 |
| Evolution | `tools/evolution/scorer.py` | 10-dim scoring + auto-save | Stage 13 |
| Evolution | `tools/evolution/evolver.py` | Mechanical + insight evolution | Stage 14 |
| **Assurance** ★ | `tools/assurance/contract.py` | 6-state verdict engine + SHA256 tracing | S2/S3/S7/S11/S13 |
| **Assurance** ★ | `tools/assurance/gate.py` | Collect audits → gate_manifest.json | Stage 13 |
| **Assurance** ★ | `tools/assurance/query_pack.py` | Cross-session knowledge summary | S0/S14 |

### 2.3  Knowledge Assets

| Asset | Location | Content |
|------|------|------|
| Algorithm Library | `algorithms/index.json` + `algorithms/*.md` | 9 domains, 27 subdomains, 74 methods |
| Paper Library | `references/papers/` | ~1330 indexed PDFs, 6 categories |
| Scoring Baselines | `references/empirical_baselines.json` | 10-dim baselines with usage_rules |
| Antipattern Library | `references/patterns/` (if exists), embedded in role EVOLUTION anchors | 28 antipatterns by topic |
| Review Criteria | `references/官方资料/评阅要点/` | CUMCM criteria 2004-2018 |
| Experience Sharing | `references/官方资料/经验分享/` | Tutorials, writing guides, MCM tips |
| Evolution Records | `roles/` EVOLUTION sections | Strategies + code templates accumulated across sessions |
| Historical Scores | `sessions/*/eval_report.json` | Auto-saved score reports |
| LaTeX Templates | `templates/` | CUMCM (`latex_template.tex`) + MCM (`mcm_template.tex`) |
| Problem Archive | `sessions/` | All past problems |

### 2.4  Paper Reading Protocol（阅读门禁 — 每个角色必须在各自阶段开始时完成）

**核心原则**:
1. **各角色各读各的** — 建模手读方法论文、编程手读实现论文、论文手读写作范文、审稿手读评阅标准。不可 S1 读一次贯穿全流程。
2. **读尽可能多** — 保底是地板，不是天花板。论文库 ~1330 篇，同类题型可能有几十篇候选，多读才能总结出可靠规律
3. **必须总结规律** — 读单篇知道"这篇做了什么"，读多篇总结出"这类题应该怎么做"

**角色-产出对应**:

| 角色 | Stage | 产出文件 | 读什么 |
|------|-------|---------|--------|
| 建模手 | S1 | `notes/阅读笔记_建模.md` | 方法选择、模型组合、推导链 |
| 编程手 | S4 | `notes/阅读笔记_编程.md` | 代码结构、可视化类型、验证模式 |
| 审稿手 | S3/S7/S9/S11 | `notes/阅读笔记_审稿.md` | 评阅标准、常见反模式(每次审计时追加) |
| 论文手 | S10 | `notes/阅读笔记_论文.md` | 摘要写法、章节比例、图表规范 |

**各角色详细要求**: 详见 S1, S4, S10 的 ⏔ 阅读门禁章节。审稿手的反模式记录见 `roles/审稿手.md`。

**模式进化机制**: 规律总结写完后，**必须追加到 `roles/*.md` 中对应的 `EVOLUTION` 锚点**。这样:
- 下次启动 `query_pack.py --problem-type X` 自动加载积累的模式
- 新 session 的 modeling/writing 锚点内容就是之前所有 session 的规律汇总
- 不需每次重读论文，模式会随时间越来越多

### 2.5  Role-Stage Mapping

| 阶段 | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 | S10 | S11 | S12 | S13 | S14 | S15 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 角色 | 建模 | 建模 | 建模 | 审稿 | 编程 | 编程 | 编程 | 审稿 | 建模 | 审稿 | 论文 | 审稿 | 论文 | 自动 | 自动 | 自动 |

### 2.6  Verification by Model Type

详见 S6。

### 2.7  Evolution Anchors in Role Docs

`roles/` 文档底部有 `<!-- EVOLUTION:MODEL_<TYPE> -->` 等锚点。每个 session 完成后，将经验规律追加到对应锚点下。下次同类型题目的 S0 阶段通过 `query_pack.py` 自动加载这些积累模式。

---

*CLC*
