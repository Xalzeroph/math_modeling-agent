# Kill Argument — 模型评价对抗审查

**执行角色**: 审稿手  
**时机**: 论文手完成初稿后（SOP Stage 7），在 claim-audit 和 citation-audit 之后  
**输入**: paper/main.tex（全篇，重点是模型评价章节）  
**输出**: `sessions/{name}/assurance/kill_argument.json` + `kill_argument.md`

---

## 为什么需要这个

标准审计（claim-audit, citation-audit）检查的是"每个数字是否对""每个引用是否真"。但存在一种失败模式：**每个局部都对，但论文整体过度销售**。

例如：
- 模型评价说"全面优于现有方法"，但实际只在 1 个数据集上测试
- 灵敏度分析说"模型稳定"，但只扰动了 ±5%（实际应该 ±20%）
- 结论章说"具有广泛适用性"，但假设条件很严格

这种问题不会被 claim-audit（数字本身是对的）或 citation-audit（引用是真的）捕获。需要专门攻击模型评价章节。

---

## 双 Thread 设计

审稿手分两步执行（两个独立的审稿 prompt，sequential）：

### Thread 1: 攻击者（Attack）

**角色**: 你是一个苛刻的数学建模竞赛评委。你的任务不是给 feedback，而是写一篇**拒稿理由**。

**攻击焦点**（选最致命的 1-2 条，不要列清单）:

1. **假设-结论不匹配**: 论文的假设是否太强，导致结论只在一个狭窄范围内成立？
2. **证据-声明 gap**: 模型评价所说的"优越性"有没有足够的对比实验支撑？
3. **范围过度声称**: "全面""显著""广泛"等修饰词有没有数据支撑？
4. **灵敏度不足**: 关键参数是否被充分讨论？最敏感参数的结论是否可靠？
5. **对比不公平**: 对比方法/基准是否合理？

**输出格式**:
```
## 攻击 memo（~200 字）

[单一论点，不列清单。写成一个连贯的拒稿段落，引用论文中的具体位置和数字。]
```

**约束**:
- 约 200 字，不超过 250
- 单一论点，写成一个完整段落
- 引用具体的 Section/Table/Equation
- 不 hedge——这是拒稿，不是"需要注意"
- 不参考任何之前的审计结果

### Thread 2: 裁决者（Adjudication）

**角色**: 你是一个独立的裁决者。你阅读攻击 memo + 论文原文，对攻击的每个子论点做出裁决。

**输入**: 攻击 memo（来自 Thread 1） + paper/main.tex

**任务**: 将攻击拆解为 3-7 个原子论点，然后逐一裁决：

| 裁决 | 含义 |
|------|------|
| `answered_by_current_text` | 论文已经回答了这一点（引用具体位置） |
| `partially_answered` | 部分回答，不足以完全反驳 |
| `still_unresolved` | 确实没回答 |

**输出格式**:
```
### 论点 P_N: [简标]

**攻击主张**: [~30 字]
**裁决**: answered_by_current_text | partially_answered | still_unresolved
**证据**: [引用论文中的具体位置，~50 字]
**如果未解决，严重性**: critical | major | minor
**如果未解决，建议修复**: [一句具体的可执行建议]

...

## 汇总
- answered_by_current_text: X
- partially_answered: Y
- still_unresolved: Z

## 净评估
[一段话：以当前论文的文本，能否挺过攻击 memo？诚实回答。]

## 优先行动项（最多 3 条）
1. ...
2. ...
3. ...
```

---

## 判决映射

| 条件 | 判决 | reason_code |
|------|------|-------------|
| still_unresolved 中有 critical | FAIL | unresolved_critical |
| still_unresolved 有 major/minor（无 critical） | WARN | unresolved_major_or_minor |
| partially_answered 中有 critical | WARN | partial_critical |
| 论文无模型评价章节或无可见过度销售 | NOT_APPLICABLE | no_overclaim_risk |
| 全部 answered | PASS | defense_survives |
| 审计执行失败 | ERROR | auditor_error |

---

## 输出

### kill_argument.json

```json
{
  "audit_skill": "kill-argument",
  "verdict": "WARN",
  "reason_code": "unresolved_major_or_minor",
  "summary": "攻击发现 1 处未解决的 major 问题：灵敏度只测了 ±5%",
  "generated_at": "ISO-8601",
  "details": {
    "attack_memo": "...",
    "decomposed_points": [
      {
        "id": "P_1",
        "label": "灵敏度范围不足",
        "attack_claim": "论文声称模型稳定但只测试了 ±5% 扰动",
        "verdict": "still_unresolved",
        "evidence": "sensitivity.md 中扰动范围为 ±5%，标准为 ±20%",
        "severity": "major",
        "recommended_fix": "扩展到 ±20% 扰动并更新 sensitivity.md"
      }
    ],
    "counts": {"answered": 2, "partial": 1, "unresolved": 1},
    "net_assessment": "..."
  }
}
```

---

## 关键规则

- Thread 1 和 Thread 2 必须独立——Thread 2 只看到攻击 memo 的文本，不知道 Thread 1 的思考过程
- 攻击必须 committed——选最致命的 1-2 条，不要列一堆 weak points
- 裁决者不要替论文辩护——如果确实没回答，就标 still_unresolved
- 不自动修改论文——只产出建议，用户决定是否改
- 当论文没有 overclaim 风险时（如纯粹的数值优化题），可以标 NOT_APPLICABLE
