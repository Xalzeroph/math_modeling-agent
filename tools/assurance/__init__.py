# ARIS Assurance Layer — Math Modeling Edition
#
# contract.py  — Six-state verdict engine + SHA256 tracing + artifact schema
# gate.py      — Aggregate audit artifacts → unified gate_manifest.json
# query_pack.py — Cross-session knowledge from EVOLUTION anchors + eval_reports
#
# Usage:
#   python tools/assurance/contract.py verify --artifact path.json
#   python tools/assurance/gate.py collect --session "problem-name"
#   python tools/assurance/query_pack.py --problem-type <type>
