#!/usr/bin/env python3
"""
自进化引擎 v9 — 只做机械活 (表格更新/标记/评分弱项提取)
Claude Code 负责洞见活 (读 scoring 结果 → 写经验总结到 role 文档)

用法:
  python tools/evolution/evolver.py evolve --session "名称" --from-scorer
  python tools/evolution/evolver.py suggest --problem-type STRING
  python tools/evolution/evolver.py gaps
  python tools/evolution/evolver.py sessions
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
        """做纯机械活 — 不写经验洞见（那是Claude的事）"""
        session_dir = self.root / "sessions" / session_name
        if not session_dir.exists():
            return {"status": "error", "message": f"Session 不存在: {session_name}"}

        ptype = problem.get("type", "unknown")
        score = results.get("overall_score", 0)
        success = score > 60
        models = _scan_models(session_dir)
        algos = sorted(set(a for m in models for a in m.get("algorithms", [])))

        changes = []

        # 1. 更新建模手已验证算法表
        if algos:
            entries = [{"算法": a, "题型": ptype, "最近验证": _now(), "得分": str(score)} for a in algos]
            rf = self.root / "roles" / "建模手.md"
            if _update_table(rf, "<!-- EVOLUTION:VERIFIED_ALGORITHMS -->", entries):
                changes.append("建模手: 更新已验证算法表")

        # 2. 标记算法库 .md + 更新 index.json
        changes += _mark_algorithms(self.root, models, success, ptype)

        # 3. 对 scorer 输出的结构化分析（供 Claude 写经验时参考）
        analysis = _analyze_scorer_output(results, ptype)

        return {
            "status": "ok",
            "session": session_name,
            "success": success,
            "changes": changes,
            "analysis": analysis,  # Claude 读这个来写经验
            "hint": "Claude Code 请读 analysis 字段，结合 sessions 中的代码和论文，总结经验并写入 role 文档对应锚点。",
            "suggested_anchors": {
                "modeler": f"<!-- EVOLUTION:MODEL_{ptype.upper()} -->",
                "coder": f"<!-- EVOLUTION:CODE_{ptype.upper()} -->",
                "writer": [f"<!-- EVOLUTION:{v} -->" for v in analysis.get("weak_anchors", [])],
            },
        }

    def suggest(self, problem_type: str) -> dict:
        """从历史 eval_report.json 中检索策略"""
        records = self._scan_sessions()
        matches = [r for r in records if problem_type in r.get("type", "")]

        if not matches:
            return {"status": "no_data", "message": f"没有 {problem_type} 的历史策略"}

        best = max(matches, key=lambda r: r.get("score", 0))
        weak = self._analyze_weak_dimensions(problem_type)

        suggestions = [f"推荐 {best.get('algorithms', [])} (历史最高 {best.get('score', 0)} 分)"]
        if weak:
            suggestions.append(f"弱项: {', '.join(w['dim'] for w in weak[:3])}")

        return {
            "status": "ok",
            "problem_type": problem_type,
            "total_cases": len(matches),
            "strategy": {
                "recommended_algorithms": best.get("algorithms", []),
                "best_score": best.get("score", 0),
                "best_session": best.get("session", ""),
            },
            "weak_dimensions": weak[:5],
            "failure_patterns": [r for r in matches if r.get("score", 0) < 60][:3],
            "suggestion": "。".join(suggestions) + "。",
        }

    def gaps(self) -> dict:
        records = self._scan_sessions()
        done_types = set(r.get("type", "") for r in records)
        verified_ids = set()
        for r in records:
            for a in r.get("algorithms", []):
                verified_ids.add(a)
        missing = [t for t in ALL_PROBLEM_TYPES if t not in done_types]

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
            "suggestion": (f"尝试: {', '.join(missing)} 类题目" if missing else "所有题型覆盖") +
                          (f", {len(unverified)} 算法待验证" if unverified else ""),
        }

    def _analyze_weak_dimensions(self, problem_type: str) -> List[dict]:
        dim_scores = {}
        sessions_dir = self.root / "sessions"
        if not sessions_dir.exists():
            return []
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
            if problem_type != data.get("problem_type", ""):
                continue
            for dim in data.get("details", []):
                name = dim.get("dimension", "")
                if name not in dim_scores:
                    dim_scores[name] = []
                dim_scores[name].append(dim.get("score", 0))

        dim_hints = {
            "sensitivity_depth": "建议多参数联合扰动(LHS/Sobol)而非单参数OAT",
            "model_diversity": "建议至少2-3个不同家族的模型对比",
            "verification_complete": "每个solver必须有对应验证脚本且全部PASS",
            "abstract_quality": "摘要必须有具体数值结果",
            "visual_richness": "建议12-18张图，美赛多用热力图/多线对比图",
            "academic_norm": "美赛建议15-25篇引用，优先SCI期刊",
            "ai_flavor_penalty": "减少'此外/关键/充分展示'等AI高频词",
            "formula_rigor": "公式30-50个，自创指标给出完整定义",
        }
        weak = []
        for name, scores in dim_scores.items():
            avg = sum(scores) / len(scores) if scores else 0
            if avg < 0.65:
                weak.append({"dim": name, "avg_score": round(avg, 2), "count": len(scores),
                            "suggestion": dim_hints.get(name, "")})
        weak.sort(key=lambda w: w["avg_score"])
        return weak

    def _scan_sessions(self) -> List[dict]:
        records = []
        sessions_dir = self.root / "sessions"
        if not sessions_dir.exists():
            return records
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
            models = _scan_models(d)
            algos = list(set(a for m in models for a in m.get("algorithms", [])))
            records.append({
                "session": d.name, "type": data.get("problem_type", "unknown"),
                "score": data.get("overall_score", 0), "grade": data.get("grade", "?"),
                "algorithms": algos,
                "lessons": "\n".join(data.get("improvements", [])),
            })
        return records

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


# ═══════════════════════════════════════════════════════════════
# 纯机械活
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


def _mark_algorithms(root, models, success, ptype):
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
                    _update_index_json(root, a)
                    break
    return changes


def _update_index_json(root, algo_id):
    idx_file = root / "algorithms" / "index.json"
    if not idx_file.exists():
        return
    index = json.loads(idx_file.read_text(encoding="utf-8"))
    for dk, domain in index.get("domains", {}).items():
        for sk, sub in domain.get("subdomains", {}).items():
            for m in sub.get("methods", []):
                if m["id"] == algo_id and not m.get("evolved_status"):
                    m["evolved_status"] = f"verified {_now()}"
                    idx_file.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
                    return


# 评分维度→论文手章节锚点
WRITING_DIM_MAP = {
    "abstract_quality": "WRITING_ABSTRACT",
    "structure_completeness": "WRITING_SOLUTION",
    "visual_richness": "WRITING_VISUALS",
    "formula_rigor": "WRITING_MODELING",
    "verification_complete": "WRITING_SOLUTION",
    "sensitivity_depth": "WRITING_SENSITIVITY",
    "model_diversity": "WRITING_MODELING",
    "academic_norm": "WRITING_REFERENCES",
    "ai_flavor_penalty": "WRITING_STYLE",
}


def _analyze_scorer_output(results: dict, ptype: str) -> dict:
    """对 scorer 结果做结构化分析，供 Claude 写经验时参考"""
    details = results.get("details", [])
    if not details:
        return {"note": "无评分细项"}

    weak_items = []
    strong_items = []
    weak_anchors = []
    for d in details:
        score = d.get("score", 1.0)
        if score < 0.65:
            weak_items.append(f"{d.get('dimension','?')}: {score:.2f} — {d.get('desc','')}")
            anchor = WRITING_DIM_MAP.get(d.get("dimension", ""))
            if anchor and anchor not in weak_anchors:
                weak_anchors.append(anchor)
        elif score > 0.85:
            strong_items.append(f"{d.get('dimension','?')}: {score:.2f}")

    return {
        "overall_score": results.get("overall_score", 0),
        "grade": results.get("grade", "?"),
        "problem_type": ptype,
        "weak_areas": weak_items,
        "strong_areas": strong_items,
        "weak_anchors": weak_anchors,
        "improvements": results.get("improvements", []),
        "hint_for_claude": (
            "请读取 sessions/{name}/ 下的代码和论文，结合以上弱项分析，"
            "用自然语言总结经验并写入 role 文档对应锚点。"
            "写作指引: ①做了什么 ②为什么低分 ③下次怎么做。简短即可，100-200字。"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="自进化引擎 v9")
    sub = parser.add_subparsers(dest="action", required=True)

    ev = sub.add_parser("evolve", help="机械活 — 更新验证表/标记算法/产出结构分析")
    ev.add_argument("--session", required=True)
    ev.add_argument("--problem", default="{}")
    ev.add_argument("--results", default="{}")
    ev.add_argument("--from-scorer", action="store_true", help="自动读取 sessions/{session}/eval_report.json")

    sub.add_parser("suggest", help="推荐策略").add_argument("--problem-type", required=True)
    sub.add_parser("gaps", help="知识盲区")
    sub.add_parser("sessions", help="所有 sessions")

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
                               "details": eval_data.get("details", []),
                               "grade": eval_data.get("grade", "?")}
            r = evo.evolve(args.session, problem, results)
        elif args.action == "suggest":
            r = evo.suggest(args.problem_type)
        elif args.action == "gaps":
            r = evo.gaps()
        elif args.action == "sessions":
            r = evo.list_sessions()
        print(json.dumps(r, indent=2, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
