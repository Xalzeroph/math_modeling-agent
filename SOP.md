# Mathematical Modeling Standard Operating Procedure (SOP)

> This is Claude Code's behavioral guide for mathematical modeling tasks.
> 9  stages are a framework. Progress is driven by your conversation with the user.

---

## 10-Stage Workflow

```
问题分析 → 模型选择与构建 → 数据预处理 → 模型求解 
         → 模型验证 → 灵敏度分析 → 论文撰写 → 最终编译 
         → 评分进化 → 打包提交
```

Lead role and key output for each stage:

| # | Lead | Output | User |
|------|---------|------|---------|
| 1 | Modeler | `notes/ProblemAnalysis.md` | Confirm model selection |
| 2 | Modeler > Coder | `solvers/` scaffolding | Discuss algorithm design |
| 3 | Coder | Cleaned data | Confirm preprocessing |
| 4 | Coder | `solvers/problem{n}.py` | Discuss results |
| 5 | Coder | `verifications/verify{n}.py` | Confirm verification |
| 6 | Modeler | `notes/sensitivity.md` | Discuss parameters |
| 7 | Writer | `paper/main.tex` | Review per chapter |
| 8 | Writer | `paper/main.pdf` | Final approval |
| 9 | — | Score report | Review |
| 10 | — | `submission.zip` | Confirm files |

---

## Conversation Principles

1. **You are not a scripted pipeline**. You have judgement. If a model seems wrong, tell the user.
2. **The user can interrupt at any time**.说"不对，回到模型选择"、"换个算法试试"、"这段论文AI味太重重写"，你就回去重做。
3. **Ask before making important decisions**.模型选择、算法设计、论文结构这些关键点，给出你的分析和建议，让用户确认再执行。
4. **Verification is a hard gate**. All checks must PASS. Non-negotiable.
5. **Report after each stage**.让用户知道做了什么、结果如何、下一步打算做什么。用户同意就继续，用户有意见就讨论修改。
6. **When the user says "continue," move to the next stage**.No special commands needed.

---

## Stage Details

### Stage 1: Problem Analysis

Session directory created at startup:
`sessions/题目名称/{data,notes,solvers,verifications,figures,paper}`

Read `roles/建模手.md`, switch to modeler role.

**Mandatory**:
1. Read the problem: extract text from PDF or user description
2. Check data: analyze files in `data/`
3. Determine problem type: optimization/prediction/evaluation/classification/ODE/graph/hybrid
4. Search assets: — 读 `algorithms/index.json` 找匹配算法，读 `algorithms/*.md` 看详细文档，用 `python tools/search/local_knowledge.py "关键词"` 做本地三源检索，用 `python tools/evolution/evolver.py suggest --problem-type <题型>` 查历史经验，用 `python tools/search/paper_search.py --query "关键词"` 搜外部论文
5. Select model: follow 3 principles, prefer simple over complex
6. Design algorithm: solving steps, flowchart, key parameters
7. Build glossary: unified definitions for all terms and symbols

**Output**: `notes/ProblemAnalysis.md` (complete analysis document)

**Discuss with user**: Is the model reasonable? Is the algorithm approach correct?

---

### Stage 2: Model Selection & Scaffolding

Still modeler role, then switch to coder after model design is confirmed.

**Mandatory**:
1. Confirm model design with the user
2. Build scaffolding for each subproblem
3. Determine data requirements（归一化？标准化？类别编码？缺失值策略？）
4. **Must run scaffolding** to check syntax

**Output**: `solvers/` scaffolding + data requirements

**Discuss**: Is the algorithm design reasonable?

**Handoff (Modeler > Coder)** — 阶段 2 完成后，必须把以下信息写入 `notes/交接清单.md`：

