#!/usr/bin/env python3
"""
论文学习工具 — O奖论文写作规律提取

每次建模时读一篇与当前题型匹配的论文，提取写作规律，
沉淀到 roles/论文手.md 的进化区。

用法:
  python tools/paper_learn.py --session "2026-国赛-B-无人机" --problem-type optimization
  python tools/paper_learn.py --session "2026-数维杯-A" --problem-type prediction
  python tools/paper_learn.py list                                           # 列出所有论文+题型
  python tools/paper_learn.py stats                                          # 统计已学/未学论文
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from collections import defaultdict


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "references" / "papers").exists() or (d / "references").exists():
            return d
        d = d.parent
    return Path.cwd()


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ── 题型匹配 ────────────────────────────────────

TOPIC_TAGS = {
    "optimization": ["调度", "优化", "配置", "装配", "规划", "RGV", "路径",
                     "scheduling", "optimization", "A", "B"],
    "evaluation":  ["评价", "评估", "会员", "画像", "判别", "评分",
                     "evaluation", "F"],
    "prediction":  ["预测", "预报", "预测", "prediction", "forecast", "C"],
    "ode":         ["微分", "方程", "动力学", "温度", "热", "ODE",
                     "differential", "D", "E"],
    "network":     ["网络", "图", "路径", "流", "连通",
                     "network", "graph", "D"],
    "classification": ["分类", "识别", "检测", "故障",
                       "classification", "detection"],
    "regression":  ["回归", "拟合", "回归", "regression", "fit"],
}

PAPER_DB_FILE = "paper_learn_db.json"


# ── 论文数据库 ──────────────────────────────────

def _list_papers(root: Path) -> list:
    ref_dir = root / "references"
    papers = []
    for pdf in sorted(ref_dir.rglob("*.pdf")):
        category = pdf.parent.name
        papers.append({
            "path": str(pdf.relative_to(root)),
            "name": pdf.stem,
            "category": category,
            "size_kb": pdf.stat().st_size // 1024,
        })
    return papers


def _match_type(name: str, category: str) -> list:
    """匹配题型 — 基于新的6大类28子类结构"""
    # category 现在是子目录名（如"层次分析法"），通过父目录获取大类
    type_map = {
        # 优化类子目录
        "线性规划": ["optimization"],
        "整数规划": ["optimization"],
        "遗传算法": ["optimization"],
        "动态规划": ["optimization"],
        # 评价类子目录
        "层次分析法": ["evaluation"],
        "TOPSIS": ["evaluation"],
        "模糊综合评价": ["evaluation"],
        # 预测类子目录
        "时间序列": ["prediction"],
        "灰色预测": ["prediction"],
        "灰色关联": ["prediction"],
        # 统计类子目录
        "回归分析": ["regression"],
        "逻辑回归": ["regression", "classification"],
        "聚类分析": ["classification"],
        "主成分分析": ["regression"],
        "因子分析": ["regression"],
        "方差分析": ["regression"],
        "典型相关分析": ["regression"],
        "SVM": ["classification"],
        "插值拟合": ["regression"],
        # 图论网络类子目录
        "最短路径": ["network", "optimization"],
        "元胞自动机": ["network", "simulation"],
        "决策树": ["classification", "network"],
        # 仿真综合类子目录
        "模拟退火": ["optimization", "simulation"],
        "蚁群算法": ["optimization", "network"],
        "粒子群": ["optimization", "simulation"],
        "神经网络": ["prediction", "classification"],
        "排队论": ["simulation", "network"],
        "蒙特卡洛": ["simulation"],
        "马尔科夫": ["prediction", "simulation"],
        "微分方程": ["ode", "simulation"],
        "博弈论": ["simulation"],
        "小波分析": ["regression"],
        "投影寻踪": ["regression"],
    }
    return type_map.get(category, ["general"])


def _load_learn_db(root: Path) -> dict:
    f = root / "memory" / PAPER_DB_FILE
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {"learned": {}, "extractions": []}


def _save_learn_db(root: Path, db: dict):
    f = root / "memory" / PAPER_DB_FILE
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")


# ── 学习指令 ────────────────────────────────────

def list_papers_cmd(root: Path) -> dict:
    papers = _list_papers(root)
    by_type = defaultdict(int)
    for p in papers:
        for t in _match_type(p["name"], p["category"]):
            by_type[t] += 1
    return {
        "total": len(papers),
        "by_type": dict(by_type),
    }


def stats_cmd(root: Path) -> dict:
    db = _load_learn_db(root)
    papers = _list_papers(root)
    learned = set(db["learned"].keys())
    total = len(papers)
    learned_count = len(learned)
    return {
        "total_papers": total,
        "learned": learned_count,
        "remaining": total - learned_count,
        "recent_extractions": db.get("extractions", [])[-5:],
        "hint": _pick_next(root, "optimization", learned),
    }


def _pick_next(root: Path, problem_type: str, learned: set) -> str:
    papers = _list_papers(root)
    # 优先选题型匹配且未学过的
    for p in papers:
        if p["name"] not in learned:
            matched = _match_type(p["name"], p["category"])
            if problem_type in matched:
                return f"suggest: {p['name']} (category={p['category']}, types={matched})"
    # fallback: 任意未学过的
    for p in papers:
        if p["name"] not in learned:
            return f"suggest: {p['name']} (category={p['category']})"
    return "全部论文已学完"


def learn_cmd(root: Path, paper_name: str, session_name: str,
              extraction: str) -> dict:
    """
    记录一次论文学习。
    extraction 是 Claude Code 读 PDF 后提取的写作规律，
    然后本函数把它写入 roles/论文手.md 的进化区。
    """
    db = _load_learn_db(root)
    papers = _list_papers(root)

    # 找到对应的论文
    matched = None
    for p in papers:
        if p["name"] == paper_name or paper_name in p["name"]:
            matched = p
            break
    if not matched:
        return {"status": "error", "message": f"论文未找到: {paper_name}"}

    # 记录已学习
    db["learned"][matched["name"]] = {
        "path": matched["path"],
        "session": session_name,
        "learned_at": _now(),
    }
    db.setdefault("extractions", []).append({
        "paper": matched["name"],
        "session": session_name,
        "extraction": extraction[:2000],
        "at": _now(),
    })
    _save_learn_db(root, db)

    # 写入论文手进化区
    role_file = root / "roles" / "论文手.md"
    if not role_file.exists():
        return {"status": "ok", "message": "记录已保存，但论文手.md 不存在"}

    text = role_file.read_text(encoding="utf-8")
    marker = "<!-- EVOLUTION:EXPRESSIONS -->"

    # 写作表达区
    entry = (
        f"### {matched['name']} ({_now()})\n\n"
        f"**来源**: {matched['path']}\n"
        f"**题型匹配**: {', '.join(_match_type(matched['name'], matched['category']))}\n\n"
        f"**提取的写作规律**:\n{extraction[:3000]}\n"
    )
    if marker in text:
        lines = text.split("\n")
        out = []
        for line in lines:
            out.append(line)
            if marker in line:
                out.append("")
                out.append(entry.strip())
                out.append("")
        role_file.write_text("\n".join(out), encoding="utf-8")

    return {
        "status": "ok",
        "paper": matched["name"],
        "total_learned": len(db["learned"]),
        "saved_to": "roles/论文手.md (EVOLUTION:EXPRESSIONS)",
    }


def suggest_cmd(root: Path, problem_type: str) -> dict:
    """推荐下一篇该读的论文"""
    db = _load_learn_db(root)
    learned = set(db["learned"].keys())
    return {"suggestion": _pick_next(root, problem_type, learned)}


# ── CLI ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="论文学习工具")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("list", help="列出所有论文及题型匹配")
    sub.add_parser("stats", help="学习统计")

    s = sub.add_parser("suggest", help="推荐下一本该读的论文")
    s.add_argument("--problem-type", required=True)

    lr = sub.add_parser("learn", help="记录一次论文学习")
    lr.add_argument("--paper", required=True, help="论文名称")
    lr.add_argument("--session", required=True, help="当前 session")
    lr.add_argument("--extraction", required=True, help="提取的写作规律")

    args = parser.parse_args()
    root = _resolve_root()

    try:
        if args.action == "list":
            r = list_papers_cmd(root)
        elif args.action == "stats":
            r = stats_cmd(root)
        elif args.action == "suggest":
            r = suggest_cmd(root, args.problem_type)
        elif args.action == "learn":
            r = learn_cmd(root, args.paper, args.session, args.extraction)
        print(json.dumps(r, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
