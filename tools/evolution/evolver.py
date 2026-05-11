#!/usr/bin/env python3
"""
自进化引擎 v5 — 每次做完题不仅记录，还主动提升自己

进化机制：
  1. 记录 — 经验写入 roles/、策略存入 memory/
  2. 对比 — 跟历史最佳会话比较，找到差距
  3. 强化 — 提升高分策略的权重，降低失败策略的权重
  4. 填补 — 检测知识盲区（做过的题型/没用过的算法），提醒补全
  5. 蒸馏 — 从多次实践中提炼可迁移的通用模板

用法:
  python tools/evolution/evolver.py evolve --session "名称" --problem '{}' --results '{}'
  python tools/evolution/evolver.py suggest --problem-type STRING
  python tools/evolution/evolver.py gaps                        # 查看知识盲区
  python tools/evolution/evolver.py summary                     # 查看进化摘要
  python tools/evolution/evolver.py sessions                    # 查看所有 session
  python tools/evolution/evolver.py compare --session A --session B  # 对比两次 session
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "algorithms").exists():
            return d
        d = d.parent
    return Path.cwd()


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _append_to_section(filepath: Path, marker: str, content: str) -> bool:
    if not filepath.exists():
        return False
    text = filepath.read_text(encoding="utf-8")
    if marker not in text:
        return False
    lines = text.split("\n")
    out = []
    for line in lines:
        out.append(line)
        if marker in line:
            out.append("")
            out.append(content.strip())
            out.append("")
    filepath.write_text("\n".join(out), encoding="utf-8")
    return True


def _update_table(filepath: Path, marker: str, new_entries: List[dict]) -> bool:
    if not filepath.exists():
        return False
    text = filepath.read_text(encoding="utf-8")
    if marker not in text:
        return False
    parts = text.split(marker, 1)
    after = parts[1]
    m = re.search(r'\n(## |<!-- )', after)
    end = m.start() if m else len(after)
    existing_block = after[:end]
    existing = {}
    for row in re.findall(r'\|(.+)\|', existing_block):
        cols = [c.strip() for c in row.split("|")]
        if cols and cols[0] and cols[0] not in ("", "---"):
            existing[cols[0]] = cols[1:]
    keys = list(new_entries[0].keys()) if new_entries else []
    for entry in new_entries:
        k = entry.get(keys[0], "") if keys else ""
        vals = [str(entry.get(kk, "")) for kk in keys[1:]]
        existing[k] = vals
    table = "| " + " | ".join(keys) + " |\n"
    table += "| " + " | ".join(["---"] * len(keys)) + " |\n"
    for k, vals in existing.items():
        table += "| " + " | ".join([k] + vals) + " |\n"
    new_text = parts[0] + marker + "\n\n" + table + "\n" + after[end:]
    filepath.write_text(new_text, encoding="utf-8")
    return True


# ═══════════════════════════════════════════════════════════════
# 进化引擎
# ═══════════════════════════════════════════════════════════════

class MathModelEvolver:
    def __init__(self, root: Path):
        self.root = root
        # 按角色分类的记忆目录
        self.mem_dirs = {
            "modeler": root / "memory" / "modeler",
            "coder":   root / "memory" / "coder",
            "writer":  root / "memory" / "writer",
        }
        for d in self.mem_dirs.values():
            d.mkdir(parents=True, exist_ok=True)

        self.strategies = self._load("modeler", "strategies.json")   # 题型→策略映射
        self.templates_db = self._load("coder", "code_templates.json")  # 代码模板
        self.qa_db = self._load("modeler", "qa_patterns.json")       # 问题-解法映射

    def _load(self, role: str, fname: str) -> dict:
        f = self.mem_dirs[role] / fname
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

    def _save(self, role: str, fname: str, data: dict):
        (self.mem_dirs[role] / fname).write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── 主入口：一次完整进化 ──────────────────────

    def evolve(self, session_name: str, problem: dict, results: dict) -> dict:
        session_dir = self.root / "sessions" / session_name
        if not session_dir.exists():
            return {"status": "error", "message": f"Session 不存在: {session_name}"}

        ptype = problem.get("type", "unknown")
        keywords = problem.get("keywords", [])
        summary = problem.get("summary", session_name)
        score = results.get("overall_score", 0)
        grade = results.get("grade", "?")
        lessons = results.get("lessons", "")
        success = score > 60

        models = _scan_models(session_dir)
        code_features = _scan_code_features(session_dir)

        changes = []

        # ── 1. 记录：记到三个角色文档
        changes += _evolve_modeler(self.root, ptype, models, keywords, success, score, summary)
        changes += _evolve_coder(self.root, session_dir, session_name, code_features, success)
        changes += _evolve_writer(self.root, session_dir, session_name, success)

        # ── 2. 记录：算法验证标记
        changes += _evolve_algorithms(self.root, models, success, ptype)

        # ── 3. 记录：案例沉淀
        changes += _evolve_cases(self.root, session_name, session_dir, problem, results, success)

        # ── 4. 强化：更新问题-解法映射 + 策略库
        patterns = _extract_qa_patterns(problem, results, models, code_features, success)
        for p in patterns:
            key = f"{p['problem_type']}_{p['model_type']}"
            if key in self.qa_db:
                self.qa_db[key]["count"] += 1
                n = self.qa_db[key]["count"]
                old = self.qa_db[key]["success_rate"]
                self.qa_db[key]["success_rate"] = (old * (n - 1) + (1.0 if success else 0.0)) / n
                # 合并新发现的代码特征
                for f in p.get("code_features", []):
                    if f not in self.qa_db[key].get("code_features", []):
                        self.qa_db[key].setdefault("code_features", []).append(f)
            else:
                self.qa_db[key] = p
            changes.append(f"强化: {key} → success_rate={self.qa_db[key]['success_rate']:.2f}")

        # 同样更新 strategies.json
        _update_strategies(self.strategies, ptype, models, keywords, success)
        _update_code_templates(self.templates_db, session_dir, self.root)

        self._save("modeler", "strategies.json", self.strategies)
        self._save("coder", "code_templates.json", self.templates_db)
        self._save("modeler", "qa_patterns.json", self.qa_db)

        # ── 5. 对比：跟历史最佳比较
        comparison = _compare_to_best(self.qa_db, ptype, score)

        # ── 6. 填补：检测知识盲区
        gaps = _detect_gaps(self.qa_db, self.root)

        # ── 7. 蒸馏：从所有 session 中提炼模板
        distilled = _distill(self.root)

        return {
            "status": "ok",
            "session": session_name,
            "success": success,
            "changes": changes,
            "comparison": comparison,
            "gaps": gaps,
            "distilled": distilled,
            "summary": f"进化完成: {len(changes)} 处更新, {'成功' if success else '失败'}案例已记录"
        }

    # ── 查询接口 ──────────────────────────────────

    def suggest(self, problem_type: str) -> dict:
        candidates = {k: v for k, v in self.qa_db.items()
                     if problem_type in v.get("problem_type", "") or problem_type in k}
        if not candidates:
            return {"status": "no_data", "message": f"没有 {problem_type} 的历史策略"}

        best = max(candidates.values(), key=lambda x: x.get("success_rate", 0) * x.get("count", 1))
        return {
            "status": "ok",
            "best": best,
            "alternatives": [v for v in candidates.values() if v != best][:3],
        }

    def gaps(self) -> dict:
        return _detect_gaps(self.qa_db, self.root)

    def list_sessions(self) -> dict:
        sessions_dir = self.root / "sessions"
        sessions = []
        if sessions_dir.exists():
            for d in sorted(sessions_dir.iterdir()):
                if d.is_dir():
                    readme = d / "README.md"
                    result_str = ""
                    if readme.exists():
                        m = re.search(r'-\s*\*\*结果\*\*:\s*(.+)', readme.read_text(encoding="utf-8"))
                        if m:
                            result_str = m.group(1).strip()
                    sessions.append({
                        "name": d.name,
                        "solvers": len(list((d / "solvers").glob("*.py"))) if (d / "solvers").exists() else 0,
                        "has_paper": (d / "paper" / "main.pdf").exists(),
                        "result": result_str,
                    })
        return {"sessions": sessions, "total": len(sessions)}

    def compare(self, s1: str, s2: str) -> dict:
        d1 = self.root / "sessions" / s1 / "README.md"
        d2 = self.root / "sessions" / s2 / "README.md"
        r1 = d1.read_text(encoding="utf-8")[:500] if d1.exists() else "N/A"
        r2 = d2.read_text(encoding="utf-8")[:500] if d2.exists() else "N/A"
        return {"session_a": s1, "summary_a": r1, "session_b": s2, "summary_b": r2}

    def summary(self) -> dict:
        return {
            "strategies": len(self.strategies),
            "qa_patterns": len(self.qa_db),
            "templates": len(self.templates_db),
            "top_strategies": sorted(self.qa_db.values(),
                key=lambda x: x.get("success_rate", 0) * x.get("count", 1), reverse=True
            )[:5],
        }

    def distill(self) -> dict:
        result = _distill(self.root)
        self._save("modeler", "distilled.json", result)
        return result


# ═══════════════════════════════════════════════════════════════
# 进化机制实现
# ═══════════════════════════════════════════════════════════════

ALL_PROBLEM_TYPES = ["optimization", "regression", "prediction", "evaluation",
                     "ode", "classification", "network", "statistics", "simulation"]

def _scan_models(session_dir: Path) -> List[dict]:
    models = []
    solver_dir = session_dir / "solvers"
    if solver_dir.exists():
        for py in solver_dir.glob("*.py"):
            code = py.read_text(encoding="utf-8")
            mtype, algos = _infer_from_code(code)
            models.append({"type": mtype, "algorithms": algos, "file": py.name})
    return models

def _scan_code_features(session_dir: Path) -> List[str]:
    features = set()
    solver_dir = session_dir / "solvers"
    if solver_dir.exists():
        for py in solver_dir.glob("*.py"):
            code = py.read_text(encoding="utf-8")
            if "curve_fit" in code: features.add("curve_fit")
            if "linprog" in code: features.add("linprog")
            if "solve_ivp" in code: features.add("solve_ivp")
            if "sklearn" in code: features.add("sklearn")
            if "cross_val" in code: features.add("cross_validation")
            if "differential_evolution" in code: features.add("differential_evolution")
            if "matplotlib" in code: features.add("matplotlib")
            if "seaborn" in code: features.add("seaborn")
            if "statsmodels" in code: features.add("statsmodels")
            if "networkx" in code: features.add("networkx")
    return sorted(features)

def _infer_from_code(code: str) -> tuple:
    if "solve_ivp" in code or "odeint" in code:
        return ("ode", ["solve_ivp"])
    if "linprog" in code or "milp" in code.lower():
        return ("optimization", ["linprog"])
    if "differential_evolution" in code or "genetic" in code.lower():
        return ("optimization", ["GA"])
    if "curve_fit" in code:
        return ("regression", ["curve_fit"])
    if "sklearn" in code:
        if "Regressor" in code or "Regression" in code:
            return ("regression", ["sklearn"])
        if "Classifier" in code:
            return ("classification", ["sklearn"])
        if "IsolationForest" in code:
            return ("classification", ["isolation_forest"])
        return ("regression", ["sklearn"])
    if "arima" in code.lower() or "prophet" in code.lower():
        return ("prediction", ["arima"])
    return ("general", [])

# ── 1. 记录：三个角色文档 ─────────────────────────


def _evolve_modeler(root, ptype, models, keywords, success, score, summary):
    changes = []
    role_file = root / "roles" / "建模手.md"
    mtypes = sorted(set(m.get("type", "?") for m in models))
    algos = sorted(set(a for m in models for a in m.get("algorithms", [])))

    if success:
        exp = f"### {_now()} — {summary[:60]}\n\n"
        exp += f"- **题型**: {ptype}\n"
        exp += f"- **模型**: {', '.join(mtypes)}\n"
        exp += f"- **算法**: {', '.join(algos)}\n"
        exp += f"- **标签**: {', '.join(keywords[:5])}\n"
        exp += f"- **得分**: {score}\n"
        if _append_to_section(role_file, "<!-- EVOLUTION:EXPERIENCES -->", exp):
            changes.append("建模手: 追加经验")
    else:
        lesson = f"### {_now()} — {summary[:60]}\n\n"
        lesson += f"- **题型**: {ptype}\n"
        lesson += f"- **尝试**: {', '.join(mtypes)}/{', '.join(algos)}\n"
        lesson += f"- **得分**: {score} — 需要分析原因\n"
        if _append_to_section(role_file, "<!-- EVOLUTION:LESSONS -->", lesson):
            changes.append("建模手: 追加教训")

    if algos:
        entries = [{"算法": a, "题型": ptype, "最近验证": _now(), "得分": str(score)}
                   for a in algos]
        if _update_table(role_file, "<!-- EVOLUTION:VERIFIED_ALGORITHMS -->", entries):
            changes.append("建模手: 更新已验证算法")
    return changes


def _evolve_coder(root, session_dir, session_name, features, success):
    changes = []
    role_file = root / "roles" / "编程手.md"
    solver_dir = session_dir / "solvers"
    if solver_dir.exists():
        for py in sorted(solver_dir.glob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True)[:1]:
            code = py.read_text(encoding="utf-8")
            tpl = f"### 模板: {session_name}/{py.name} ({_now()})\n\n```python\n{code[:1000]}\n```\n"
            if _append_to_section(role_file, "<!-- EVOLUTION:CODE_TEMPLATES -->", tpl):
                changes.append(f"编程手: +模板 {py.name}")
                break
    if not success:
        pitfall = f"### {_now()} — {session_name}\n\n本次验证未通过。检查 verifications/ 的输出。\n"
        if _append_to_section(role_file, "<!-- EVOLUTION:PITFALLS -->", pitfall):
            changes.append("编程手: 追加踩坑")
    return changes


def _evolve_writer(root, session_dir, session_name, success):
    changes = []
    role_file = root / "roles" / "论文手.md"
    main_tex = session_dir / "paper" / "main.tex"
    if main_tex.exists() and success:
        content = main_tex.read_text(encoding="utf-8")
        abstract = ""
        m = re.search(r'\\begin\{abstract\}(.+?)\\end\{abstract\}', content, re.DOTALL)
        if m:
            abstract = m.group(1).strip()[:300]
        sections = re.findall(r'\\section\{([^}]+)\}', content)
        case = f"### 案例: {session_name} ({_now()})\n\n**摘要**: {abstract or '见文件'}\n\n**结构**: {', '.join(sections)}\n"
        if _append_to_section(role_file, "<!-- EVOLUTION:PAPER_TEMPLATES -->", case):
            changes.append("论文手: 追加论文案例")
    if not success:
        lesson = f"### {_now()} — {session_name}\n\n本次论文未达预期\n"
        if _append_to_section(role_file, "<!-- EVOLUTION:WRITING_LESSONS -->", lesson):
            changes.append("论文手: 追加写作教训")
    return changes


def _evolve_algorithms(root, models, success, ptype):
    changes = []
    algo_dir = root / "algorithms"
    type_map = {
        "optimization": ["01-优化算法说明.md"], "regression": ["02-预测类算法说明.md", "07-机器学习算法说明.md"],
        "prediction": ["02-预测类算法说明.md"], "evaluation": ["03-评价类算法说明.md"],
        "network": ["04-图论与网络分析算法说明.md"], "classification": ["07-机器学习算法说明.md"],
        "ode": ["06-综合类算法说明.md"], "statistics": ["05-统计分析与数据处理算法说明.md"],
        "simulation": ["06-综合类算法说明.md"],
    }
    for m in models:
        for a in m.get("algorithms", []):
            for tf in type_map.get(ptype, []):
                fpath = algo_dir / tf
                if not fpath.exists():
                    continue
                content = fpath.read_text(encoding="utf-8")
                tag = f"<!-- EVOLVED: verified {_now()} -->"
                if tag not in content and a.lower() in content.lower():
                    fpath.write_text(content.replace(a, f"{a} {tag}", 1), encoding="utf-8")
                    changes.append(f"算法库: 标记 {a} verified")
    return changes


def _evolve_cases(root, session_name, session_dir, problem, results, success):
    changes = []
    case_dir = root / "models" / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    fpath = case_dir / f"{session_name}.md"
    content = (
        f"# {session_name}\n\n"
        f"- **日期**: {_now()}\n"
        f"- **题型**: {problem.get('type', 'unknown')}\n"
        f"- **关键词**: {', '.join(problem.get('keywords', []))}\n"
        f"- **结果**: {'PASS' if success else 'FAIL'}\n\n"
        f"## 题目\n{problem.get('description', '')[:500]}\n\n"
        f"## 教训\n{results.get('lessons', '')}\n"
    )
    fpath.write_text(content, encoding="utf-8")
    changes.append(f"模型库: {fpath.name}")
    return changes

# ── 4. 强化：QA模式提取 ─────────────────────────


def _extract_qa_patterns(problem, results, models, features, success):
    patterns = []
    for m in models:
        patterns.append({
            "problem_type": problem.get("type", "unknown"),
            "model_type": m.get("type", "unknown"),
            "algorithms": m.get("algorithms", []),
            "keywords": problem.get("keywords", []),
            "code_features": features,
            "success_rate": 1.0 if success else 0.0,
            "count": 1,
            "last_score": results.get("overall_score", 0),
            "last_used": _now(),
        })
    return patterns


def _update_strategies(strategies, ptype, models, keywords, success):
    for m in models:
        mtype = m.get("type", "unknown")
        key = f"{ptype}_{mtype}"
        if key in strategies:
            s = strategies[key]
            n = s.get("count", 0) + 1
            s["success_rate"] = (s.get("success_rate", 0.5) * (n - 1) + (1.0 if success else 0.0)) / n
            s["count"] = n
            s["last_used"] = _now()
        else:
            strategies[key] = {
                "problem_type": ptype, "model_type": mtype,
                "algorithms": m.get("algorithms", []), "tags": keywords[:5],
                "success_rate": 1.0 if success else 0.0, "count": 1,
                "last_used": _now(), "first_seen": _now(),
            }


def _update_code_templates(templates_db, session_dir, root):
    solver_dir = session_dir / "solvers"
    if not solver_dir.exists():
        return
    for py in sorted(solver_dir.glob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True)[:2]:
        code = py.read_text(encoding="utf-8")
        h = str(hash(code[:200]))
        if h in templates_db:
            templates_db[h]["count"] += 1
        else:
            templates_db[h] = {
                "id": f"tpl_{len(templates_db):04d}", "name": py.name,
                "session": session_dir.name, "code": code[:3000],
                "created": _now(), "count": 1,
            }

# ── 5. 对比 ─────────────────────────────────────


def _compare_to_best(qa_db, ptype, current_score):
    best_score = 0
    for v in qa_db.values():
        if v.get("problem_type") == ptype and v.get("last_score", 0) > best_score:
            best_score = v["last_score"]
    if best_score == 0:
        return {"message": f"这是 {ptype} 的第一个案例，无法对比", "gap": 0}
    gap = best_score - current_score
    return {
        "best_score": best_score, "current_score": current_score,
        "gap": gap,
        "message": f"{'优于' if gap < 0 else '低于'}历史最佳 {abs(gap)} 分" if gap != 0 else "与历史最佳持平"
    }

# ── 6. 填补：知识盲区 ───────────────────────────


def _detect_gaps(qa_db, root):
    done_types = set()
    for v in qa_db.values():
        done_types.add(v.get("problem_type", ""))
    missing = [t for t in ALL_PROBLEM_TYPES if t not in done_types]

    # 检查 algorithm/index.json 中有但从未验证过的算法
    index_file = root / "algorithms" / "index.json"
    unverified = []
    if index_file.exists():
        index = json.loads(index_file.read_text(encoding="utf-8"))
        for dk, domain in index.get("domains", {}).items():
            for sk, sub in domain.get("subdomains", {}).items():
                for m in sub.get("methods", []):
                    if not m.get("evolved_status") and m.get("id", "") not in qa_db:
                        unverified.append({
                            "id": m["id"], "name": m["name"],
                            "domain": domain["name"], "package": m["package"],
                        })

    return {
        "missing_problem_types": missing,
        "unverified_algorithms": unverified[:10],
        "suggestion": (f"建议尝试: {', '.join(missing)} 类题目"
                       if missing else "所有题型均有覆盖") +
                      (f", {len(unverified)} 个算法待验证" if unverified else "")
    }

# ── 7. 蒸馏 ─────────────────────────────────────


def _distill(root):
    sessions_dir = root / "sessions"
    if not sessions_dir.exists():
        return {"status": "empty"}

    template = {"total_sessions": 0, "by_type": {}, "common_features": {}}

    for d in sessions_dir.iterdir():
        if not d.is_dir():
            continue
        readme = d / "README.md"
        if not readme.exists():
            continue
        template["total_sessions"] += 1
        text = readme.read_text(encoding="utf-8")
        m = re.search(r'题型\*\*:\s*(\w+)', text)
        if m:
            t = m.group(1)
            template["by_type"][t] = template["by_type"].get(t, 0) + 1

    # 统计代码特征频率
    for d in sessions_dir.iterdir():
        if not d.is_dir():
            continue
        solver_dir = d / "solvers"
        if solver_dir.exists():
            for py in solver_dir.glob("*.py"):
                code = py.read_text(encoding="utf-8")
                for feat in ["curve_fit", "linprog", "solve_ivp", "sklearn",
                            "cross_val", "matplotlib", "seaborn", "networkx"]:
                    if feat in code:
                        template["common_features"][feat] = template["common_features"].get(feat, 0) + 1

    return template


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="自进化引擎 v5")
    sub = parser.add_subparsers(dest="action", required=True)

    ev = sub.add_parser("evolve", help="从 session 进化")
    ev.add_argument("--session", required=True)
    ev.add_argument("--problem", default="{}")
    ev.add_argument("--results", default="{}")

    sub.add_parser("summary", help="进化摘要")
    sub.add_parser("sessions", help="所有 sessions")
    sub.add_parser("gaps", help="知识盲区")
    sub.add_parser("distill", help="从所有 sessions 提取模板")

    sug = sub.add_parser("suggest", help="推荐策略")
    sug.add_argument("--problem-type", required=True)

    cmp = sub.add_parser("compare", help="对比两次session")
    cmp.add_argument("--session", required=True, dest="s1")
    cmp.add_argument("--vs", required=True, dest="s2")

    args = parser.parse_args()
    root = _resolve_root()
    evo = MathModelEvolver(root)

    try:
        if args.action == "evolve":
            r = evo.evolve(args.session, json.loads(args.problem), json.loads(args.results))
        elif args.action == "summary":
            r = evo.summary()
        elif args.action == "sessions":
            r = evo.list_sessions()
        elif args.action == "gaps":
            r = evo.gaps()
        elif args.action == "distill":
            r = evo.distill()
        elif args.action == "suggest":
            r = evo.suggest(args.problem_type)
        elif args.action == "compare":
            r = evo.compare(args.s1, args.s2)
        print(json.dumps(r, indent=2, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
