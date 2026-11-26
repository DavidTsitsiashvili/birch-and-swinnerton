"""Check data/ files: valid statuses, unique ids, dependencies exist."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUSES = {"conjecture", "in_progress", "checked", "refuted", "dead"}

nodes = json.loads((ROOT / "data/nodes.json").read_text())
curves = json.loads((ROOT / "data/curves.json").read_text())
errors = []
ids = [n["id"] for n in nodes]
if len(ids) != len(set(ids)):
    errors.append("duplicate node ids")
for n in nodes:
    if n["status"] not in STATUSES:
        errors.append(f'{n["id"]}: bad status {n["status"]}')
    for d in n["depends_on"]:
        if d not in ids:
            errors.append(f'{n["id"]}: depends on unknown {d}')
    if n["status"] == "checked" and not n.get("lean"):
        errors.append(f'{n["id"]}: "checked" but no Lean theorem')
for c in curves:
    if len(c["ainvs"]) != 5:
        errors.append(f'{c["label"]}: needs 5 coefficients')
for i, line in enumerate((ROOT / "data/events.jsonl").read_text().splitlines(), 1):
    if line.strip():
        try:
            json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"events.jsonl line {i}: invalid JSON")

counts = {s: sum(n["status"] == s for n in nodes) for s in sorted(STATUSES)}
print("Nodes:", counts, "| Curves:", len(curves))
if errors:
    print("FAIL:"); print("\n".join(errors)); sys.exit(1)
print("PASS: data is consistent.")
