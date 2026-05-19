#!/usr/bin/env python3
"""本地知识检索 — 同义词映射 + 三源（算法库/论文库/进化经验）整合检索

解决 Claude Code 用 Grep 的语义鸿沟问题:
  搜"最短路径" → 找到 Dijkstra/Floyd/A* 的算法文档
  搜"灵敏度"   → 找到 Metropolis/扰动测试相关的进化经验

不依赖 embedding 模型，纯规则驱动。同义词映射手工维护。
"""

import argparse
import json
import re
import sys
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "algorithms").exists():
            return d
        d = d.parent
    return Path.cwd()


# ═══════════════════════════════════════════════════════════════
# 同义词映射表 — 手工维护，每次进化可扩展
# ═══════════════════════════════════════════════════════════════

SYNONYM_MAP: Dict[str, List[str]] = {
    # 优化相关
    "优化": ["optimization", "规划", "LP", "调度", "配置", "分配", "线性规划", "整数规划", "非线性规划"],
    "线性规划": ["linprog", "LP", "单纯形", "simplex", "内点法", "interior-point"],
    "整数规划": ["ILP", "MIP", "分支定界", "branch and bound", "割平面", "cutting plane"],
    "动态规划": ["DP", "状态转移", "最优子结构", "dynamic programming", "背包问题"],
    "遗传算法": ["GA", "genetic", "进化", "变异", "交叉", "deap", "differential_evolution"],
    "粒子群": ["PSO", "pyswarms", "swarm", "粒子群优化"],
    "模拟退火": ["SA", "simulated annealing", "退火", "dual_annealing", "Metropolis"],
    "蚁群": ["ACO", "ant colony", "蚂蚁", "信息素", "pheromone"],
    "多目标": ["NSGA-II", "Pareto", "pareto", "多目标优化", "MOO"],

    # 评价相关
    "评价": ["evaluation", "评估", "打分", "排序", "决策", "优劣", "评分"],
    "层次分析法": ["AHP", "层级分析", "成对比较"],
    "TOPSIS": ["优劣解距离", "理想解", "负理想解"],
    "熵权法": ["熵", "entropy", "客观赋权", "EWM"],
    "模糊": ["fuzzy", "模糊数学", "模糊评价", "隶属度"],

    # 预测相关
    "预测": ["prediction", "预报", "时间序列", "forecast", "推演"],
    "灰色预测": ["GM(1,1)", "grey model", "Grey Prediction"],
    "时间序列": ["ARIMA", "SARIMA", "季节性", "平稳性", "ADF检验", "自相关"],
    "指数平滑": ["Holt-Winters", "exponential smoothing", "平滑"],
    "Prophet": ["Facebook Prophet", "prophet", "加法模型"],

    # 统计/数据分析
    "回归": ["regression", "拟合", "回归分析", "linear regression", "最小二乘", "OLS"],
    "逻辑回归": ["logistic", "分类", "logit", "sigmoid"],
    "聚类": ["cluster", "K-means", "层次聚类", "DBSCAN", "聚类分析"],
    "主成分": ["PCA", "降维", "主成分分析"],
    "插值": ["interpolation", "interp1d", "样条", "spline", "曲面插值"],
    "拟合": ["curve_fit", "最小二乘", "lsq", "非线性拟合"],
    "假设检验": ["t检验", "卡方", "Shapiro-Wilk", "正态性", "显著性"],
    "方差分析": ["ANOVA", "组间差异", "F检验"],
    "因子分析": ["factor analysis", "潜在变量", "FA"],

    # 图论/网络
    "最短路径": ["Dijkstra", "dijkstra", "Floyd", "Bellman", "networkx.shortest_path", "A*", "astar"],
    "网络流": ["最大流", "最小费用流", "max flow", "Edmonds-Karp", "Ford-Fulkerson"],
    "生成树": ["MST", "最小生成树", "Kruskal", "Prim"],
    "元胞自动机": ["CA", "cellular automata", "格子", "演化规则"],
    "图论": ["graph theory", "网络", "连通", "度", "邻接"],

    # 仿真/动力学
    "蒙特卡洛": ["Monte Carlo", "MC", "随机模拟", "rand", "采样"],
    "排队论": ["queuing", "排队", "M/M/1", "服务率", "等待时间"],
    "博弈论": ["game theory", "博弈", "纳什均衡", "Nash"],
    "微分方程": ["ODE", "PDE", "differential", "odeint", "solve_ivp", "动力学", "数值解"],
    "马尔科夫": ["Markov", "状态转移", "MCMC", "生灭过程"],
    "灵敏度": ["sensitivity", "扰动", "鲁棒性", "参数分析", "OAT", "Sobol", "LHS"],

    # 机器学习
    "支持向量机": ["SVM", "support vector", "核方法", "SVC", "SVR"],
    "随机森林": ["Random Forest", "random forest", "集成学习", "bagging"],
    "XGBoost": ["xgboost", "boosting", "梯度提升", "GBDT"],
    "神经网络": ["neural network", "MLP", "BP", "tensorflow", "keras", "LSTM", "RNN"],
    "决策树": ["decision tree", "CART", "剪枝"],
}


