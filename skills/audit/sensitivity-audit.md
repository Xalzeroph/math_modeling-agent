# Sensitivity Audit — 灵敏度分析审计

**执行角色**: 审稿手  
**时机**: 建模手完成灵敏度分析后（SOP Stage 6 之后、Stage 7 之前）  
**输入**: notes/sensitivity.md + solvers/*.py（确认参数来源）  
**输出**: `sessions/{name}/assurance/sensitivity_audit.json`

---

## 为什么需要这个

灵敏度分析是美赛 O 奖论文 100% 包含的内容。但常见问题：
- 只分析了 1-2 个参数 → 不全面
- 只定性描述（"模型稳定"）→ 缺定量数据
- 扰动幅度太小（±5%）→ 不足以说明鲁棒性
- 没找出最敏感参数 → 缺少关键洞察

---

## Step 1: 审计清单

### A. 参数数量

| 条件 | 判决 |
|------|------|
| ≥3 个关键参数 | PASS |
| 2 个 | WARN |
| 0-1 个 | FAIL |

**关键参数的定义**: 建模手在模型设计中指定的核心参数（如学习率、惩罚系数、权重因子），不是求解器的超参数。

### B. 扰动幅度

| 条件 | 判决 |
|------|------|
| ±20% 或更宽 | PASS |
| ±10% | WARN |
| < ±10% | FAIL |

### C. 定量化程度

| 条件 | 判决 |
|------|------|
| 每个参数有 % 变化幅度 | PASS |
| 部分参数只有定性描述 | WARN |
| 全部只说"稳定""影响小"无数字 | FAIL |

### D. 最敏感参数

| 条件 | 判决 |
|------|------|
| 明确标识 + 讨论实际含义 | PASS |
| 标识了但未讨论 | WARN |
| 完全未标识 | FAIL |

### E. 多参数分析（加分项）

| 条件 | 判决 |
|------|------|
| 做了联合扰动/LHS | PASS（但不必需，无 → NOT_APPLICABLE） |
| 只做 OAT | NOT_APPLICABLE（可接受） |

---

## Step 2: 判决

| 条件 | 判决 | reason_code |
|------|------|-------------|
| 全部达标 | PASS | all_checks_pass |
| 1-2 项 WARN（如参数少 1 个、扰动窄了） | WARN | minor_issues |
| 任何 FAIL 项 | FAIL | insufficient_sensitivity |
| 无 sensitivity.md 文件 | BLOCKED | no_sensitivity_analysis |
| 审计失败 | ERROR | auditor_error |

---

## Step 3: 输出

```json
{
  "audit_skill": "sensitivity-audit",
  "verdict": "WARN",
  "reason_code": "minor_issues",
  "summary": "灵敏度分析基本合格：3 个参数 ±20%，定量明确。但只做了 2 个参数，标准要求 ≥3",
  "audited_input_hashes": {
    "notes/sensitivity.md": "sha256:..."
  },
  "generated_at": "ISO-8601",
  "details": {
    "checks": {
      "parameter_count": {"status": "WARN", "actual": 2, "required": 3},
      "perturbation_range": {"status": "PASS", "range": "±20%"},
      "quantification": {"status": "PASS"},
      "most_sensitive_identified": {"status": "PASS", "parameter": "α"},
      "multi_param_analysis": {"status": "NOT_APPLICABLE"}
    }
  }
}
```

---

## 关键规则

- 灵敏度审计在 Stage 6 之后执行（不在 Gate 2）
- ±5% 的扰动不能证明"模型稳定"
- "显著变化"没有数字 = FAIL，必须有 % 
- 多参数联合分析是加分项，不强制
