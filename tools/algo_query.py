#!/usr/bin/env python3
"""算法知识库查询工具 — 从 algorithms/index.json 查找推荐算法

用法:
  python tools/algo_query.py --type optimization          # 按题型查询
  python tools/algo_query.py --keyword "故障检测"          # 按关键词模糊匹配
  python tools/algo_query.py --problem "资源分配优化问题"   # 智能匹配
"""

import argparse
import json
import sys
from pathlib import Path


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "algorithms" / "index.json").exists():
            return d
        d = d.parent
    return Path.cwd()


def load_index(root: Path) -> dict:
    f = root / "algorithms" / "index.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {}

def load_code_index(root: Path) -> dict:
    f = root / "algorithms" / "code_index.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {}

def query_python_equiv(root: Path, matlab_func: str) -> dict:
    """查 MATLAB 函数的 Python 等价库"""
    ci = load_code_index(root)
    results = []
    mf = matlab_func.lower()
    mapping = {
        'linprog': ('线性规划', 'scipy.optimize.linprog'),
        'intlinprog': ('整数规划', 'pulp / scipy.optimize.milp'),
        'fmincon': ('非线性约束优化', 'scipy.optimize.minimize(method="SLSQP")'),
        'fminunc': ('无约束优化', 'scipy.optimize.minimize(method="BFGS")'),
        'ga': ('遗传算法', 'deap / scipy.optimize.differential_evolution'),
        'pso': ('粒子群', 'pyswarms'),
        'simulannealbnd': ('模拟退火', 'scipy.optimize.dual_annealing'),
        'kmeans': ('K-Means聚类', 'sklearn.cluster.KMeans'),
        'fitlm': ('线性回归拟合', 'sklearn.linear_model.LinearRegression / statsmodels.OLS'),
        'fitnlm': ('非线性回归拟合', 'scipy.optimize.curve_fit'),
        'regress': ('回归分析', 'sklearn.linear_model.LinearRegression'),
        'arima': ('ARIMA时间序列', 'statsmodels.tsa.arima.ARIMA'),
        'feedforwardnet': ('前馈神经网络', 'tensorflow.keras.Sequential'),
        'svm': ('支持向量机', 'sklearn.svm.SVC'),
        'pca': ('主成分分析', 'sklearn.decomposition.PCA'),
        'dijkstra': ('最短路径', 'scipy.sparse.csgraph.dijkstra / networkx'),
        'spline': ('样条插值', 'scipy.interpolate'),
        'interp1': ('一维插值', 'scipy.interpolate.interp1d'),
        'interp2': ('二维插值', 'scipy.interpolate.interp2d'),
        'fft': ('傅里叶变换', 'numpy.fft / scipy.fft'),
        'rand': ('随机数', 'numpy.random'),
        'cluster': ('层次聚类', 'scipy.cluster.hierarchy / sklearn.cluster'),
        'train': ('模型训练', 'tensorflow.keras / sklearn'),
        'tree': ('决策树', 'sklearn.tree.DecisionTreeClassifier'),
        'gamultiobj': ('多目标优化', 'pymoo'),
        'patternsearch': ('模式搜索', 'scipy.optimize.direct'),
        'stepwise': ('逐步回归', 'sklearn.feature_selection / statsmodels'),
    }
    for k, (desc, py) in mapping.items():
        if mf in k or k in mf:
            results.append({'matlab': k, 'description': desc, 'python': py})
    return {'query': matlab_func, 'results': results, 'total_categories': len(ci)}


def query_by_type(index: dict, ptype: str) -> dict:
    domain = index.get("domains", {}).get(ptype)
    if not domain:
        return {"status": "not_found", "message": f"未找到题型: {ptype}", "available": list(index.get("domains", {}).keys())}

    result = {"type": ptype, "name": domain["name"], "methods": []}
    for sub_key, sub in domain.get("subdomains", {}).items():
        for m in sub.get("methods", []):
            result["methods"].append({
                "id": m["id"],
                "name": m["name"],
                "package": m["package"],
                "apply": m.get("apply", []),
                "params": m.get("params"),
                "evolved": m.get("evolved_status"),
            })
    return result


def query_by_keyword(index: dict, keyword: str) -> dict:
    results = []
    kw = keyword.lower()
    for dk, domain in index.get("domains", {}).items():
        for sk, sub in domain.get("subdomains", {}).items():
            for m in sub.get("methods", []):
                text = f"{domain['name']} {sub['name']} {m['name']} {' '.join(m.get('apply', []))}".lower()
                if kw in text:
                    results.append({
                        "domain": domain["name"],
                        "subdomain": sub["name"],
                        "method": m["name"],
                        "id": m["id"],
                        "package": m["package"],
                        "apply": m.get("apply", []),
                        "evolved": m.get("evolved_status"),
                    })
    return {"keyword": keyword, "count": len(results), "results": results[:15]}


def smart_match(index: dict, problem: str) -> dict:
    """根据问题描述智能匹配题型和推荐算法"""
    mapping = index.get("problem_type_mapping", {})
    scores = {}
    for ptype, keywords in mapping.items():
        score = sum(1 for k in keywords if k in problem)
        if score > 0:
            scores[ptype] = score

    if not scores:
        # 退化为关键词搜索
        return {"matched_types": [], "recommendations": query_by_keyword(index, problem)}

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    recommendations = []
    for ptype, score in ranked[:3]:
        domain = index["domains"].get(ptype, {})
        top_methods = []
        for sk, sub in domain.get("subdomains", {}).items():
            for m in sub.get("methods", []):
                top_methods.append({
                    "domain": domain["name"],
                    "method": m["name"],
                    "id": m["id"],
                    "package": m["package"],
                    "apply": m.get("apply", []),
                    "evolved": m.get("evolved_status"),
                })
        recommendations.append({
            "type": ptype,
            "score": score,
            "top_methods": top_methods[:5],
        })

    return {
        "problem": problem[:100],
        "matched_types": [{"type": t, "score": s} for t, s in ranked],
        "recommendations": recommendations,
    }


def main():
    parser = argparse.ArgumentParser(description="算法知识库查询")
    parser.add_argument("--type", dest="ptype", help="按题型查询")
    parser.add_argument("--keyword", help="按关键词查询")
    parser.add_argument("--problem", help="根据问题描述智能匹配")
    parser.add_argument("--matlab", help="查 MATLAB 函数的 Python 等价库")
    parser.add_argument("--list-types", action="store_true", help="列出所有题型")

    args = parser.parse_args()
    root = _resolve_root()
    index = load_index(root)

    if args.list_types:
        types = {}
        for k, d in index.get("domains", {}).items():
            types[k] = d["name"]
        print(json.dumps({"types": types, "count": len(types)}, indent=2, ensure_ascii=False))
    elif args.matlab:
        print(json.dumps(query_python_equiv(root, args.matlab), indent=2, ensure_ascii=False))
    elif args.ptype:
        print(json.dumps(query_by_type(index, args.ptype), indent=2, ensure_ascii=False))
    elif args.keyword:
        print(json.dumps(query_by_keyword(index, args.keyword), indent=2, ensure_ascii=False))
    elif args.problem:
        print(json.dumps(smart_match(index, args.problem), indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
