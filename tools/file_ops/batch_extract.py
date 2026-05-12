#!/usr/bin/env python3
"""批量论文统计 — 从PDF中提取页数、字数、图表数、公式数、参考文献数量"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "algorithms").exists():
            return d
        d = d.parent
    return Path.cwd()


def extract_pdf_stats(pdf_path: Path) -> dict:
    """从单个PDF提取统计指标"""
    try:
        import pdfplumber
    except ImportError:
        return {"error": "需要 pdfplumber: pip install pdfplumber"}

    stats = {
        "file": str(pdf_path.name),
        "pages": 0,
        "chars": 0,
        "figures": 0,
        "tables": 0,
        "equations": 0,
        "references": 0,
        "sections": 0,
        "error": None,
    }

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            stats["pages"] = len(pdf.pages)
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            if not full_text.strip():
                stats["error"] = "无法提取文本（可能是扫描版PDF）"
                return stats

            stats["chars"] = len(full_text)

            # 图片：查找 Figure/Fig/图 引用
            fig_patterns = [
                r'Figure\s+\d+', r'Fig\.?\s*\d+', r'Fig\s+(\d+)',
                r'图\s*\d+', r'\\includegraphics',
            ]
            figs = set()
            for pat in fig_patterns:
                figs.update(re.findall(pat, full_text, re.IGNORECASE))
            stats["figures"] = len(figs)

            # 表格：查找 Table/表 引用
            tbl_patterns = [r'Table\s+\d+', r'表\s*\d+']
            tbls = set()
            for pat in tbl_patterns:
                tbls.update(re.findall(pat, full_text, re.IGNORECASE))
            stats["tables"] = len(tbls)

            # 公式：查找 \begin{equation} / $$ / = ... 模式
            eq_count = 0
            eq_count += len(re.findall(r'\\begin\{equation\}', full_text))
            eq_count += len(re.findall(r'\\begin\{align\}', full_text))
            # 独立行公式：以 = 结尾的行，或包含数学符号的行
            eq_lines = re.findall(r'^[^a-zA-Z]*[=≈≤≥].*$', full_text, re.MULTILINE)
            eq_count += min(len(eq_lines), 100)  # 上限100避免误匹配
            stats["equations"] = eq_count

            # 参考文献：查找 References / 参考文献 到结尾的条目
            ref_section = re.search(
                r'(?:References|REFERENCES|参考文献|Work\s*Cited|Bibliography)\s*\n',
                full_text
            )
            if ref_section:
                ref_text = full_text[ref_section.end():]
                # 统计引用条目：[N] 或 N. 或 (Author, Year)
                ref_entries = len(re.findall(
                    r'(?:\[\d+\]|\d+\.\s|\(\w+,\s*\d{4}\))',
                    ref_text[:3000]
                ))
                stats["references"] = ref_entries

            # 章节数：\section / 数字标题 / 一、二、
            sec_patterns = [r'\\section\{', r'^\d+\.\s+\w', r'^[一二三四五六七八九十]、']
            secs = set()
            for pat in sec_patterns:
                secs.update(re.findall(pat, full_text, re.MULTILINE))
            stats["sections"] = len(secs)

            pdf.close()
    except Exception as e:
        stats["error"] = str(e)[:200]

    return stats


def batch_extract(root: Path, contest: Optional[str] = None, limit: int = 50) -> dict:
    """批量提取论文统计"""
    meta_file = root / "references" / "papers_metadata.json"
    papers_dir = root / "references" / "papers"

    if not meta_file.exists():
        return {"status": "error", "message": "论文元数据不存在"}

    data = json.loads(meta_file.read_text(encoding="utf-8"))
    papers = data.get("papers", [])

    # 筛选
    if contest:
        papers = [p for p in papers if p.get("contest") == contest]

    # 优先选有奖项的（质量更高）
    awarded = [p for p in papers if p.get("award")]
    others = [p for p in papers if not p.get("award")]
    selected = awarded[:limit]
    if len(selected) < limit:
        selected += others[:limit - len(selected)]
    selected = selected[:limit]

    results = []
    errors = 0
    for p in selected:
        rel_path = p["file"]
        pdf_path = papers_dir.parent / rel_path  # references/papers/...
        if not pdf_path.exists():
            # 尝试直接构造路径
            pdf_path = root / "references" / rel_path

        if not pdf_path.exists():
            results.append({"file": p.get("name", rel_path), "error": "文件未找到"})
            errors += 1
            continue

        stats = extract_pdf_stats(pdf_path)
        stats["category"] = p.get("category", "")
        stats["subcategory"] = p.get("subcategory", "")
        stats["award"] = p.get("award", "")
        stats["year"] = p.get("year", "")
        stats["problem"] = p.get("problem", "")
        stats["contest"] = p.get("contest", "")
        results.append(stats)

    # 汇总
    valid = [r for r in results if not r.get("error")]
    if valid:
        pages = [r["pages"] for r in valid]
        chars = [r["chars"] for r in valid]
        figs = [r["figures"] for r in valid]
        tbls = [r["tables"] for r in valid]
        eqs = [r["equations"] for r in valid]
        refs = [r["references"] for r in valid]
        secs = [r["sections"] for r in valid]

        def pct(lst, p):
            s = sorted(lst)
            idx = int(len(s) * p / 100)
            return s[min(idx, len(s)-1)] if s else 0

        summary = {
            "count": len(valid),
            "errors": errors,
            "pages": {"min": min(pages), "max": max(pages), "p25": pct(pages, 25), "p50": pct(pages, 50), "p75": pct(pages, 75)},
            "chars": {"min": min(chars), "max": max(chars), "p25": pct(chars, 25), "p50": pct(chars, 50), "p75": pct(chars, 75)},
            "figures": {"min": min(figs), "max": max(figs), "p25": pct(figs, 25), "p50": pct(figs, 50), "p75": pct(figs, 75)},
            "tables": {"min": min(tbls), "max": max(tbls), "p25": pct(tbls, 25), "p50": pct(tbls, 50), "p75": pct(tbls, 75)},
            "equations": {"min": min(eqs), "max": max(eqs), "p25": pct(eqs, 25), "p50": pct(eqs, 50), "p75": pct(eqs, 75)},
            "references": {"min": min(refs), "max": max(refs), "p25": pct(refs, 25), "p50": pct(refs, 50), "p75": pct(refs, 75)},
            "sections": {"min": min(secs), "max": max(secs), "p25": pct(secs, 25), "p50": pct(secs, 50), "p75": pct(secs, 75)},
        }
    else:
        summary = {"count": 0, "errors": errors}

    return {
        "status": "ok",
        "contest": contest or "all",
        "requested": len(selected),
        "summary": summary,
        "details": results,
    }


def main():
    parser = argparse.ArgumentParser(description="批量论文统计")
    parser.add_argument("--contest", default=None, help="比赛类型: MCM/ICM 或 CUMCM（不指定则全部）")
    parser.add_argument("--limit", type=int, default=50, help="最多处理篇数")
    parser.add_argument("--output", default=None, help="输出文件（默认 references/paper_stats.json）")
    args = parser.parse_args()

    root = _resolve_root()
    result = batch_extract(root, args.contest, args.limit)

    output_path = root / "references" / "paper_stats.json" if not args.output else Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    # 输出摘要
    summary = result.get("summary", {})
    print(json.dumps({
        "status": result["status"],
        "contest": args.contest or "all",
        "count": summary.get("count", 0),
        "errors": summary.get("errors", 0),
        "file": str(output_path.relative_to(root)) if output_path.is_relative_to(root) else str(output_path),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
