# Citation Audit — 引用真实性验证

**执行角色**: 审稿手  
**时机**: 论文手完成初稿后（SOP Stage 7），在 paper-claim-audit 之后  
**输入**: paper/main.tex + references.bib（或内嵌 \bibitem）  
**输出**: `sessions/{name}/assurance/citation_audit.json` + `citation_audit.md`

---

## 三层验证链

逐层 fallback，任一层确认为真即可停止：

1. **arXiv API** — 按 arXiv ID 查询 `http://export.arxiv.org/api/query?id_list={id}`
2. **CrossRef API** — 按 DOI 查询 `https://api.crossref.org/works/{doi}`
3. **Semantic Scholar** — 按标题模糊匹配 `https://api.semanticscholar.org/graph/v1/paper/search?query={title}`（阈值 0.6）
4. **Web 搜索** — 如果三层都失败，用 WebSearch 直接搜索标题

---

## Step 1: 发现 bib 和引用

1. 定位 bib 文件：`references.bib` 或 `paper/*.bib` 或内嵌 `\bibitem`
2. 提取所有 `\cite{key}` 的上下文（周围 1 句完整文本）
3. 建立两个集合：
   - `cited_keys`: 论文中实际被引用的 cite key
   - `bib_keys`: bib 文件中定义的 key
   - `bib_keys \ cited_keys`: 只在 bib 中但没被引用的（可选检查）

---

## Step 2: 逐条审计（审稿手 persona 执行）

对每个**被引用的** cite key，读取 bib 条目 + 引用上下文，执行三层检查：

### 2.1 存在性检查

| 方法 | 何时用 |
|------|--------|
| arXiv API | bib 有 `archivePrefix = {arXiv}` 或 `eprint` |
| CrossRef | bib 有 `doi` |
| Semantic Scholar | 只有标题，没有 arXiv ID 或 DOI |
| WebSearch | 以上三层都失败或没覆盖 |

**输出**: 验证状态 + 验证 URL
- `verified` — 确认存在
- `unverified` — 所有层都找不到
- `verify_pending` — 网络瞬时失败（**不计入幻觉率**）

### 2.2 元数据正确性

对比 bib 字段与权威源：
| 字段 | 检查方法 |
|------|---------|
| 作者 | arXiv author == bib author？顺序、拼写 |
| 年份 | arXiv published year == bib year？ |
| 会议/期刊 | arXiv 对应的是 preprint 还是已发表版本？ |
| 标题 | 标题是否一致（允许微小差异如大小写） |

### 2.3 上下文恰当性

对每个 `\cite{X}` 的引用位置，检查：
- 被引论文是否真的**支撑**了引用处的论断？
- 是否存在"引用了但不相关"的情况？
- 是否存在"明明是 A 说的却引用成 B"的情况？

---

## Step 3: 判决

### 每条引用判决

| 判决 | 含义 | 行动 |
|------|------|------|
| **KEEP** | 条目正确，所有引用恰当 | 无 |
| **FIX** | 元数据需修正，引用恰当 | 修正 bib 条目 |
| **REPLACE** | 引用上下文错误 | 找正确的论文替换，或改写句子 |
| **REMOVE** | 引用是编造的或根本不支持 | 删除引用 + 删除支撑声明 |

### 总体判决映射

| 条件 | 判决 | reason_code |
|------|------|-------------|
| 无引用或 bib | NOT_APPLICABLE | no_citations |
| bib 不可读 | BLOCKED | bib_unreadable |
| 全部 KEEP | PASS | all_entries_keep |
| 仅有 FIX | WARN | metadata_drift |
| 任何 REPLACE 或 REMOVE | FAIL | wrong_context_or_hallucinated |
| 审计执行失败 | ERROR | auditor_error |

---

## Step 4: 输出

### citation_audit.json

```json
{
  "audit_skill": "citation-audit",
  "verdict": "WARN",
  "reason_code": "metadata_drift",
  "summary": "15 条引用中 11 KEEP, 4 FIX（元数据修正）",
  "audited_input_hashes": {
    "references.bib": "sha256:...",
    "main.tex": "sha256:..."
  },
  "generated_at": "ISO-8601",
  "details": {
    "total_entries": 15,
    "counts": {"KEEP": 11, "FIX": 4, "REPLACE": 0, "REMOVE": 0},
    "per_entry": [
      {
        "key": "saaty1980ahp",
        "verdict": "KEEP",
        "existence": "verified",
        "metadata": "correct",
        "context": "SUPPORTS",
        "uses": [{"file": "main.tex", "line": 42, "verdict": "SUPPORTS"}]
      }
    ]
  }
}
```

### citation_audit.md

```markdown
# 引用审计报告

**日期**: YYYY-MM-DD
**Bib 文件**: references.bib
**总条目**: 15

## 汇总
| 判决 | 数量 |
|------|------|
| KEEP | 11 |
| FIX | 4 |
| REPLACE | 0 |
| REMOVE | 0 |

## 优先修复

### FIX: saaty1980ahp
- 年份应为 1980，bib 中写为 1990
- ACTION: 修正 year 字段

...
```

---

## 关键规则

- 网络瞬时失败标 `verify_pending`，**不计入幻觉率**
- REPLACE/REMOVE 需要人工确认后才修改
- 上下文恰当性 > 元数据正确性（引用错误使用比拼写错误更危险）
- 不引用自己没读过的论文——如果需要验证上下文，去读论文原文
