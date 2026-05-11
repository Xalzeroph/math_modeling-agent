#!/usr/bin/env python3
"""进化引擎种子数据生成器 — 从 O 奖论文创建种子 session 用于进化引擎冷启动"""

import argparse, json, os, shutil, sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "algorithms").exists():
            return d
        d = d.parent
    return Path.cwd()


TYPE_MAP = {
    "A": "optimization", "B": "optimization",
    "C": "prediction", "D": "network",
    "E": "ode", "F": "evaluation",
}


def _select_seeds(meta_file: Path, n: int = 6) -> list:
    """从论文元数据中选取代表性 O 奖论文作为种子"""
    if not meta_file.exists():
        return []

    data = json.loads(meta_file.read_text(encoding="utf-8"))
    outstanding = [p for p in data.get("papers", [])
                   if p.get("award") in ("Outstanding", "O奖") and p.get("problem")]

    # 每题选 1 篇
    selected = []
    seen_problems = set()
    for p in outstanding:
        prob = p.get("problem")
        if prob not in seen_problems and len(selected) < n:
            selected.append(p)
            seen_problems.add(prob)

    # 如果不够 N 篇，补充
    if len(selected) < n:
        extras = [p for p in outstanding if p not in selected]
        for p in extras[:n - len(selected)]:
            selected.append(p)

    return selected


def create_seed_session(root: Path, paper: dict, index: int) -> Optional[dict]:
    """为一篇 O 奖论文创建种子 session"""
    name = paper.get("name", "")
    year = paper.get("year", "")
    problem = paper.get("problem", "")
    subcat = paper.get("subcategory", "")

    session_name = f"seed-{year}-MCM-{problem}-Outstanding-{paper.get('team_id', index)}"
    session_dir = root / "sessions" / session_name
    session_dir.mkdir(parents=True, exist_ok=True)

    # 推断题型
    problem_type = TYPE_MAP.get(problem, "general")

    # 创建 README.md
    readme = f"""# {session_name}

**日期**: {year}
**题型**: {problem_type}
**竞赛**: MCM/ICM {problem}题
**奖项**: Outstanding (O奖)
**子类**: {subcat}
**关键词**: {problem_type}, MCM, {problem}-题, O奖

## 题目
来自 {year} 年 MCM/ICM {problem}题。

## 来源
references/papers/{paper.get('category', '')}/{paper.get('subcategory', '')}/{name}.pdf

## 模型
{_model_hints(problem_type, subcat)}
"""
    (session_dir / "README.md").write_text(readme, encoding="utf-8")

    # 创建 solver 目录和占位文件
    (session_dir / "solvers").mkdir(exist_ok=True)
    (session_dir / "verifications").mkdir(exist_ok=True)

    # 创建问题描述 JSON
    problem_json = {
        "type": problem_type,
        "keywords": [problem_type, "MCM", f"{problem}-题", "O奖", subcat],
        "description": f"{year} MCM/ICM Problem {problem} — Outstanding Winner paper: {name}",
    }
    (session_dir / "problem.json").write_text(json.dumps(problem_json, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "session_name": session_name,
        "problem_type": problem_type,
        "paper": name,
        "year": year,
        "problem": problem,
    }


def _model_hints(problem_type: str, subcat: str) -> str:
    """根据题型和子类给出模型提示"""
    hints = {
        ("optimization", "线性规划"): "线性规划 / 整数规划",
        ("optimization", "遗传算法"): "遗传算法 / 多目标优化",
        ("optimization", "动态规划"): "动态规划 / 状态转移",
        ("evaluation", "层次分析法"): "层次分析法(AHP) / 模糊综合评价",
        ("evaluation", "TOPSIS"): "TOPSIS / 熵权法",
        ("prediction", "灰色预测"): "灰色预测 GM(1,1) / 时间序列",
        ("prediction", "时间序列"): "ARIMA / 指数平滑",
        ("network", "最短路径"): "Dijkstra / Floyd / 网络流",
        ("network", "元胞自动机"): "元胞自动机 / 交通流仿真",
        ("ode", "模拟退火"): "模拟退火 / 微分方程建模",
        ("ode", "微分方程"): "ODE / PDE 建模与数值求解",
    }
    return hints.get((problem_type, subcat), f"{problem_type} 相关模型")


def main():
    parser = argparse.ArgumentParser(description="进化引擎种子数据生成器")
    parser.add_argument("--n", type=int, default=6, help="种子数量（默认6）")
    parser.add_argument("--dry-run", action="store_true", help="仅打印而不创建")
    args = parser.parse_args()

    root = _resolve_root()
    meta_file = root / "references" / "papers_metadata.json"

    if not meta_file.exists():
        print(json.dumps({
            "status": "error",
            "message": "论文元数据索引不存在。请先运行: python tools/build_paper_index.py"
        }, ensure_ascii=False))
        sys.exit(1)

    seeds = _select_seeds(meta_file, args.n)
    if not seeds:
        print(json.dumps({
            "status": "error",
            "message": "未找到 O 奖论文种子。论文库需要包含 Outstanding 标签的论文。"
        }, ensure_ascii=False))
        sys.exit(1)

    created = []
    for i, paper in enumerate(seeds):
        if args.dry_run:
            session_name = f"seed-{paper.get('year')}-MCM-{paper.get('problem')}-Outstanding-{paper.get('team_id', i)}"
            created.append({"session_name": session_name, "paper": paper["name"]})
        else:
            result = create_seed_session(root, paper, i)
            if result:
                created.append(result)

    print(json.dumps({
        "status": "dry_run" if args.dry_run else "ok",
        "seeded": len(created),
        "sessions": created,
        "hint": "现在可以运行: python tools/evolver.py evolve --session <session_name> --problem '{\"type\": \"optimization\", \"keywords\": [\"MCM\"]}'" if not args.dry_run else "运行 python tools/bootstrapper.py 来实际创建种子 session",
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
