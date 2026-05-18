# Code Audit — 代码完整性审计

**执行角色**: 审稿手  
**时机**: 编程手完成求解验证后（SOP Stage 5，Gate 2）  
**输入**: solvers/*.py + verifications/*.py + results/*.csv  
**输出**: `sessions/{name}/assurance/code_audit.json` + `code_audit.md`

---

## 为什么需要这个

编程手在 Stage 5 做了 verify（数值阈值检查）。但还有一类问题 verify 不覆盖：
- 约束是否**真的**满足（不是接近，是严格）
- 两个 solver 的结果是否**真的一致**
- 有没有定义了但没调用的死代码
- result 文件是否真的是 solver 生成的

---

## Step 1: 收集文件

```
solvers/problem*.py     — 求解代码
verifications/verify*.py — 验证脚本
results/*.csv           — 结果输出
notes/ProblemAnalysis.md — 约束定义
```

---

## Step 2: 审计协议

### A. 约束可行性验证

对优化模型，逐一核验约束：

```python
# 对每个约束，验证
assert 约束表达式 <= 容许误差，f"约束违反: {表达式} = {实际值}, 上限 = {上限}"
```

- 容许误差：线性约束 ≤ 1e-6，非线性 ≤ 1e-4
- FAIL 条件：任何约束明确违反

### B. 求解器交叉验证

如果同一个问题用了多个求解器（如 scipy + pulp）：
- 最优值差异是否 < 1%
- 如差异 > 1%：WARN，注明差异来源

如果只有 1 个 solver：NOT_APPLICABLE

### C. 死代码检测

- 扫描 `def` 和函数调用，找出定义但未调用的函数
- 注意区分：被 verify 脚本调用的工具函数不算死代码
- WARN 条件：发现死代码

### D. 结果文件溯源

- results/ 中的每个 .csv/.txt 文件是否由 solver 显式输出？
- 有没有结果文件引用了不存在的列名/路径？
- FAIL 条件：phantom results（结果文件存在但未被任何 solver 生成）

### E. 鲁棒性检查

- 如果有随机性（seed/sampling），不同 seed 下结果是否稳定？
- 对确定性算法，NOT_APPLICABLE
- 波动 > 5%：WARN

---

## Step 3: 判决

| 条件 | 判决 | reason_code |
|------|------|-------------|
| 全部通过 | PASS | all_checks_pass |
| 死代码或轻微鲁棒性问题 | WARN | minor_issues |
| 约束违反 / 幽灵结果 / 双 solver 不一致 | FAIL | integrity_violation |
| 无优化模型（如纯统计题） | NOT_APPLICABLE | no_optimization_code |
| 无 solver 文件 | BLOCKED | no_solvers_found |
| 审计失败 | ERROR | auditor_error |

---

## Step 4: 输出

### code_audit.json

```json
{
  "audit_skill": "code-audit",
  "verdict": "PASS",
  "reason_code": "all_checks_pass",
  "summary": "4 个 solver 全部通过约束验证，双求解器一致（差异 < 0.1%）",
  "audited_input_hashes": {
    "solvers/problem1_lp.py": "sha256:...",
    "results/cost.csv": "sha256:..."
  },
  "generated_at": "ISO-8601",
  "details": {
    "checks": {
      "constraint_feasibility": {"status": "PASS", "violations": 0},
      "solver_cross_validation": {"status": "PASS", "max_delta_pct": 0.08},
      "dead_code": {"status": "WARN", "functions": ["_debug_plot"]},
      "result_provenance": {"status": "PASS", "orphans": []},
      "robustness": {"status": "NOT_APPLICABLE"}
    }
  }
}
```

### code_audit.md

```markdown
# 代码审计报告

**日期**: YYYY-MM-DD
**审计者**: 审稿手
**Solver 数量**: 4

## 总体判决: PASS

## 各检查项

### A. 约束可行性: PASS
- 4 个 solver 全部约束满足

### B. 求解器交叉验证: PASS
- problem1_lp (scipy) vs problem1_pulp: 最优值差异 0.08%

### C. 死代码检测: WARN
- `_debug_plot()` 在 problem1_lp.py 中定义但从未调用

### D. 结果文件溯源: PASS
- 8 个结果文件全部由对应 solver 生成

### E. 鲁棒性: NOT_APPLICABLE
- 确定性算法，无需此检查
```

---

## 关键规则

- 只检查代码完整性，不评价算法选择是否合理（那是 idea-audit 的事）
- FAIL/BLOCKED 在 `assurance: submission` 时阻断
- 死代码只是 WARN，不阻断
