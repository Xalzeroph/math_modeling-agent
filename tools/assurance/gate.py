#!/usr/bin/env python3
"""
Assurance Gate — Aggregate audit artifacts into a unified gate_manifest.json.

Collects all audit artifacts from sessions/<name>/assurance/, validates each
against the assurance contract schema, checks for stale inputs, and produces
a single gate_manifest with the overall verdict.

Usage:
    python tools/assurance/gate.py collect --session "problem-name" [--assurance submission]
    python tools/assurance/gate.py status --session "problem-name"   # quick check
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from contract import (
    ASSURANCE_LEVELS,
    VERDICTS,
    check_stale,
    is_blocking,
    resolve_assurance_level,
    validate_artifact,
    validate_verdict,
)

# ── Audit skill definitions ────────────────
# What audits should exist for a complete session

EXPECTED_AUDITS = {
    "proof_audit": {
        "skill": "proof-checker",
        "stage": 2,
        "audited_by": "审稿手",
        "description": "公式推导验证",
    },
    "idea_audit": {
        "skill": "idea-audit",
        "stage": 2,
        "audited_by": "审稿手",
        "description": "模型选型审计",
    },
    "code_audit": {
        "skill": "code-audit",
        "stage": 5,
        "audited_by": "审稿手",
        "description": "代码完整性审计",
    },
    "claim_map": {
        "skill": "claim_map",
        "stage": 5,
        "audited_by": "审稿手",
        "description": "结果→论断映射（Markdown artifact）",
    },
    "sensitivity_audit": {
        "skill": "sensitivity-audit",
        "stage": 6,
        "audited_by": "审稿手",
        "description": "灵敏度分析审计",
    },
    "claim_audit": {
        "skill": "paper-claim-audit",
        "stage": 7,
        "audited_by": "审稿手",
        "description": "论文数字核对",
    },
    "citation_audit": {
        "skill": "citation-audit",
        "stage": 7,
        "audited_by": "审稿手",
        "description": "引用真实性验证",
    },
    "kill_argument": {
        "skill": "kill-argument",
        "stage": 7,
        "audited_by": "审稿手",
        "description": "模型评价对抗审查",
    },
}


def collect_audits(session_dir: Path) -> dict[str, dict]:
    """Scan assurance/ directory and load all audit artifacts."""
    assurance_dir = session_dir / "assurance"
    if not assurance_dir.exists():
        return {}

    audits = {}
    # Scan both .json and .md artifacts
    for f in sorted(list(assurance_dir.glob("*.json")) + list(assurance_dir.glob("*.md"))):
        try:
            if f.suffix == ".md":
                # Markdown artifacts: store content, map via filename
                content = f.read_text(encoding="utf-8")
                skill_name = f.stem  # e.g. "claim_map"
                audits[skill_name] = {
                    "artifact_path": str(f.relative_to(session_dir)),
                    "data": {
                        "audit_skill": skill_name,
                        "verdict": "PASS",
                        "summary": "Markdown artifact present (" + str(len(content)) + " chars)",
                        "full_content": content,
                        "generated_at": "",
                    },
                }
            else:
                data = json.loads(f.read_text(encoding="utf-8"))
                skill = data.get("audit_skill", f.stem)
                audits[skill] = {
                    "artifact_path": str(f.relative_to(session_dir)),
                    "data": data,
                }
        except (json.JSONDecodeError, Exception):
            audits[f.stem] = {
                "artifact_path": str(f.relative_to(session_dir)),
                "data": None,
                "parse_error": True,
            }
    return audits


def build_manifest(session_name: str, session_dir: Path, assurance: str = "draft") -> dict:
    """Build the complete gate manifest for a session."""
    audits = collect_audits(session_dir)
    gates = []
    blocking_count = 0
    warn_count = 0
    passed_count = 0
    missing_count = 0

    for audit_key, audit_def in EXPECTED_AUDITS.items():
        skill_name = audit_def["skill"]
        gate_entry = {
            "audit": audit_key,
            "skill": skill_name,
            "stage": audit_def["stage"],
            "description": audit_def["description"],
        }

        if skill_name in audits and audits[skill_name]["data"] is not None:
            artifact = audits[skill_name]["data"]
            verdict = artifact.get("verdict", "UNKNOWN")

            # Validate artifact
            valid, errors = validate_artifact(artifact)
            stale_inputs = check_stale(artifact.get("audited_input_hashes", {}))

            gate_entry["verdict"] = verdict
            gate_entry["summary"] = artifact.get("summary", "")
            gate_entry["artifact_valid"] = valid
            gate_entry["artifact_path"] = audits[skill_name]["artifact_path"]
            gate_entry["stale_inputs"] = stale_inputs

            if stale_inputs:
                gate_entry["verdict"] = "STALE"
                gate_entry["stale_note"] = "Audit artifact is stale — files changed since audit ran"
                if is_blocking("STALE", assurance):
                    blocking_count += 1
                else:
                    warn_count += 1

            elif verdict == "PASS":
                passed_count += 1
            elif verdict == "WARN":
                warn_count += 1
            elif is_blocking(verdict, assurance):
                blocking_count += 1
            else:
                warn_count += 1

            if errors:
                gate_entry["schema_errors"] = errors

        else:
            gate_entry["verdict"] = "MISSING"
            gate_entry["summary"] = "Audit artifact not found"
            missing_count += 1
            if is_blocking("MISSING", assurance):
                blocking_count += 1

        gates.append(gate_entry)

    # Overall verdict
    if blocking_count > 0:
        overall = "FAIL"
    elif missing_count > 0 and assurance == "submission":
        overall = "WARN"
    elif missing_count > 0:
        overall = "WARN"
    elif warn_count > 0:
        overall = "WARN"
    else:
        overall = "PASS"

    submission_ready = overall in ("PASS", "WARN") or (assurance == "draft" and overall != "FAIL")

    return {
        "session": session_name,
        "assurance_level": assurance,
        "overall_verdict": overall,
        "submission_ready": submission_ready,
        "summary": {
            "total_audits": len(EXPECTED_AUDITS),
            "passed": passed_count,
            "warn": warn_count,
            "blocking": blocking_count,
            "missing": missing_count,
        },
        "gates": gates,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assurance_contract_version": "1.0",
    }


def print_status(manifest: dict):
    """Pretty-print a gate manifest status summary."""
    s = manifest["summary"]
    print(f"\n{'='*60}")
    print(f"  Session: {manifest['session']}")
    print(f"  Assurance Level: {manifest['assurance_level']}")
    print(f"  Overall Verdict: {manifest['overall_verdict']}")
    print(f"  Submission Ready: {'YES' if manifest['submission_ready'] else 'NO'}")
    print(f"  Audits: {s['passed']} PASS, {s['warn']} WARN, {s['blocking']} BLOCK, {s['missing']} MISS")
    print(f"{'='*60}")
    for g in manifest["gates"]:
        icon = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]",
                "MISSING": "[MISS]", "STALE": "[STALE]",
                "BLOCKED": "[BLOCK]", "ERROR": "[ERR]",
                "NOT_APPLICABLE": "[N/A]"}.get(g["verdict"], "[???]")
        print(f"  {icon:8s}  Stage {g['stage']}  {g['description']}")
        if g.get("stale_inputs"):
            print(f"          STALE: {', '.join(g['stale_inputs'])}")
        if g.get("schema_errors"):
            for e in g["schema_errors"]:
                print(f"          ERROR: {e}")
        if g.get("summary"):
            print(f"          {g['summary']}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="ARIS Assurance Gate")
    sub = parser.add_subparsers(dest="command")

    collect_p = sub.add_parser("collect", help="Collect audits and build gate manifest")
    collect_p.add_argument("--session", required=True, help="Session name")
    collect_p.add_argument("--assurance", default=None, choices=["draft", "submission"],
                           help="Assurance level override")
    collect_p.add_argument("--effort", default="balanced",
                           choices=["lite", "balanced", "max"],
                           help="Effort level (affects assurance default)")
    collect_p.add_argument("--no-save", action="store_true", help="Print only, don't save")

    status_p = sub.add_parser("status", help="Quick gate status check")
    status_p.add_argument("--session", required=True, help="Session name")

    args = parser.parse_args()

    if args.command in ("collect", "status"):
        # Resolve root
        root = Path.cwd()
        for _ in range(5):
            if (root / "algorithms").exists():
                break
            root = root.parent

        session_dir = root / "sessions" / args.session
        if not session_dir.exists():
            print(f"ERROR: Session not found: {args.session}", file=sys.stderr)
            sys.exit(1)

        if args.command == "collect":
            assurance = resolve_assurance_level(args.effort, args.assurance)
            manifest = build_manifest(args.session, session_dir, assurance)
            print(json.dumps(manifest, indent=2, ensure_ascii=False))

            if not args.no_save:
                adir = session_dir / "assurance"
                adir.mkdir(parents=True, exist_ok=True)
                mpath = adir / "gate_manifest.json"
                mpath.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"\n[已保存到 {mpath}]", file=sys.stderr)

            print_status(manifest)
            sys.exit(0 if manifest["submission_ready"] else 1)

        elif args.command == "status":
            manifest = build_manifest(args.session, session_dir, "draft")
            print_status(manifest)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
