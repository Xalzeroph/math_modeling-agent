#!/usr/bin/env python3
"""
自进化引擎 v7 — 做完题后记录经验到 roles/ 和 algorithms/

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
        # 改造1: 附加评分弱项
        maker = f"<!-- EVOLUTION:{MODEL_ANCHORS.get(ptype, 'MODEL_COMMON_PRACTICES')} -->"
        if _append_dim_notes(self.root / "roles" / "建模手.md",
                             maker, results, summary):
            changes.append("建模手: 追加评分弱项")
        changes += _evolve_coder(self.root, session_dir, session_name, ptype, success)
        changes += _evolve_writer(self.root, session_dir, session_name, success, results)

        # 改造5: check_outputs 集成
        check_file = session_dir / "output_check.json"
        if check_file.exists():
            try:
                chk = json.loads(check_file.read_text(encoding="utf-8"))
                vis_note = f"### 产出检查 — {session_name}\n\n"
                for c in chk.get("checks", []):
                    if not c.get("pass", True):
                        vis_note += f"- **{c.get('check','?')}**: {c.get('detail','')}\n"
                if len(vis_note) > 50:
                    _append_to_section(self.root / "roles" / "论文手.md",
                                       "<!-- EVOLUTION:WRITING_VISUALS -->", vis_note)
                    changes.append("论文手: check_outputs 结果写入")
            except:
                pass

        # 2. 算法验证标记
        changes += _evolve_algorithms(self.root, models, success, ptype)

        return {
            "status": "ok",
            "session": session_name,
            "success": success,
            "changes": changes,
            "gaps": self.gaps(),
            "summary": f"进化完成: {len(changes)} 处更新, {'成功' if success else '失败'}案例已记录",
        }

    def suggest(self, problem_type: str) -> dict:
        """从 sessions/ 的 eval_report.json 中检索历史策略，返回完整信息包"""
        records = self._scan_sessions()
        matches = [r for r in records if problem_type in r.get("type", "")]

        if not matches:
            return {"status": "no_data", "message": f"没有 {problem_type} 的历史策略"}

        # 最佳策略
        best = max(matches, key=lambda r: r.get("score", 0))
        best_session = best.get("session", "")
        best_score = best.get("score", 0)

        # 弱项维度统计（从所有同类 session 的 eval_report.json 读取 details）
        weak_dims = self._analyze_weak_dimensions(problem_type)
        # 写作建议
        writing_tips = self._collect_writing_tips(problem_type)
        # 代码模板
        code_templates = self._find_code_templates(problem_type)

        suggestions = [f"推荐 {best.get('algorithms', [])} (历史最高 {best_score} 分)"]
        if weak_dims:
            dim_names = [w["dim"] for w in weak_dims[:3]]
            suggestions.append(f"注意弱项: {', '.join(dim_names)}")
        if writing_tips:
            suggestions.append(f"写作: {writing_tips[0]['chapter']}需优化({writing_tips[0]['last_score']})")

        return {
            "status": "ok",
            "problem_type": problem_type,
            "total_cases": len(matches),
            "strategy": {
                "recommended_algorithms": best.get("algorithms", []),
                "best_score": best_score,
                "best_session": best_session,
            },
            "weak_dimensions": weak_dims[:5],
            "code_templates": code_templates[:3],
            "writing_tips": writing_tips[:5],
            "failure_patterns": [r for r in matches if r.get("score", 0) < 60][:3],
            "suggestion": "。".join(suggestions) + "。",
        }

    def _analyze_weak_dimensions(self, problem_type: str) -> List[dict]:
        """从历史 session 的 eval_report.json 分析弱项维度"""
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

        weak = []
        dim_hints = {
            "sensitivity_depth": "建议多参数联合扰动(LHS/Sobol)而非单参数OAT",
            "model_diversity": "建议至少2-3个不同家族的模型对比",
            "verification_complete": "每个solver必须有对应验证脚本且全部PASS",
            "abstract_quality": "摘要必须有具体数值结果，不得只说'效果好'",
            "visual_richness": "建议12-18张图，美赛多用热力图/多线对比图",
            "academic_norm": "美赛建议15-25篇引用，优先SCI期刊",
            "ai_flavor_penalty": "减少'此外/关键/充分展示'等AI高频词",
            "formula_rigor": "公式30-50个，自创指标给出完整定义",
            "structure_completeness": "必须包含假设+符号说明+灵敏度+Strengths/Weaknesses",
        }
        for name, scores in dim_scores.items():
            avg = sum(scores) / len(scores) if scores else 0
            if avg < 0.65:
                weak.append({
                    "dim": name,
                    "avg_score": round(avg, 2),
                    "count": len(scores),
                    "suggestion": dim_hints.get(name, f"该维度历史平均分{avg:.2f}，需提升"),
                })
        weak.sort(key=lambda w: w["avg_score"])
        return weak

    def _collect_writing_tips(self, problem_type: str) -> List[dict]:
        """从论文手锚点收集写作建议"""
        writer_file = self.root / "roles" / "论文手.md"
        if not writer_file.exists():
            return []
        text = writer_file.read_text(encoding="utf-8")

        # 锚点→章节名映射
        anchor_names = {
            "WRITING_ABSTRACT": "摘要", "WRITING_MODELING": "模型建立",
            "WRITING_SOLUTION": "模型求解", "WRITING_SENSITIVITY": "灵敏度分析",
            "WRITING_VISUALS": "图表", "WRITING_STYLE": "语言风格",
            "WRITING_REFERENCES": "参考文献", "WRITING_EVALUATION": "模型评价",
        }
        tips = []
        for anchor, name in anchor_names.items():
            # 找该锚点下有没有评分弱项记录
            marker = f"<!-- EVOLUTION:{anchor} -->"
            if marker in text:
                idx = text.index(marker)
                block = text[idx:idx+500]
                # 提取最近一条记录的得分
                scores = re.findall(r'(\d\.\d+)', block)
                if scores:
                    tips.append({
                        "chapter": name,
                        "last_score": float(scores[0]),
                        "suggestion": f"查看 roles/论文手.md 的 {name} 章节最佳实践",
                    })
        tips.sort(key=lambda t: t["last_score"])
        return tips

    def _find_code_templates(self, problem_type: str) -> List[dict]:
        """从编程手锚点找代码模板"""
        coder_file = self.root / "roles" / "编程手.md"
        if not coder_file.exists():
            return []
        text = coder_file.read_text(encoding="utf-8")
        code_anchor = CODE_ANCHORS.get(problem_type, "CODE_TEMPLATES")
        marker = f"<!-- EVOLUTION:{code_anchor} -->"
        if marker not in text:
            return []

        templates = []
        idx = text.index(marker)
        block = text[idx:idx+5000]
        # 提取 ```python ... ``` 代码块
        for m in re.finditer(r'###\s+(.+?)\n\n```python\n(.+?)```', block, re.DOTALL):
            title = m.group(1).strip()
            code = m.group(2).strip()[:500]
            templates.append({"title": title, "code_preview": code})
        return templates

    def _scan_sessions(self) -> List[dict]:
        """扫描 sessions/ 中的 eval_report.json 获取历史记录"""
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
            # 提取算法信息
            models = _scan_models(d)
            algos = list(set(a for m in models for a in m.get("algorithms", [])))
            records.append({
                "session": d.name,
                "type": data.get("problem_type", "unknown"),
                "score": data.get("overall_score", 0),
                "grade": data.get("grade", "?"),
                "algorithms": algos,
                "lessons": "\n".join(data.get("improvements", [])),
            })
        return records

    def gaps(self) -> dict:
        """检测知识盲区 — 未做过的题型 + 未验证的算法"""
        records = self._scan_sessions()
        done_types = set(r.get("type", "") for r in records)

        verified_ids = set()
        for r in records:
            for a in r.get("algorithms", []):
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

MODEL_ANCHORS = {
    "optimization": "MODEL_OPTIMIZATION",
    "evaluation": "MODEL_EVALUATION",
    "prediction": "MODEL_PREDICTION",
    "network": "MODEL_NETWORK",
    "statistics": "MODEL_STATISTICS",
    "ode": "MODEL_SIMULATION",
    "simulation": "MODEL_SIMULATION",
    "classification": "MODEL_MACHINE_LEARNING",
}

# 题型→编程手锚点映射
CODE_ANCHORS = {
    "optimization": "CODE_OPTIMIZATION", "evaluation": "CODE_EVALUATION",
    "prediction": "CODE_PREDICTION", "network": "CODE_NETWORK",
    "statistics": "CODE_STATISTICS", "ode": "CODE_SIMULATION",
    "simulation": "CODE_SIMULATION", "classification": "CODE_ML",
}

# 评分维度→论文手锚点映射
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

def _evolve_modeler(root, ptype, models, keywords, success, score, summary):
    changes = []
    role_file = root / "roles" / "建模手.md"
    mtypes = sorted(set(m.get("type", "?") for m in models))
    algos = sorted(set(a for m in models for a in m.get("algorithms", [])))

    anchor = MODEL_ANCHORS.get(ptype, "MODEL_COMMON_PRACTICES")
    marker = f"<!-- EVOLUTION:{anchor} -->"

    if success:
        exp = f"### {_now()} — {summary[:60]}\n\n"
        exp += f"- **题型**: {ptype}\n"
        exp += f"- **模型**: {', '.join(mtypes)}\n"
        exp += f"- **算法**: {', '.join(algos)}\n"
        exp += f"- **标签**: {', '.join(keywords[:5])}\n"
        exp += f"- **得分**: {score}\n"
        if _append_to_section(role_file, marker, exp):
            changes.append(f"建模手: 追加经验到 {anchor}")
        # 改造1: 追加评分弱项
        details = results.get("details", []) if 'results' in dir() else []
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

# 改造1需要让 _evolve_modeler 能访问 results，改为从 evolve() 传入
def _append_dim_notes(role_file, marker, results, summary):
    """追加评分弱项到建模手锚点"""
    details = results.get("details", [])
    if not details:
        return False
    dim_notes = []
    for d in details:
        if d.get("score", 1.0) < 0.65:
            dim_notes.append(f"- **{d.get('dimension','?')}**: {d['score']:.2f} — {d.get('desc','')}")
    if dim_notes:
        note = f"### 评分弱项 — {summary[:40]}\n\n" + "\n".join(dim_notes) + "\n"
        return _append_to_section(role_file, marker, note)
    return False


def _evolve_coder(root, session_dir, session_name, ptype, success):
    changes = []
    role_file = root / "roles" / "编程手.md"
    solver_dir = session_dir / "solvers"
    code_anchor = CODE_ANCHORS.get(ptype, "CODE_TEMPLATES")
    marker = f"<!-- EVOLUTION:{code_anchor} -->"

    if solver_dir.exists():
        for py in sorted(solver_dir.glob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True)[:2]:
            code = py.read_text(encoding="utf-8")
            # 去注释但保留完整结构（前3000字符）
            tpl = f"### {session_name}/{py.name} ({_now()})\n\n```python\n{code[:3000]}\n```\n"
            if _append_to_section(role_file, marker, tpl):
                changes.append(f"编程手: +模板 {py.name} → {code_anchor}")
    if not success:
        pitfall = f"### {_now()} — {session_name}\n\n本次验证未通过。检查 verifications/ 输出。\n"
        if _append_to_section(role_file, "<!-- EVOLUTION:PITFALLS -->", pitfall):
            changes.append("编程手: 追加踩坑")
    return changes


def _evolve_writer(root, session_dir, session_name, success, results):
    changes = []
    role_file = root / "roles" / "论文手.md"
    main_tex = session_dir / "paper" / "main.tex"

    # 常规论文案例（保留）
    if main_tex.exists() and success:
        content = main_tex.read_text(encoding="utf-8")
        m = re.search(r'\\begin\{abstract\}(.+?)\\end\{abstract\}', content, re.DOTALL)
        abstract = m.group(1).strip()[:300] if m else "见文件"
        sections = re.findall(r'\\section\{([^}]+)\}', content)
        case = f"### {session_name} ({_now()})\n\n**摘要**: {abstract}\n\n**结构**: {', '.join(sections)}\n"
        if _append_to_section(role_file, "<!-- EVOLUTION:PAPER_TEMPLATES -->", case):
            changes.append("论文手: 追加论文案例")

    # 改造3: 按评分维度写入对应章节锚点
    if success:
        details = results.get("details", [])
        for d in details:
            if d.get("score", 1.0) < 0.65:
                dim = d.get("dimension", "")
                anchor = WRITING_DIM_MAP.get(dim)
                if anchor:
                    tip = f"### {session_name} ({_now()})\n\n**{d.get('desc','')}**: {d['score']:.2f}\n\n建议: 查看上方该章节的 O 奖最佳实践\n"
                    marker = f"<!-- EVOLUTION:{anchor} -->"
                    if _append_to_section(role_file, marker, tip):
                        changes.append(f"论文手: 追加写作建议到 {anchor}")

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
                    # 改造6: 同步更新 index.json 的 evolved_status
                    _update_index_json(root, a)
                    break
    return changes

def _update_index_json(root, algo_id):
    """更新 algorithms/index.json 中方法的 evolved_status"""
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
