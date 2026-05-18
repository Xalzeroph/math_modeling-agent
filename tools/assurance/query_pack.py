#!/usr/bin/env python3
"""
Query Pack Generator — Lightweight replacement for ARIS research-wiki.

Reads EVOLUTION anchors in roles/*.md + eval_report.json from past sessions
of the same problem type, then outputs query_pack.md — a context summary
injected into the agent at Stage 0.

Usage:
    python tools/assurance/query_pack.py --problem-type <type> [--max-chars 8000]
"""

import argparse
import json
import re
import sys
from pathlib import Path


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "algorithms").exists():
            return d
        d = d.parent
    return Path.cwd()


def collect_evolution_experiences(root: Path, problem_type: str) -> list[str]:
    """Collect relevant EVOLUTION anchor blocks from role files."""
    role_dir = root / "roles"
    if not role_dir.exists():
        return []

    anchor_pattern = re.compile(
        rf"<!--\s*EVOLUTION:(?:MODEL|CODE|WRITING)_(?:{re.escape(problem_type)}|{re.escape(problem_type.upper())})\s*-->(.+?)(?:<!--\s*EVOLUTION:|$)",
        re.DOTALL
    )
    results = []
    for rf in sorted(role_dir.glob("*.md")):
        text = rf.read_text(encoding="utf-8")
        for m in anchor_pattern.finditer(text):
            content = m.group(1).strip()
            if content:
                results.append(f"### [{rf.stem}] {content[:500]}")
    return results[:5]


def collect_sessions(root: Path, problem_type: str) -> list[dict]:
    """Collect eval_reports from past sessions of the same type."""
    sessions_dir = root / "sessions"
    if not sessions_dir.exists():
        return []

    reports = []
    for d in sorted(sessions_dir.iterdir()):
        if not d.is_dir():
            continue
        ef = d / "eval_report.json"
        if not ef.exists():
            continue
        try:
            data = json.loads(ef.read_text(encoding="utf-8"))
            if data.get("problem_type", "") == problem_type:
                reports.append({
                    "session": d.name,
                    "score": data.get("overall_score", 0),
                    "grade": data.get("grade", ""),
                    "weak": data.get("analysis", {}).get("weak_areas", []),
                    "strong": data.get("analysis", {}).get("strong_areas", []),
                })
        except (json.JSONDecodeError, Exception):
            pass
    return reports


def build_query_pack(root: Path, problem_type: str, max_chars: int = 8000) -> str:
    """Build a context pack from EVOLUTION anchors + past eval_reports."""
    parts = []

    # 1. EVOLUTION experiences
    exp = collect_evolution_experiences(root, problem_type)
    if exp:
        parts.append("## 历史经验（EVOLUTION 锚点）\n")
        parts.extend(exp)

    # 2. Past session scores
    sessions = collect_sessions(root, problem_type)
    if sessions:
        parts.append("\n## 同类题型历史成绩\n")
        for s in sessions:
            weak = "; ".join(s["weak"][:3]) if s["weak"] else "none"
            strong = "; ".join(s["strong"][:3]) if s["strong"] else "none"
            parts.append(f"- **{s['session']}**: {s['score']}分 ({s['grade']}) 强:{strong} 弱:{weak}")

    query_pack = "\n".join(parts)
    if not query_pack.strip():
        return "<!-- No relevant history found. -->\n"

    if len(query_pack) > max_chars:
        query_pack = query_pack[:max_chars] + "\n\n<!-- TRUNCATED -->\n"

    return query_pack


def main():
    parser = argparse.ArgumentParser(description="Query Pack Generator")
    parser.add_argument("--problem-type", required=True, help="Problem type (optimization/prediction/evaluation/etc.)")
    parser.add_argument("--max-chars", type=int, default=8000)
    parser.add_argument("--save", action="store_true", help="Save to query_pack.md in project root")
    args = parser.parse_args()

    root = _resolve_root()
    qp = build_query_pack(root, args.problem_type, args.max_chars)

    if args.save:
        out = root / "query_pack.md"
        out.write_text(qp, encoding="utf-8")
        print(f"[Saved to {out}]")
    else:
        print(qp)


if __name__ == "__main__":
    main()