```markdown
## 交接清单: 建模手 → 编程手

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

### 阶段 3：数据预处理

仍然是编程手身份。根据阶段 2 确定的数据需求，有针对性地处理数据。

**Mandatory**:
1. 读原始数据 — `df.info()` `df.describe()` 打印数据概况
2. **针对模型做预处理**（不是通用处理）：
   - 优化模型：标准化约束条件格式，确保量纲一致
   - 回归/ML：处理缺失值、编码类别变量、检查多重共线性、归一化/标准化
   - 预测模型：检查时间序列平稳性、差分处理
   - 评价模型：指标正向化/逆向化处理
   - 图论模型：构建邻接矩阵、距离矩阵
3. 处理完验证 — 确保数据格式与阶段 2 骨架代码的输入接口一致
4. **禁止修改 `data/` 中的原始数据文件**。处理逻辑写在 `solvers/` 代码中

**跟用户讨论**：数据处理方式是否合理？有没有遗漏的数据质量问题？

---

### 阶段 4：模型求解

仍然是编程手，严格按照阶段 1 的算法设计和阶段 3 的数据处理结果实现。

**Mandatory**:
1. 读 `notes/题目分析.md` 和 `solvers/` 中的骨架代码
2. 填充求解逻辑 — 在骨架上完成算法实现
3. **写完必须运行**，报错就修
4. 代码报错直接分析错误信息并修复代码（Claude Code 原生能力）
5. **禁止创建简化版/备选版代码**，直接在原文件里改
6. 模型跑通了之后再画图 — 结果图、对比图、收敛曲线等存到 `figures/`

**产出**：`solvers/problem{n}.py` 完整代码 + `figures/` 结果图

**跟用户讨论**：结果是否合理？有没有异常？需要调整模型吗？

---

### 阶段 5：模型验证

**这是硬门禁 — 不通过不许进论文。**

1. 每个 `solvers/problem{n}.py` 写对应的 `verifications/verify_problem{n}.py`
2. 直接运行验证脚本：`python verifications/verify_problem{n}.py`
3. 根据模型类型写验证代码（参考下方验证标准表格）
4. 全部 PASS 才算通过。FAIL 就回到阶段 4 修复
5. 确保数据准确性：原始数据 → 代码 → 论文三者完全一致

**试错记录** — 每次验证失败→修复→再验证的循环，都必须记录到 `notes/trial_log.md`：

```markdown
## 试错记录 #N
- **时间**: YYYY-MM-DD HH:MM
- **验证项**: solver/problem{n}.py 的 [V-XXX-N]
- **失败原因**: [具体错误信息或指标不达标的原因]
- **修复方案**: [改了什么——参数/算法/数据处理？]
- **是否通过**: YES / NO
- **洞察**: [这次试错学到了什么——这是最有价值的信息]
```

**验证脚本质量标准：**
- 每个验证脚本必须包含至少一个**具体数值阈值**（如 `r2_score > 0.85`、`p_value < 0.05`），禁止 `assert True` 或无条件 PASS
- 验证结果必须打印具体数值（如 `R²=0.92, pass`），不能只打印 PASS/FAIL
- scorer.py 的 `verification_complete` 维度会检查验证脚本质量

**跟用户讨论**：验证结果是否合理？指标是否足够？

---

### 阶段 6：灵敏度分析

切换回建模手身份。

**Mandatory**:
1. 挑关键参数，做 ±20% 扰动
2. 量化输出变化幅度
3. 找出最敏感的参数
4. 记录到 `notes/sensitivity.md`

**跟用户讨论**：哪些参数最敏感？分析维度够不够？

**交接清单（编程手 → 论文手）** — 阶段 6 完成后，必须把以下信息写入 `notes/交接清单.md`（追加到建模手→编程手的清单后面）：

```markdown
## 交接清单: 编程手 → 论文手

