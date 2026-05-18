# Result-to-Claim 映射表

| 论文论断 | 来源 Solver | 结果文件 | 关键数值 | 支撑程度 | 缺口 |
|---------|------------|---------|---------|---------|------|
| 省域碳排放综合排名 | problem1_evaluation.py | results/p1_evaluation.csv | 北京 C=0.9953 (#1), 内蒙古 C=0.0258 (#30) | supported | 分类标签为英文(High-High等)，中文论文需翻译 |
| 熵权法指标权重 | problem1_evaluation.py | 终端输出 + figures/p1_weight.svg | 碳生产率0.3614, 经济协调度0.3614, 总量0.1442, 人均0.0696, 强度0.0633 | supported | 生产率和协调度权重相同，需解释是否合理 |
| 最优聚类数 k=2 | problem1_evaluation.py | 终端输出 | silhouette=0.7623 | supported | k=2 将北京单独分为一类，其余29省为另一类，区分度可能不足 |
| STIRPAT 因素分解 | p2_model.py | results/p2_stirpat_model.txt | b=1.000, c=1.000, d=1.000, R²=1.000 | partial | 系数全为1是因为 Kaya 恒等式，非真实弹性系数。建议补充文献对比值 |
| 碳排放驱动因素识别 | p2_model.py | 终端输出 + figures/p2_stirpat.svg | 人均GDP+0.9778相关, 碳强度-0.9532相关 | partial | 描述性相关分析，非因果推断 |
| 三情景预测 | p3_scenario.py | results/baseline_bau.csv, carbon_reduction.csv, enhanced_reduction.csv | BAU 2045→14833Mt, CR 2028→12024Mt, ER 2026→11804Mt | supported | 缺少置信区间/不确定性范围 |
| 碳达峰时间与峰值 | p3_scenario.py | results/p3_summary.json | CR 达峰2028年(12024Mt), ER 2026年起持续下降 | partial | BAU 在2045年仍未达峰，Enhanced 在2026年即开始下降(实际峰值在2025前) |

## 未覆盖的论断
- 问题4（政策建议）当前仅在终端打印，未有结构化结果文件 → 需补充
- 省域碳排放空间差异分析未有统计检验（如 Moran's I）
- 各因素对碳排放的贡献度分解未有定量结果（如 LMDI 分解）
- 三情景的关键参数假设缺少单独的存档文件
