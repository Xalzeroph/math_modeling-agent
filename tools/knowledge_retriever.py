#!/usr/bin/env python3
"""本地知识检索引擎 — 算法文档 + O奖论文 + 进化经验"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Optional


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "algorithms").exists():
            return d
        d = d.parent
    return Path.cwd()


def _score_keywords(text: str, keywords: List[str]) -> float:
    """简单关键词匹配打分"""
    text_lower = text.lower()
    score = 0.0
    for kw in keywords:
        kw_lower = kw.lower()
        # 精确匹配权重高
        count = text_lower.count(kw_lower)
        score += count * 1.0
    return score


def search_algorithms(root: Path, query: str, limit: int = 5) -> List[dict]:
    """搜索算法文档"""
    algo_dir = root / "algorithms"
    if not algo_dir.exists():
        return []

    keywords = re.split(r'[\s,，、]+', query.strip())
    keywords = [k for k in keywords if k]

    results = []
    for f in sorted(algo_dir.glob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        # 从标题提取算法类别
        title_match = re.search(r'^#\s*(.+)', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f.stem

        # 提取前 300 字作为摘要
        clean = re.sub(r'#{1,6}\s*', '', content[:500])
        snippet = clean[:300].replace('\n', ' ').strip()

        score = _score_keywords(title + " " + content[:2000], keywords)

        if score > 0:
            results.append({
                "source": "algorithms",
                "file": str(f.relative_to(root)),
                "title": title,
                "snippet": snippet,
                "score": score,
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def search_local_papers(root: Path, query: str, limit: int = 5) -> List[dict]:
    """搜索 O奖论文（按文件名和目录匹配）"""
    ref_dir = root / "references"
    if not ref_dir.exists():
        return []

    keywords = re.split(r'[\s,，、]+', query.strip())
    keywords = [k for k in keywords if k]

    results = []
    for pdf in sorted(ref_dir.rglob("*.pdf")):
        # 用文件名 + 父目录名作为标题
        category = pdf.parent.name
        filename = pdf.stem
        full_name = f"{category} {filename}"
        rel_path = str(pdf.relative_to(root))

        score = _score_keywords(full_name + " " + category, keywords)

        # 启发式匹配：关键词 → 相关子目录名
        type_map = {
            "优化": ["优化类", "线性规划", "整数规划", "遗传算法", "动态规划", "模拟退火", "蚁群算法", "粒子群"],
            "调度": ["优化类", "线性规划", "动态规划", "模拟退火", "蚁群算法"],
            "预测": ["预测类", "时间序列", "灰色预测", "灰色关联", "神经网络"],
            "评价": ["评价类", "层次分析法", "TOPSIS", "模糊综合评价"],
            "网络": ["图论网络类", "最短路径", "元胞自动机", "决策树"],
            "数据": ["统计类", "回归分析", "聚类分析", "主成分分析", "插值拟合"],
            "分类": ["统计类", "SVM", "逻辑回归", "聚类分析", "决策树"],
            "回归": ["统计类", "回归分析", "逻辑回归", "插值拟合"],
            "拟合": ["统计类", "插值拟合", "回归分析"],
            "微分方程": ["仿真综合类", "微分方程"],
            "模拟": ["仿真综合类", "蒙特卡洛", "仿真综合类"],
            "排队": ["仿真综合类", "排队论"],
        }
        for t_kw, matched_cats in type_map.items():
            if t_kw in " ".join(keywords).lower():
                if category in matched_cats:
                    score += 2.0

        if score > 0:
            results.append({
                "source": "local_paper",
                "file": rel_path,
                "title": full_name,
                "category": category,
                "score": score,
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def search_evolution_skills(root: Path, query: str, limit: int = 5) -> List[dict]:
    """搜索进化产生的技能文件"""
    evo_skill_dir = root / "memory" / "evolution" / "skills"
    if not evo_skill_dir.exists():
        return []

    keywords = re.split(r'[\s,，、]+', query.strip())
    keywords = [k for k in keywords if k]

    results = []
    for f in sorted(evo_skill_dir.glob("*.md")):
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        title_match = re.search(r'^#\s*(.+)', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f.stem

        snippet = content[:300].replace('\n', ' ').strip()

        score = _score_keywords(title + " " + content, keywords)
        if score > 0:
            results.append({
                "source": "evolution",
                "file": str(f.relative_to(root)),
                "title": title,
                "snippet": snippet,
                "score": score,
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def retrieve_all(root: Path, query: str, problem_type: Optional[str] = None) -> dict:
    """综合检索所有知识源"""
    # 如果是问题类型，增强 query
    enhanced_query = query
    if problem_type:
        enhanced_query = f"{problem_type} {query}"

    return {
        "query": query,
        "problem_type": problem_type,
        "algorithms": search_algorithms(root, enhanced_query, limit=5),
        "local_papers": search_local_papers(root, enhanced_query, limit=5),
        "evolution_skills": search_evolution_skills(root, enhanced_query, limit=5),
    }


def main():
    parser = argparse.ArgumentParser(description="本地知识检索引擎")
    parser.add_argument("--query", required=True, help="搜索关键词")
    parser.add_argument("--type", default="all",
                        choices=["all", "algorithms", "papers", "evolution"],
                        help="知识源类型")
    parser.add_argument("--problem-type", default=None, help="问题类型(如 optimization, regression)")
    parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()
    root = _resolve_root()

    if args.type == "algorithms":
        result = {"algorithms": search_algorithms(root, args.query, args.limit)}
    elif args.type == "papers":
        result = {"local_papers": search_local_papers(root, args.query, args.limit)}
    elif args.type == "evolution":
        result = {"evolution_skills": search_evolution_skills(root, args.query, args.limit)}
    else:
        result = retrieve_all(root, args.query, args.problem_type)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