def expand_query(query: str) -> List[str]:
    """将用户查询扩展为同义词列表"""
    keywords = re.split(r'[\s,，、]+', query.strip())
    keywords = [k for k in keywords if k]
    expanded = set(keywords)
    for kw in keywords:
        for key, synonyms in SYNONYM_MAP.items():
            if kw.lower() in key.lower() or key.lower() in kw.lower():
                expanded.update(synonyms)
                expanded.add(key)
    return list(expanded)


# ═══════════════════════════════════════════════════════════════
# 三源检索
# ═══════════════════════════════════════════════════════════════

def search_algorithms(root: Path, terms: List[str]) -> List[dict]:
    """从 index.json 中检索匹配的算法"""
    index_file = root / "algorithms" / "index.json"
    if not index_file.exists():
        return []

    data = json.loads(index_file.read_text(encoding="utf-8"))
    results = []
    for dk, domain in data.get("domains", {}).items():
        for sk, sub in domain.get("subdomains", {}).items():
            for m in sub.get("methods", []):
                # 拼一个可搜索的文本
                searchable = f"{m['name']} {m['package']} {' '.join(m.get('apply', []))} {sub['name']} {domain['name']}".lower()
                score = sum(1 for t in terms if t.lower() in searchable)
                if score > 0:
                    results.append({
                        "method_id": m["id"],
                        "name": m["name"],
                        "package": m["package"],
                        "domain": domain["name"],
                        "subdomain": sub["name"],
                        "apply": m.get("apply", []),
                        "evolved": m.get("evolved_status"),
                        "score": score,
                    })
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:10]


def search_papers(root: Path, terms: List[str]) -> List[dict]:
    """从 papers_metadata.json 中检索论文"""
    meta_file = root / "references" / "papers_metadata.json"
    if not meta_file.exists():
        return []

    data = json.loads(meta_file.read_text(encoding="utf-8"))
    results = []
    for p in data.get("papers", []):
        searchable = f"{p.get('name','')} {p.get('category','')} {p.get('subcategory','')} {p.get('problem','')} {p.get('award','')}".lower()
        score = sum(1 for t in terms if t.lower() in searchable)
        if score > 0:
            p["score"] = score
            results.append(p)

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:15]


def search_evolution(root: Path, terms: List[str]) -> List[dict]:
    """从 sessions/*/eval_report.json 中检索历史经验"""
    results = []
    sessions_dir = root / "sessions"
    if not sessions_dir.exists():
        return results
    for d in sorted(sessions_dir.iterdir()):
        if not d.is_dir():
            continue
        ef = d / "eval_report.json"
        if not ef.exists():
            continue
        try:
            data = json.loads(ef.read_text(encoding="utf-8"))
        except:
            continue
        searchable = json.dumps(data, default=str).lower()
        score = sum(1 for t in terms if t.lower() in searchable)
        if score > 0:
            data["session"] = d.name
            data["score"] = score
            results.append(data)

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:10]


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="本地知识检索 — 同义词扩展 + 三源整合")
    parser.add_argument("query", nargs="?", help="搜索关键词")
    parser.add_argument("--source", default="all", choices=["all", "algorithms", "papers", "evolution"],
                       help="指定数据源 (默认 all)")
    parser.add_argument("--limit", type=int, default=10, help="每源最多返回条数")
    args = parser.parse_args()

    if not args.query:
        parser.print_help()
        sys.exit(1)

    root = _resolve_root()
    terms = expand_query(args.query)

    result = {"query": args.query, "expanded_terms": terms[:20]}

    if args.source in ("all", "algorithms"):
        algos = search_algorithms(root, terms)
        result["algorithms"] = algos[:args.limit]

    if args.source in ("all", "papers"):
        papers = search_papers(root, terms)
        result["papers"] = papers[:args.limit]

    if args.source in ("all", "evolution"):
        evo = search_evolution(root, terms)
        result["evolution"] = evo[:args.limit]

    result["summary"] = (
        f"算法: {len(result.get('algorithms', []))} 条, "
        f"论文: {len(result.get('papers', []))} 条, "
        f"经验: {len(result.get('evolution', []))} 条"
    )

    output = json.dumps(result, indent=2, ensure_ascii=False)
    try:
        print(output)
    except UnicodeEncodeError:
        import sys
        if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        print(output)


if __name__ == "__main__":
    main()
