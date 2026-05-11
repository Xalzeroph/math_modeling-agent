#!/usr/bin/env python3
"""产出完整性检查 — 编译后自动验证所有产出是否完整一致"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


def _resolve_root() -> Path:
    d = Path.cwd()
    for _ in range(5):
        if (d / "algorithms").exists():
            return d
        d = d.parent
    return Path.cwd()


def check_session(root: Path, session_name: str) -> dict:
    """对一个 session 做完整性检查"""
    session_dir = root / "sessions" / session_name
    if not session_dir.exists():
        # 兼容旧结构：paper/ 在根目录下
        session_dir = root
        if not (session_dir / "paper").exists():
            return {"status": "error", "message": f"Session 不存在: {session_name}"}

    checks = []
    passed = 0
    failed = 0

    # ── 检查1: 文件编码 ──────────────────────
    for p in sorted(session_dir.rglob("*.tex")):
        try:
            content = p.read_text(encoding="utf-8")
            checks.append({"check": "encoding", "file": str(p.name), "pass": True,
                          "detail": "UTF-8"})
            passed += 1
        except UnicodeDecodeError:
            checks.append({"check": "encoding", "file": str(p.name), "pass": False,
                          "detail": "非 UTF-8 编码"})
            failed += 1

    for p in sorted(session_dir.rglob("*.py")):
        try:
            p.read_text(encoding="utf-8")
            passed += 1
        except UnicodeDecodeError:
            checks.append({"check": "encoding", "file": str(p.relative_to(root)), "pass": False,
                          "detail": "非 UTF-8 编码"})
            failed += 1

    # ── 检查2: 图片引用 vs 实际文件 ──────────
    main_tex = None
    for candidate in [session_dir / "paper" / "main.tex", root / "paper" / "main.tex"]:
        if candidate.exists():
            main_tex = candidate
            break

    if main_tex:
        tex_content = main_tex.read_text(encoding="utf-8")
        referenced = set(re.findall(r'\\includegraphics\s*(?:\[.*?\])?\s*\{(.+?)\}', tex_content))
        referenced = {r.replace(".png","").replace(".jpg","").replace(".eps","").replace(".pdf","") for r in referenced}

        figures_dir = session_dir / "figures"
        if not figures_dir.exists():
            figures_dir = root / "figures"
        actual_files = set()
        if figures_dir.exists():
            actual_files = {p.stem for p in figures_dir.glob("*") if p.suffix.lower() in ('.png', '.jpg', '.eps', '.pdf')}

        missing = referenced - actual_files
        unused = actual_files - referenced
        if missing:
            checks.append({"check": "figure_refs", "pass": False,
                          "detail": f"论文引用了但 filesystem 不存在的图: {missing}", "missing": list(missing)})
            failed += 1
        else:
            checks.append({"check": "figure_refs", "pass": True,
                          "detail": f"全部 {len(referenced)} 张图引用有效", "count": len(referenced)})
            passed += 1
        if unused:
            checks.append({"check": "figure_unused", "pass": True,
                          "detail": f"figures/ 里有 {len(unused)} 张论文未使用的图", "unused": list(unused)})

    # ── 检查3: solver vs verification 一一对应 ──
    solver_dir = session_dir / "solvers"
    verify_dir = session_dir / "verifications"
    if not solver_dir.exists():
        solver_dir = root / "solvers"
    if not verify_dir.exists():
        verify_dir = root / "verifications"

    if solver_dir and solver_dir.exists():
        solvers = [p.stem for p in solver_dir.glob("*.py") if not p.name.startswith("_")]
        verifies = [p.stem for p in verify_dir.glob("*.py")] if verify_dir and verify_dir.exists() else []

        solo = [s for s in solvers if not any(s in v or v in s for v in verifies)]
        if solo:
            checks.append({"check": "solver_verify_pair", "pass": False,
                          "detail": f"无验证脚本的 solver: {solo}"})
            failed += 1
        else:
            checks.append({"check": "solver_verify_pair", "pass": True,
                          "detail": f"全部 {len(solvers)} 个 solver 有对应验证"})
            passed += 1

    # ── 检查4: PDF 页数检查 ──────────────────
    pdf_path = None
    for candidate in [session_dir / "paper" / "main.pdf", root / "paper" / "main.pdf"]:
        if candidate.exists():
            pdf_path = candidate
            break

    if pdf_path:
        try:
            import subprocess, sys
            # 尝试用 pdfplumber
            try:
                import pdfplumber
                with pdfplumber.open(str(pdf_path)) as pdf:
                    pages = len(pdf.pages)
            except:
                pages = -1
            if 8 <= pages <= 25:
                checks.append({"check": "pdf_pages", "pass": True, "detail": f"{pages} 页 — 在合理范围"})
                passed += 1
            elif pages > 0:
                checks.append({"check": "pdf_pages", "pass": False,
                              "detail": f"{pages} 页 — 应该在 8-25 页范围内"})
                failed += 1
        except:
            pass

    # ── 汇总 ──────────────────────────────────
    return {
        "status": "ok",
        "session": session_name,
        "checks": checks,
        "pass_count": passed,
        "fail_count": failed,
        "overall": "ALL PASS" if failed == 0 else f"FAILED — {failed} 项不通过",
    }


def main():
    parser = argparse.ArgumentParser(description="产出完整性检查")
    parser.add_argument("--session", required=True, help="Session 名称")
    args = parser.parse_args()

    root = _resolve_root()
    result = check_session(root, args.session)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