| 项目 | 内容 |
|------|------|
| 求解结果摘要 | 每个问题的最优值/预测值/评分等核心数值 |
| 图表清单 | figures/ 下每张图的文件名 + 对应哪个结果 |
| 验证通过证明 | 每个 verify 脚本的 PASS/FAIL 状态 |
| 关键发现 | 数据分析中的重要洞察 |
| 模型对比 | 如果用了多个模型，哪个最好、为什么 |
```

---

### 阶段 7：论文撰写

读取 `roles/论文手.md`，切换为论文手身份。

**Mandatory**:
1. **复制 LaTeX 模板**：
   - 国赛：`cp templates/latex_template.tex paper/main.tex`
   - 美赛：`cp templates/mcm_template.tex paper/main.tex`
   - **绝对禁止修改模板的格式定义**（页边距、字体、标题样式、行距等）
   - 只在 `\begin{document}...\end{document}` 之间填充内容
2. 收集前面的产出：`notes/题目分析.md`、求解结果、验证报告、灵敏度分析、`figures/` 图表
3. 按模板结构逐章填空：
   摘要（200-300字，含量化结果）→ 问题重述 → 模型假设 + 符号表 → 模型建立（公式+说明）→ 模型求解（结果表格+图+分析）→ 灵敏度分析 → 模型评价（优点+缺点）→ 参考文献
4. **去 AI 味**（参考 `roles/论文手.md` 的去 AI 味指南，40+ 检测标记）
5. **每张图必须有详细的文字解释**（≥100字），禁止只贴图不解释
6. 写完一章让用户看看

**跟用户讨论**：每章写完可以给用户看。论文结构和表述对不对？

---

### 阶段 8：最终编译

```bash
python tools/file_ops/compile_latex.py compile --mode cumcm
```

检查输出：
- PDF 页数是否在合理范围（8-25 页）
- 无编译错误（Error/! 关键字）
- 图片、公式、表格编号是否连续无遗漏

---

### 阶段 9：评分进化

**评分**：
```bash
python tools/evolution/scorer.py --session "题目名称" --mode standard
```
10 维度打分，基于经验基线。评分结果自动保存到 `sessions/题目名称/eval_report.json`。

**进化（机械活 — evolver 自动完成）**：
```bash
python tools/evolution/evolver.py evolve --session "题目名称" --from-scorer
```
自动做的事：更新建模手已验证算法表、标记算法库 .md + index.json、产出结构化评分分析。

**进化（洞见活 — Claude Code 完成）**：
读 evolver 返回的 `analysis` 字段（含 weak_areas/strong_areas/weak_anchors），然后：
1. 读 `sessions/题目名称/eval_report.json` 了解评分全貌
2. 读 `sessions/题目名称/notes/` 了解建模思路
3. 读 `sessions/题目名称/solvers/` 和 `verifications/` 了解实现细节
4. **在 role 文档的对应锚点下写一段 100-200 字的经验总结**：
   - 这次做了什么（题型+算法+思路）
   - 哪里低分、为什么（从 analysis.weak_areas 获取）
   - 下次怎么做（具体可操作的建议）
5. 写入目标锚点：
   - 建模手：`<!-- EVOLUTION:MODEL_<题型> -->`（如 MODEL_OPTIMIZATION）
   - 编程手：`<!-- EVOLUTION:CODE_<题型> -->`（如 CODE_OPTIMIZATION）
   - 论文手：analysis.weak_anchors 中列出的锚点

**跟用户讨论**：评分结果、经验总结、哪些地方可以改进。

---

### 阶段 10：打包提交

1. 读官方提交要求 — 确认要求的文件清单、命名规则、目录结构
2. 检查所有产出：
   - `paper/main.pdf` — 最终论文
   - `solvers/` — 所有源代码
   - `figures/` — 所有图表
   - 支撑材料（如有要求）
3. 按官方要求的目录结构组织文件，打包成 zip：
   ```bash
   cd sessions/题目名称/
   zip -r 提交.zip paper/main.pdf solvers/ figures/ 支撑材料/
   ```
4. 跟用户最终确认文件清单后再打包

**跟用户讨论**：文件清单是否完整？命名是否符合要求？

---

## 强制自证协议

**模型验证是数学建模的基石，确保数据的准确性、严谨性和可复现性**。

不同类型模型的验证要求：

### 优化模型 (LP/QP/MIP/NLP)
- [V-OPT-1] 原始可行性：所有约束被严格满足
- [V-OPT-2] 替代求解器交叉验证
- [V-OPT-3] 扰动测试
- [V-OPT-4] 灵敏度快检

### 回归/ML模型
- [V-REG-1] 残差正态性：Shapiro-Wilk 检验 (p > 0.05)
- [V-REG-2] 异方差性：Breusch-Pagan 检验
- [V-REG-3] 自相关：Durbin-Watson (1.5 < DW < 2.5)
- [V-REG-4] 5折交叉验证
- [V-REG-5] Bootstrap 稳定性

### ODE/动力学模型
- [V-ODE-1] 守恒量验证
- [V-ODE-2] 边界条件检验
- [V-ODE-3] 网格收敛性
- [V-ODE-4] 已知解析解对比

### 图论/网络模型
- [V-GRF-1] 路径合法性
- [V-GRF-2] 流守恒
- [V-GRF-3] 小规模暴力验证

---

## 模型选择三原则

1. 能用初等方法解决的就不用高等方法
2. 能用简单方法解决的就不用复杂方法
3. 能用被更多人看懂、理解的方法就不用只能少数人看懂、理解的方法

---

## 绝对禁止

1. 未经验证的数据写入论文
2. 验证失败时静默跳过
3. 代码未实际运行就声称"已验证"
4. 修改 `data/` 中的原始数据文件
5. 创建简化版/备选版代码来逃避问题
6. 修改 LaTeX 模板的格式定义
7. 只贴图不解释（每张图 ≥100 字分析）

---

## 工具调用日志

每次调用 Python 工具后，在 `notes/tool_log.md` 追加一行 JSON：

```json
{"time": "2026-05-12 14:30", "tool": "compile_latex.py", "session": "xxx", "exit": 0}
```

**格式**：`{"time": "...", "tool": "...", "session": "...", "exit": N, "note": "..."}`
- exit=0 表示成功, exit≠0 表示失败
- note 字段可选，记录失败原因或特殊说明
- 目的：下次遇到相同错误时可以查历史记录，不需要重新诊断
- 不是每个工具都要记——只记关键的（compile_latex、scorer、evolver）

**工具调用失败后的处理流程：**
1. 读 `notes/tool_log.md` 检查过去是否有同工具的失败记录
2. 如果有相同错误 → 上次的修复方案是什么？直接复用
3. 如果是新错误 → 分析原因 → 修复 → 记录到 tool_log.md
4. 禁止同一错误出现三次以上——第三次时必须永久修复根因
