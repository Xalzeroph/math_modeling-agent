#!/usr/bin/env python3
"""
自进化引擎 v6 — 做完题后记录经验到 roles/ 和 models/cases/

用法:
  python tools/evolution/evolver.py evolve --session "名称" --from-scorer
  python tools/evolution/evolver.py suggest --problem-type STRING
  python tools/evolution/evolver.py gaps
  python tools/evolution/evolver.py sessions
  python tools/evolution/evolver.py compare --session A --vs B
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List
from collections import defaultdict


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

ALL_PROBLEM_TYPES = ["optimization", "regression", "prediction", "evaluation",
                     "ode", "classification", "network", "statistics", "simulation"]


class MathModelEvolver:
    def __init__(self, root: Path):
        self.root = root

    def evolve(self, session_name: str, problem: dict, results: dict) -> dict:
        session_dir = self.root / "sessions" / session_name
        if not session_dir.exists():
            return {"status": "error", "message": f"Session 不存在: {session_name}"}

        ptype = problem.get("type", "unknown")
        keywords = problem.get("keywords", [])
        summary = problem.get("summary", session_name)
        score = results.get("overall_score", 0)
        success = score > 60

        models = _scan_models(session_dir)
        code_features = _scan_code_features(session_dir)

        changes = []

        # 1. 记录到三个角色文档
        changes += _evolve_modeler(self.root, ptype, models, keywords, success, score, summary)
        changes += _evolve_coder(self.root, session_dir, session_name, success)
        changes += _evolve_writer(self.root, session_dir, session_name, success)

        # 2. 算法验证标记
        changes += _evolve_algorithms(self.root, models, success, ptype)

        # 3. 案例沉淀到 models/cases/
        changes += _evolve_cases(self.root, session_name, problem, results, success)

        return {
            "status": "ok",
            "session": session_name,
            "success": success,
            "changes": changes,
            "gaps": self.gaps(),
            "summary": f"进化完成: {len(changes)} 处更新, {'成功' if success else '失败'}案例已记录",
        }

    def suggest(self, problem_type: str) -> dict:
        """从 models/cases/ 和 role 文档进化区中检索历史策略"""
        cases = self._scan_cases()
        matches = [c for c in cases if problem_type in c.get("type", "")]

        best = None
        best_score = 0
        failures = []
        for c in matches:
            score = c.get("score", 0)
            if score > best_score:
                best_score = score
                best = c
            if c.get("result") == "FAIL":
                failures.append(c)

        if not matches:
            return {"status": "no_data", "message": f"没有 {problem_type} 的历史策略"}

        return {
            "status": "ok",
            "problem_type": problem_type,
            "total_cases": len(matches),
            "recommended": best,
            "failure_patterns": failures[:5],
            "suggestion": (
                f"推荐 {best.get('algorithms', [])} "
                f"(得分 {best.get('score', 0)})" if best
                else f"尚无 {problem_type} 的高分策略"
            ) + (f"，注意: {failures[0].get('lessons', '')[:60]}" if failures else ""),
        }

    def _scan_cases(self) -> List[dict]:
        """扫描 models/cases/ 中所有案例"""
        cases = []
        case_dir = self.root / "models" / "cases"
        if not case_dir.exists():
            return cases
        for f in sorted(case_dir.glob("*.md")):
            text = f.read_text(encoding="utf-8")[:2000]
            case = {"session": f.stem}
            m = re.search(r'题型\*\*:\s*(\w+)', text)
            if m:
                case["type"] = m.group(1)
            m = re.search(r'结果\*\*:\s*(\w+)', text)
            if m:
                case["result"] = m.group(1)
            m = re.search(r'关键词\*\*:\s*(.+)', text)
            if m:
                case["keywords"] = [k.strip() for k in m.group(1).split(",")]
            m = re.search(r'算法\*\*:\s*(.+)', text)
            if m:
                case["algorithms"] = [a.strip() for a in m.group(1).split(",")]
            m = re.search(r'得分\*\*:\s*(\d+)', text)
            if m:
                case["score"] = int(m.group(1))
            m = re.search(r'教训\*\*\n*(.+?)(?:\n##|\Z)', text, re.DOTALL)
            if m:
                case["lessons"] = m.group(1).strip()[:300]
            cases.append(case)
        return cases

    def gaps(self) -> dict:
        """检测知识盲区 — 未做过的题型 + 未验证的算法"""
        cases = self._scan_cases()
        done_types = set(c.get("type", "") for c in cases)

        # 统计已验证的算法
        verified_ids = set()
        for c in cases:
            for a in c.get("algorithms", []):
                verified_ids.add(a)

        missing = [t for t in ALL_PROBLEM_TYPES if t not in done_types]

        # 检查 index.json 中从未验证过的算法
        index_file = self.root / "algorithms" / "index.json"
        unverified = []
        if index_file.exists():
            index = json.loads(index_file.read_text(encoding="utf-8"))
            for dk, domain in index.get("domains", {}).items():
                for sk, sub in domain.get("subdomains", {}).items():
                    for m in sub.get("methods", []):
                        if not m.get("evolved_status") and m["id"] not in verified_ids:
                            unverified.append({
                                "id": m["id"], "name": m["name"],
                                "domain": domain["name"], "package": m["package"],
                            })

        return {
            "missing_problem_types": missing,
            "unverified_algorithms": unverified[:10],
            "suggestion": (f"建议尝试: {', '.join(missing)} 类题目"
                           if missing else "所有题型均有覆盖") +
                          (f", {len(unverified)} 个算法待验证" if unverified else ""),
        }

    def list_sessions(self) -> dict:
        sessions_dir = self.root / "sessions"
        sessions = []
        if sessions_dir.exists():
            for d in sorted(sessions_dir.iterdir()):
                if d.is_dir() and not d.name.startswith("."):
                    sessions.append({
                        "name": d.name,
                        "solvers": len(list((d / "solvers").glob("*.py"))) if (d / "solvers").exists() else 0,
                        "has_paper": (d / "paper" / "main.pdf").exists(),
                    })
        return {"sessions": sessions, "total": len(sessions)}

    def compare(self, s1: str, s2: str) -> dict:
        d1 = self.root / "sessions" / s1
        d2 = self.root / "sessions" / s2
        return {
            "session_a": s1, "exists_a": d1.exists(),
            "session_b": s2, "exists_b": d2.exists(),
        }


# ═══════════════════════════════════════════════════════════════
# 代码扫描
# ═══════════════════════════════════════════════════════════════

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
            for feat in ["curve_fit", "linprog", "solve_ivp", "sklearn",
                        "cross_val", "matplotlib", "seaborn", "networkx",
                        "differential_evolution", "statsmodels"]:
                if feat in code:
                    features.add(feat)
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
        return ("regression", ["sklearn"])
    if "arima" in code.lower() or "prophet" in code.lower():
        return ("prediction", ["arima"])
    return ("general", [])


# ═══════════════════════════════════════════════════════════════
# 进化动作 — 写入 role 文档和 case 文件
# ═══════════════════════════════════════════════════════════════

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
        entries = [{"算法": a, "题型": ptype, "最近验证": _now(), "得分": str(score)} for a in algos]
        if _update_table(role_file, "<!-- EVOLUTION:VERIFIED_ALGORITHMS -->", entries):
            changes.append("建模手: 更新已验证算法")
    return changes


def _evolve_coder(root, session_dir, session_name, success):
    changes = []
    role_file = root / "roles" / "编程手.md"
    solver_dir = session_dir / "solvers"
    if solver_dir.exists():
        for py in sorted(solver_dir.glob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True)[:1]:
            code = py.read_text(encoding="utf-8")
            tpl = f"### {session_name}/{py.name} ({_now()})\n\n```python\n{code[:1000]}\n```\n"
            if _append_to_section(role_file, "<!-- EVOLUTION:CODE_TEMPLATES -->", tpl):
                changes.append(f"编程手: +模板 {py.name}")
                break
    if not success:
        pitfall = f"### {_now()} — {session_name}\n\n本次验证未通过。\n"
        if _append_to_section(role_file, "<!-- EVOLUTION:PITFALLS -->", pitfall):
            changes.append("编程手: 追加踩坑")
    return changes


def _evolve_writer(root, session_dir, session_name, success):
    changes = []
    role_file = root / "roles" / "论文手.md"
    main_tex = session_dir / "paper" / "main.tex"
    if main_tex.exists() and success:
        content = main_tex.read_text(encoding="utf-8")
        m = re.search(r'\\begin\{abstract\}(.+?)\\end\{abstract\}', content, re.DOTALL)
        abstract = m.group(1).strip()[:300] if m else "见文件"
        sections = re.findall(r'\\section\{([^}]+)\}', content)
        case = f"### {session_name} ({_now()})\n\n**摘要**: {abstract}\n\n**结构**: {', '.join(sections)}\n"
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
        "optimization": ["01-优化算法说明.md"],
        "regression": ["02-预测类算法说明.md", "07-机器学习算法说明.md"],
        "prediction": ["02-预测类算法说明.md"],
        "evaluation": ["03-评价类算法说明.md"],
        "network": ["04-图论与网络分析算法说明.md"],
        "classification": ["07-机器学习算法说明.md"],
        "ode": ["06-综合类算法说明.md"],
        "statistics": ["05-统计分析与数据处理算法说明.md"],
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
                if tag in content:
                    continue
                pattern = re.compile(
                    rf'(^##\s+\d+\.?\s*.*?{re.escape(a)}.*?$)|'
                    rf'(^##\s+{re.escape(a)}.*?$)',
                    re.MULTILINE | re.IGNORECASE
                )
                matched = pattern.search(content)
                if matched:
                    new_line = f"{matched.group(0)} {tag}"
                    content = content.replace(matched.group(0), new_line, 1)
                    fpath.write_text(content, encoding="utf-8")
                    changes.append(f"算法库: 标记 {a} verified")
                    break
    return changes


def _evolve_cases(root, session_name, problem, results, success):
    case_dir = root / "models" / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    fpath = case_dir / f"{session_name}.md"

    # 提取算法信息
    session_dir = root / "sessions" / session_name
    models = _scan_models(session_dir)
    algos = list(set(a for m in models for a in m.get("algorithms", [])))

    content = (
        f"# {session_name}\n\n"
        f"- **日期**: {_now()}\n"
        f"- **题型**: {problem.get('type', 'unknown')}\n"
        f"- **算法**: {', '.join(algos) if algos else 'N/A'}\n"
        f"- **得分**: {results.get('overall_score', 0)}\n"
        f"- **关键词**: {', '.join(problem.get('keywords', []))}\n"
        f"- **结果**: {'PASS' if success else 'FAIL'}\n\n"
        f"## 教训\n{results.get('lessons', '')}\n"
    )
    fpath.write_text(content, encoding="utf-8")
    return [f"模型库: {fpath.name}"]


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="自进化引擎 v6")
    sub = parser.add_subparsers(dest="action", required=True)

    ev = sub.add_parser("evolve", help="从 session 进化")
    ev.add_argument("--session", required=True)
    ev.add_argument("--problem", default="{}")
    ev.add_argument("--results", default="{}")
    ev.add_argument("--from-scorer", action="store_true", help="自动读取 sessions/{session}/eval_report.json")

    sub.add_parser("suggest", help="推荐策略").add_argument("--problem-type", required=True)
    sub.add_parser("gaps", help="知识盲区")
    sub.add_parser("sessions", help="所有 sessions")

    cmp = sub.add_parser("compare", help="对比两次 session")
    cmp.add_argument("--session", required=True, dest="s1")
    cmp.add_argument("--vs", required=True, dest="s2")

    args = parser.parse_args()
    root = _resolve_root()
    evo = MathModelEvolver(root)

    try:
        if args.action == "evolve":
            problem = json.loads(args.problem)
            results = json.loads(args.results)
            if getattr(args, "from_scorer", False):
                eval_file = root / "sessions" / args.session / "eval_report.json"
                if eval_file.exists():
                    eval_data = json.loads(eval_file.read_text(encoding="utf-8"))
                    if not problem or problem == {}:
                        problem = {"type": eval_data.get("problem_type", "unknown"),
                                   "keywords": [], "summary": args.session}
                    results = {"overall_score": eval_data.get("overall_score", 0),
                               "lessons": "\n".join(eval_data.get("improvements", [])),
                               "grade": eval_data.get("grade", "?")}
            r = evo.evolve(args.session, problem, results)
        elif args.action == "suggest":
            r = evo.suggest(args.problem_type)
        elif args.action == "gaps":
            r = evo.gaps()
        elif args.action == "sessions":
            r = evo.list_sessions()
        elif args.action == "compare":
            r = evo.compare(args.s1, args.s2)
        print(json.dumps(r, indent=2, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
