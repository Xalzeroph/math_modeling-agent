# Proof Checker — 公式推导验证

**执行角色**: 审稿手  
**时机**: 建模手完成模型设计后（SOP Stage 2，Gate 1）  
**输入**: notes/ProblemAnalysis.md（公式推导部分）+ 建模分析文档  
**输出**: `sessions/{name}/assurance/proof_audit.json` + `proof_audit.md`

---

## 适用场景

数学建模论文中的公式推导验证，包括：
- AHP 层次分析法的一致性检验
- 优化模型的 KKT 条件
- 迭代算法的收敛性论证
- 统计检验的假设条件
- 任何从假设到结论的推导链

---

## 问题分类（简化自 ARIS Proof Checker 的 20 类 → 适合数学建模的 8 类）

### Group A: 逻辑结构

| 类别 | 描述 | 例子 |
|------|------|------|
| **UNJUSTIFIED_STEP** | 推导步骤无理由 | "显然可得"但没有说明为什么 |
| **MISSING_CASE** | 漏了边界/退化情况 | 分母可以是 0 的情况没讨论 |
| **QUANTIFIER_ERROR** | 量词顺序错误 | "对所有参数存在最优" vs "存在最优对所有参数" |
| **CIRCULAR** | 循环论证 | 用结论证明前提 |

### Group B: 数学正确性

| 类别 | 描述 | 例子 |
|------|------|------|
| **ALGEBRA_ERROR** | 代数运算错误 | 展开/因式分解错误 |
| **DOMAIN_ERROR** | 函数域不匹配 | log(负数)、除以 0 |
| **ASSUMPTION_VIOLATION** | 使用定理但前提不满足 | 用正态检验但数据非正态 |
| **MISSING_CONDITION** | 推导使用了未声明的条件 | 假设了对称性但未写出 |

---

## Step 1: 自底向上构建

建模手应该已经写了推导。审稿手逐条检查：

### 1.1 符号完整性

遍历每个公式，检查：
- 每个符号是否在术语表中定义
- 同一符号是否在不同地方有不同含义（symbol drift）

### 1.2 推导链完整性

对每个"因此""由此可得""显然"，检查：
- 前面的公式是否逻辑上蕴涵后面的？
- 如果跨度超过 1 步，中间是否缺了关键推导？

### 1.3 AHP 特检

如果用了 AHP：
- 判断矩阵是否标注
- 一致性检验：CI 和 CR 的计算过程是否可复现
- CR < 0.1 是否真的满足（重新计算一遍）

### 1.4 KKT 特检

如果用了优化模型：
- 列写拉格朗日函数
- 逐一检查 KKT 条件（stationarity + primal feasibility + dual feasibility + complementary slackness）
- 最优解是否真的满足全部 4 个条件

### 1.5 收敛性特检

如果用了迭代算法（GA/PSO/SA）：
- 是否给定了收敛判据？
- 如果声称"收敛到全局最优"，有没有论证（metropolis/elitism/等）？
- 收敛曲线是否合理（不是"收敛到"凭空数字）？

---

## Step 2: 判决

| 条件 | 判决 | reason_code |
|------|------|-------------|
| 全部推导完整，所有条件满足 | PASS | all_proofs_valid |
| Minor issues（标注不清但不影响结论） | WARN | minor_clarity_issues |
| 推导有 gap 或重大错误 | FAIL | proof_gap_or_error |
| 论文中无公式推导（纯叙述） | NOT_APPLICABLE | no_formal_proofs |
| 无建模分析文档 | BLOCKED | no_analysis_doc |
| 审计失败 | ERROR | auditor_error |

---

## Step 3: 输出

### proof_audit.json

```json
{
  "audit_skill": "proof-checker",
  "verdict": "WARN",
  "reason_code": "minor_clarity_issues",
  "summary": "公式推导总体正确，2 处符号未定义，1 处跳步",
  "audited_input_hashes": {
    "notes/ProblemAnalysis.md": "sha256:..."
  },
  "generated_at": "ISO-8601",
  "details": {
    "total_checks": 15,
    "issues": [
      {
        "location": "Eq.(3)",
        "category": "MISSING_CONDITION",
        "severity": "minor",
        "description": "符号 α 在 Eq.(3) 中首次使用但未在术语表中定义"
      }
    ]
  }
}
```

### proof_audit.md

```markdown
# 公式推导审计报告

**日期**: YYYY-MM-DD
**审计者**: 审稿手

## 总体判决: WARN

## 问题清单

### [WARN] Eq.(3): 符号 α 未定义
- **严重性**: minor
- **类别**: MISSING_CONDITION
- **修复**: 在术语表中添加 α = 学习率，取值 0.01

### [WARN] Eq.(5)→Eq.(6): 跳步
- **严重性**: minor
- **类别**: UNJUSTIFIED_STEP
- **描述**: "显然可得"跨越了 2 步，需要补充中间推导
- **修复**: 展开括号，补充因式分解步骤

## 所有检查通过项
- Eq.(1)-(2): 推导完整，符号已定义
- Eq.(4): Lagrange 函数正确
- KKT 条件 4 项全部满足
```

---

## 关键规则

- 审稿手重新计算一遍 CR、KKT 等关键检验（不信任建模手的计算）
- Minor 问题标 WARN 不阻断，Major/Fatal 标 FAIL
- 符号表缺陷是建模手的事——只报告，不帮补
