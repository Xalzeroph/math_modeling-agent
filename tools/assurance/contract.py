#!/usr/bin/env python3
"""
Assurance Contract — Six-state verdict engine + SHA256 artifact tracing.

Defines the canonical verdict state machine and artifact schema used by every
audit module (proof-checker, code-audit, claim-audit, citation-audit, etc.)
and consumed by gate.py for final submission gating.

Usage:
    python tools/assurance/contract.py verify --artifact <path.json>
    python tools/assurance/contract.py schema --skill <name>    # print schema for copy-paste
    python tools/assurance/contract.py hash --file <path>
"""

import argparse
import hashlib
import json
import sys
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ── Six-state verdict machine ────────────────

VERDICTS = {
    "PASS": {
        "meaning": "All checks passed",
        "blocking": False,
        "artifact_required": True,
    },
    "WARN": {
        "meaning": "Issues found, none disqualifying",
        "blocking": False,
        "artifact_required": True,
    },
    "FAIL": {
        "meaning": "Disqualifying issues found — must fix before submission",
        "blocking": True,
        "artifact_required": True,
    },
    "NOT_APPLICABLE": {
        "meaning": "Audit ran but nothing to audit (no theorems, no cites, etc.)",
        "blocking": False,
        "artifact_required": True,
    },
    "BLOCKED": {
        "meaning": "Audit should apply but prerequisites are missing (e.g. paper has claims but no results/)",
        "blocking": True,
        "artifact_required": False,
    },
    "ERROR": {
        "meaning": "Audit invocation failed (network, timeout, malformed output)",
        "blocking": True,
        "artifact_required": False,
    },
}

ASSURANCE_LEVELS = {
    "draft": {"description": "Audit results advisory only; FAIL does not block", "blocks_on": []},
    "submission": {"description": "All audits must PASS or WARN; FAIL/BLOCKED/ERROR block", "blocks_on": ["FAIL", "BLOCKED", "ERROR"]},
}


def resolve_assurance_level(effort: str = "balanced", explicit: Optional[str] = None) -> str:
    """Resolve assurance level from effort or explicit override."""
    if explicit and explicit in ASSURANCE_LEVELS:
        return explicit
    if effort in ("max", "beast"):
        return "submission"
    return "draft"


def validate_verdict(verdict: str) -> bool:
    """Check if a verdict string is one of the six valid states."""
    return verdict in VERDICTS


def is_blocking(verdict: str, assurance: str = "submission") -> bool:
    """Check if a verdict blocks pipeline progression."""
    if verdict not in VERDICTS:
        return True
    if assurance not in ASSURANCE_LEVELS:
        return VERDICTS[verdict]["blocking"]
    blocks = ASSURANCE_LEVELS[assurance]["blocks_on"]
    return verdict in blocks


# ── SHA256 file hashing ────────────────

def hash_file(path: Path) -> str:
    """SHA256 hash of a file."""
    if not path.exists():
        return "sha256:MISSING"
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()[:12]}"


def hash_files(files: list[Path]) -> dict[str, str]:
    """Hash a list of files, returning {relative_path: sha256}."""
    return {str(f): hash_file(f) for f in files}


def verify_hash(current_hash: str, recorded_hash: str) -> bool:
    """Check if a hash matches the recorded one (handles MISSING gracefully)."""
    if recorded_hash == "sha256:MISSING":
        return False
    return current_hash == recorded_hash


def check_stale(recorded_hashes: dict[str, str]) -> list[str]:
    """Check which files have changed since the audit ran."""
    stale = []
    for path_str, recorded in recorded_hashes.items():
        current = hash_file(Path(path_str))
        if not verify_hash(current, recorded):
            stale.append(path_str)
    return stale


# ── Artifact schema ────────────────

REQUIRED_FIELDS = [
    "audit_skill",
    "verdict",
    "summary",
    "generated_at",
]

OPTIONAL_FIELDS = [
    "audited_input_hashes",
    "details",
    "reason_code",
]


def validate_artifact(artifact: dict) -> tuple[bool, list[str]]:
    """Validate an audit artifact against the schema. Returns (valid, errors)."""
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in artifact:
            errors.append(f"Missing required field: {field}")
    if "verdict" in artifact and not validate_verdict(artifact["verdict"]):
        errors.append(f"Invalid verdict: {artifact['verdict']}")
    if "audited_input_hashes" in artifact:
        stale = check_stale(artifact["audited_input_hashes"])
        if stale:
            errors.append(f"STALE inputs: {', '.join(stale)}")
    return len(errors) == 0, errors


def create_artifact_skeleton(skill_name: str) -> dict:
    """Create a minimal artifact skeleton for an audit skill."""
    return {
        "audit_skill": skill_name,
        "verdict": "PASS",
        "summary": "",
        "audited_input_hashes": {},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "details": {},
    }


# ── CLI ────────────────

def main():
    parser = argparse.ArgumentParser(description="ARIS Assurance Contract")
    sub = parser.add_subparsers(dest="command")

    verify_p = sub.add_parser("verify", help="Verify an audit artifact")
    verify_p.add_argument("--artifact", required=True, help="Path to artifact JSON")

    schema_p = sub.add_parser("schema", help="Print artifact schema skeleton")
    schema_p.add_argument("--skill", default="unknown", help="Audit skill name")

    hash_p = sub.add_parser("hash", help="SHA256 hash a file or directory")
    hash_p.add_argument("--file", required=True, help="Path to file")

    args = parser.parse_args()

    if args.command == "verify":
        artifact_path = Path(args.artifact)
        if not artifact_path.exists():
            print(json.dumps({"status": "ERROR", "message": f"File not found: {args.artifact}"}))
            sys.exit(1)
        try:
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(json.dumps({"status": "ERROR", "message": f"Invalid JSON: {e}"}))
            sys.exit(1)
        valid, errors = validate_artifact(artifact)
        result = {
            "status": "PASS" if valid else "FAIL",
            "verdict": artifact.get("verdict", "UNKNOWN"),
            "skill": artifact.get("audit_skill", "unknown"),
            "errors": errors,
            "stale_inputs": check_stale(artifact.get("audited_input_hashes", {})),
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if valid else 1)

    elif args.command == "schema":
        skeleton = create_artifact_skeleton(args.skill)
        print(json.dumps(skeleton, indent=2, ensure_ascii=False))

    elif args.command == "hash":
        p = Path(args.file)
        if p.is_file():
            print(hash_file(p))
        else:
            print(f"Not a file: {args.file}", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
