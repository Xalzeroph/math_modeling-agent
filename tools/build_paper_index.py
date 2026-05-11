#!/usr/bin/env python3
"""论文元数据索引构建器 — 从文件名和目录结构推断元数据"""

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


# MCM 文件名模式：2004_B-18-Successful.pdf / 2017_F类-O奖--64486.pdf
RE_MCM_O = re.compile(
    r'^(?P<year>20\d{2})[_\s]*'
    r'(?P<problem>[ABCDEF])[_\s\-\u7c7b]*'
    r'(?:O奖|[Oo]utstanding)?[_\-\-]*'
    r'(?P<team>\d+)'
)
# CUMCM 年份模式：2008一等奖... / B74316.PDF
RE_CUMCM_YEAR = re.compile(r'^(?P<year>20\d{2})')
RE_CUMCM_AWARD = re.compile(r'一等奖|二等奖|O奖|Outstanding|Finalist|Meritorious')


def infer_metadata(filepath: Path, relative_path: str) -> dict:
    """从路径和文件名推断论文元数据"""
    category_path = Path(relative_path)
    parts = category_path.parts

    # 第一级是大类（如"优化类"），第二级是子类（如"遗传算法"）
    big_cat = parts[1] if len(parts) > 1 else "unknown"
    sub_cat = parts[2] if len(parts) > 2 else "unknown"
    fname_stem = filepath.stem

    meta = {
        "file": str(relative_path).replace("\\", "/"),
        "name": fname_stem,
        "category": big_cat,
        "subcategory": sub_cat,
        "year": None,
        "contest": None,
        "problem": None,
        "award": None,
        "team_id": None,
    }

    # 尝试匹配 MCM/ICM O奖论文模式
    m = RE_MCM_O.search(fname_stem)
    if m:
        meta["year"] = int(m.group("year"))
        meta["contest"] = "MCM/ICM"
        meta["problem"] = m.group("problem")
        meta["team_id"] = m.group("team")
        # 检测奖项
        name_lower = fname_stem.lower()
        if "outstanding" in name_lower or "o奖" in name_lower:
            meta["award"] = "Outstanding"
        elif "finalist" in name_lower:
            meta["award"] = "Finalist"
        elif "meritorious" in name_lower:
            meta["award"] = "Meritorious"
        return meta

    # 尝试 CUMCM 年份
    m = RE_CUMCM_YEAR.search(fname_stem)
    if m:
        year = int(m.group("year"))
        if 2000 <= year <= 2030:
            meta["year"] = year
            meta["contest"] = "CUMCM"

    # CUMCM 奖项
    award_match = RE_CUMCM_AWARD.search(fname_stem)
    if award_match:
        meta["award"] = award_match.group()

    # 如果目录名本身包含年份信息（如 "2017_F类-O奖"）
    if meta["year"] is None:
        ym = RE_CUMCM_YEAR.search(sub_cat)
        if ym:
            meta["year"] = int(ym.group(1))

    return meta


def build_index(root: Path) -> dict:
    """扫描 references/papers/ 建立元数据索引"""
    papers_dir = root / "references" / "papers"
    if not papers_dir.exists():
        papers_dir = root / "references"
        if not papers_dir.exists():
            return {"status": "error", "message": "references/papers/ 不存在"}

    entries = []
    stats = {"total": 0, "by_contest": {}, "by_year": {}, "by_award": {}, "by_category": {}}

    for pdf in sorted(papers_dir.rglob("*.pdf")):
        rel = pdf.relative_to(papers_dir)
        meta = infer_metadata(pdf, f"papers/{rel}")
        entries.append(meta)
        stats["total"] += 1

        # 统计
        cat = meta["category"]
        stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1

        contest = meta.get("contest")
        if contest:
            stats["by_contest"][contest] = stats["by_contest"].get(contest, 0) + 1

        year = meta.get("year")
        if year:
            stats["by_year"][str(year)] = stats["by_year"].get(str(year), 0) + 1

        award = meta.get("award")
        if award:
            stats["by_award"][award] = stats["by_award"].get(award, 0) + 1

    # 按年份倒序
    stats["by_year"] = dict(sorted(stats["by_year"].items(), reverse=True))
    stats["by_category"] = dict(sorted(stats["by_category"].items(), key=lambda x: -x[1]))

    return {
        "version": 1,
        "total": stats["total"],
        "stats": stats,
        "papers": entries,
    }


def main():
    parser = argparse.ArgumentParser(description="论文元数据索引构建器")
    parser.add_argument("--output", default=None, help="输出文件路径（默认 references/papers_metadata.json）")
    args = parser.parse_args()

    root = _resolve_root()
    result = build_index(root)

    if "status" in result:
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    output_path = root / "references" / "papers_metadata.json" if not args.output else Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "total": result["total"],
        "file": str(output_path.relative_to(root)) if output_path.is_relative_to(root) else str(output_path),
        "stats": result["stats"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
