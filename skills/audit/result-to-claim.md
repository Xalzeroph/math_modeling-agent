# Result-to-Claim — 结果→论断映射

**执行角色**: 审稿手（审查编程手起草的映射表）  
**时机**: 编程手完成求解验证后（SOP Stage 5，Gate 2）  
**输入**: results/*.csv + verifications/verify*.py + notes/ProblemAnalysis.md  
**输出**: `sessions/{name}/assurance/claim_map.md`（编程手起草，审稿手验证）

---

## 核心问题

编程手求解完得到了数值。审稿手要回答：这些数值**到底支撑什么论断**？

- "最优值 = 1256.3 万" → 支撑"方案 A 优于方案 B" 吗？（需要对比数据）
- "R² = 0.92" → 支撑"模型拟合良好"吗？（需要对比基准 R²）
- "精度 = 97%" → 支撑"模型优秀"吗？（需要和同类方法比较）

---

## Step 1: 审稿手验证清单

### A. 每个问题是否都有明确的结果输出？

| 检查 | 通过标准 |
|------|---------|
| 最优值/预测值/评分是否明确 | results/ 中有对应文件和数值 |
| 是否给出了对比基准 | 至少一个 baseline 对比 |
| 是否讨论了不确定性 | 置信区间/误差范围/seed 波动 |

### B. 每条结果支持的论断是否恰当？

| 检查 | 通过标准 | 反例 |
|------|---------|------|
| 因果 vs 相关 | 数值上升 ≠ 证明因果 | "A 增加导致 B 增加"（实际只有相关性） |
| 显著性 | 差距小（<2%）不能声称"显著优于" | "显著提升"只有 0.3% 差距 |
| 泛化 | 单数据点不能声称"普遍规律" | 只有 1 组对比就说"全面超越" |

### C. 哪些论断缺少证据支撑？

| 类型 | 例子 |
|------|------|
| 论文声称但 results/ 中无对应 | "模型鲁棒性高"但没有 multi-seed 数据 |
| 需要额外实验支撑 | "推广到更大场景"但没有 scale 测试 |
| 逻辑跳跃 | "因此适用于任何优化问题"（只有一个实例） |

---

## Step 2: 判决

| 条件 | 判决 | reason_code |
|------|------|-------------|
| 所有结果都有对应论断，全部科学支撑 | PASS | all_claims_supported |
| 部分论断 mildly overstated | WARN | minor_overstatement |
| 论断与结果严重不符 / 编造 | FAIL | unsupported_claims |
| 无 results/ 目录或空白 | BLOCKED | no_results |
| 审计失败 | ERROR | auditor_error |

---

## Step 3: 输出

### claim_map.md（编程手起草模板，审稿手填充判决）

```markdown
# 结果→论断映射表

**日期**: YYYY-MM-DD

## 问题 1

| # | 论文论断 | 来源 Solver | 结果文件 | 结果值 | 支撑程度 | 审稿手判决 |
|---|---------|------------|---------|--------|---------|-----------|
| 1 | 最优成本 1256.3 万 | problem1_lp.py | results/cost.csv | 1256.284 | supported | PASS |
| 2 | 比方案 A 优 15.3% | problem1_lp.py | results/compare.csv | 12.8% | partial | WARN — 数字不匹配 |
| 3 | 模型适用于大规模场景 | — | — | — | unsupported | FAIL — 无 scale 测试数据 |

## 问题 2
...
```

---

## 关键规则

- 审稿手不生成 claim_map.md（编程手起草），只审查和修正
- "科学地支撑" 的标准：因果需要控制变量 / 相关需要统计显著 / 泛化需要多数据集
- 无结果的论断必须标 unsafe_claimed，不能装看不见
- FAIL/BLOCKED 在 `assurance: submission` 时阻断
