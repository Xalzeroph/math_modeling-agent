# Paper Claim Audit — 论文数字核对

**执行角色**: 审稿手  
**时机**: 论文手完成初稿后（SOP Stage 7）  
**输入**: paper/main.tex + results/*.csv + verifications/*.py  
**输出**: `sessions/{name}/assurance/claim_audit.json` + `claim_audit.md`

---

## 核心理念

**零上下文审查**。审稿手只看两样东西——论文 .tex 和原始结果文件。不读建模分析文档，不读求解代码，不知道"作者意图"。只做一件事：论文里的每个数字，和结果文件一致吗？

这比"独立审查"更严格——审稿手连上一步做了什么都不知道。

---

## Step 1: 收集文件（只收集路径，不读内容）

### 论文文件（claims）
```
paper/main.tex
paper/sections/*.tex（如果存在）
```

### 结果文件（evidence）
```
results/*.csv
results/*.txt
sessions/{name}/assurance/claim_map.md
```

### 排除（不看）
```
notes/ProblemAnalysis.md
notes/sensitivity.md
notes/trial_log.md
notes/交接清单.md
solvers/*.py
verifications/*.py（只看其中的数值输出，不看逻辑）
```

---

## Step 2: 审计协议（审稿手 persona 执行）

以审稿手身份阅读论文和结果，逐条执行以下协议：

### A. 提取每一条量化论断

扫描 paper/main.tex，找出所有包含数值的句子：
- 位置（section / table / figure caption）
- 精确引用原句
- 声称的数值

### B. 逐一追溯证据

对每条提取的论断，在结果文件中找对应数值：
- 哪个结果文件包含这个数？
- 文件里精确的值是多少？
- 匹配状态：`exact_match` / `rounding_ok` / `mismatch`

**四舍五入规则**：只有标准四舍五入到显示精度才允许。84.7% 写成 85% OK。84.7% 写成 85.3% **NOT OK**。

### C. 检查以下 7 种失败模式

1. **数字膨胀**: 论文说 85.3%，文件里是 84.7%
2. **最优种子挑选**: 论文说"平均 90.2%"，但只是 5 次中的最佳
3. **参数不一致**: 论文说用了参数 α=0.08，但 solver 代码里是 α=0.1
4. **聚合不匹配**: 论文说"平均 5 次"，但结果文件只有 3 次
5. **差值计算错误**: 论文说"提升 15%"，实际 (85.3-73.1)/73.1=16.7%
6. **图表标题不匹配**: Figure caption 描述的和图表数据不一致
7. **范围过度声明**: 论文说"全面超越"，但只测了 1 个数据集/1 个场景

---

## Step 3: 撰写报告

### claim_audit.json (machine-readable)

```json
{
  "audit_skill": "paper-claim-audit",
  "verdict": "PASS | WARN | FAIL | NOT_APPLICABLE | BLOCKED | ERROR",
  "reason_code": "all_numbers_match | rounding_drift | claim_mismatch | no_numeric_claims | no_raw_evidence",
  "summary": "One-line verdict summary in Chinese",
  "audited_input_hashes": {
    "main.tex": "sha256:...",
    "results/cost.csv": "sha256:..."
  },
  "generated_at": "ISO-8601",
  "details": {
    "total_claims": 24,
    "counts": {
      "exact_match": 18,
      "rounding_ok": 3,
      "ambiguous_mapping": 1,
      "mismatch": 2
    },
    "per_claim": [
      {
        "claim_id": 1,
        "location": "Section 6, paragraph 2",
        "paper_text": "最优总成本为 1256.3 万元",
        "claimed_value": 1256.3,
        "evidence_file": "results/problem1_cost.csv",
        "evidence_value": 1256.284,
        "status": "rounding_ok",
        "details": "四舍五入可接受（1256.284→1256.3）"
      }
    ]
  }
}
```

### 判决映射

| 输入状态 | 判决 | reason_code |
|---------|------|-------------|
| 论文中无数值论断 | NOT_APPLICABLE | no_numeric_claims |
| 有论断但无结果文件 | BLOCKED | no_raw_evidence |
| 全部匹配 | PASS | all_numbers_match |
| 仅有四舍五入差异 | WARN | rounding_drift |
| 任何实质性不匹配 | FAIL | claim_mismatch |
| 审计执行失败 | ERROR | auditor_error |

### claim_audit.md (human-readable)

```markdown
# 论文数字审计报告

**日期**: YYYY-MM-DD
**审计者**: 审稿手（零上下文）
**论文**: [从 tex 提取标题]

## 总体判决: [PASS | WARN | FAIL]

## 统计
- 总论断数: N
- 精确匹配: X
- 四舍五入 OK: Y
- 模糊映射: Z
- ⚠️ 不匹配: W

## 不匹配详情

### [FAIL] 论断 #N: [简述]
- **位置**: Section X / Table Y
- **论文说**: "..."
- **实际证据**: ...
- **状态**: mismatch
- **修正建议**: ...

## 全部论断明细

| # | 位置 | 论文值 | 证据值 | 状态 |
|---|------|--------|--------|------|
| 1 | Section 6 | 1256.3 | 1256.284 | rounding_ok |
```

---

## 关键规则

- 审稿手只读 paper/.tex + results/，不看任何中间文档
- `NOT_APPLICABLE` 也必须写入 artifact——不能静默跳过
- FAIL/BLOCKED 在 `assurance: submission` 时必须阻断流程
- SHA256 哈希所有审计输入，gate.py 通过对比哈希检测 stale artifact
- 网络/执行失败标 `ERROR`，不标 FAIL
